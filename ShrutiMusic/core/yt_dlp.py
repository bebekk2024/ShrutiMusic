"""
core/yt_dlp.py

Ready-to-use wrapper for yt-dlp with:
- sane default options (headers, IPv4 forcing, cookie support)
- retry logic
- synchronous functions that call yt-dlp (blocking)
- async wrappers to call those functions safely from an asyncio event loop

Usage examples (inside async code):
    from core.yt_dlp import async_extract_info, async_download_audio

    info = await async_extract_info("https://www.youtube.com/watch?v=...")
    path = await async_download_audio("https://www.youtube.com/watch?v=...", out_dir="/tmp")

Notes:
- Ensure yt-dlp is installed in your environment (requirements.txt: "yt-dlp>=2025.0.0")
- Ensure ffmpeg is available on the PATH when you need to post-process or transcode
- For age-restricted/private videos you may supply a cookiefile path via YTDL_COOKIE_PATH env var
"""

import os
import time
import logging
import tempfile
import shutil
import asyncio
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from yt_dlp import YoutubeDL, DownloadError, ExtractorError

logger = logging.getLogger(__name__)
# A small thread pool for running blocking yt-dlp calls
_EXECUTOR = ThreadPoolExecutor(max_workers=int(os.environ.get("YTDL_THREAD_POOL", "2")))


DEFAULT_YTDL_OPTS: Dict[str, Any] = {
    "format": "bestaudio/best",
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "cachedir": False,
    "source_address": os.environ.get("YTDL_SOURCE_ADDRESS", "0.0.0.0"),  # force IPv4 if needed
    "http_headers": {
        "User-Agent": os.environ.get(
            "YTDL_USER_AGENT",
            "Mozilla/5.0 (X11; Linux x86_64)"
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        ),
        "Referer": "https://m.youtube.com/watch?v=u_15ggPEi8w",
    },
    # postprocessors and outtmpl are left to caller when downloading
    # 'cookiefile': os.environ.get('YTDL_COOKIE_PATH'),
}


class YTDLError(Exception):
    """Generic yt-dlp wrapper error."""


def _build_opts(extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    opts = dict(DEFAULT_YTDL_OPTS)
    if extra_opts:
        opts.update(extra_opts)
    # If an env cookie path is set and no cookiefile present in opts, use it
    cookie_env = os.environ.get("YTDL_COOKIE_PATH")
    if cookie_env and "cookiefile" not in opts:
        opts["cookiefile"] = cookie_env
    return opts


def extract_info(url: str, opts: Optional[Dict[str, Any]] = None, retries: int = 3, wait: int = 2) -> Dict[str, Any]:
    """
    Blocking function that extracts info for a given URL using yt-dlp.
    Returns the info dict. Raises YTDLError on repeated failure.
    """
    options = _build_opts(opts)
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            with YoutubeDL(options) as ytdl:
                info = ytdl.extract_info(url, download=False)
                logger.debug("yt-dlp extract_info success for %s", url)
                return info
        except (DownloadError, ExtractorError, Exception) as e:
            last_exc = e
            logger.warning("yt-dlp extract failed (attempt %s/%s) for %s: %s", attempt, retries, url, e)
            if attempt < retries:
                time.sleep(wait)
    raise YTDLError(f"yt-dlp failed to extract info for {url}: {last_exc}")


async def async_extract_info(url: str, opts: Optional[Dict[str, Any]] = None, retries: int = 3, wait: int = 2) -> Dict[str, Any]:
    """
    Async wrapper for extract_info. Safe to call from asyncio code.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, lambda: extract_info(url, opts=opts, retries=retries, wait=wait))


def download_audio(url: str, out_dir: Optional[str] = None, filename_template: str = "%(title)s-%(id)s.%(ext)s",
                   opts: Optional[Dict[str, Any]] = None, retries: int = 3, wait: int = 2) -> str:
    """
    Blocking download helper.
    - Downloads best audio to out_dir (temporary directory if None).
    - Returns the full path to the downloaded file.
    - Uses ffmpeg postprocessor to ensure common audio format if desired.
    """
    options = _build_opts(opts) if opts else _build_opts({})
    # Set output template and postprocessor for audio
    if "outtmpl" not in options:
        # Put into a temporary directory if out_dir is None
        if out_dir is None:
            temp_dir = tempfile.mkdtemp(prefix="yt_dlp_")
            out_dir = temp_dir
        options["outtmpl"] = os.path.join(out_dir, filename_template)

    # Optional: Add a postprocessor to convert to opus/m4a/mp3 if caller wants.
    # The repository that will use this function can pass 'postprocessors' in opts to control this.
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            with YoutubeDL(options) as ytdl:
                logger.debug("Starting yt-dlp download for %s -> %s", url, options.get("outtmpl"))
                result = ytdl.extract_info(url, download=True)
                # result may be a dict for single video or playlist dict
                # Locate the actual filename from the returned info
                # yt-dlp returns 'requested_downloads' or files on extracted info depending on postprocessors
                # As fallback, try to build filename via prepare_filename
                if isinstance(result, dict):
                    # If it's a playlist, pick the first entry (caller should avoid playlist for audio download)
                    if result.get("_type") == "playlist" and result.get("entries"):
                        info = result["entries"][0]
                    else:
                        info = result
                else:
                    info = result

                # Try to determine filepath
                # YoutubeDL.prepare_filename is internal; but extract_info with download usually populates 'requested_downloads'
                # We'll try common keys
                possible_paths = []
                if isinstance(info, dict):
                    # yt-dlp may include _filename in some setups; check common keys
                    for key in ("_filename", "filepath", "filename"):
                        if key in info and info[key]:
                            possible_paths.append(info[key])
                # Fallback: scan out_dir for newest file
                if out_dir and os.path.isdir(out_dir):
                    # Find newest file in out_dir
                    try:
                        files = [os.path.join(out_dir, f) for f in os.listdir(out_dir)]
                        files = [f for f in files if os.path.isfile(f)]
                        if files:
                            newest = max(files, key=os.path.getmtime)
                            possible_paths.append(newest)
                    except Exception:
                        pass

                if possible_paths:
                    # return the first candidate that exists
                    for p in possible_paths:
                        if os.path.exists(p):
                            logger.debug("Downloaded file located: %s", p)
                            return p

                # If we reached here, try to use ytdl.prepare_filename to build path (best-effort)
                try:
                    filename = YoutubeDL(options).prepare_filename(info)
                    if os.path.exists(filename):
                        return filename
                except Exception:
                    pass

                raise YTDLError("Could not determine downloaded file path from yt-dlp result.")
        except (DownloadError, ExtractorError, Exception) as e:
            last_exc = e
            logger.warning("yt-dlp download failed (attempt %s/%s) for %s: %s", attempt, retries, url, e)
            if attempt < retries:
                time.sleep(wait)
    raise YTDLError(f"yt-dlp failed to download {url}: {last_exc}")


async def async_download_audio(url: str, out_dir: Optional[str] = None, filename_template: str = "%(title)s-%(id)s.%(ext)s",
                               opts: Optional[Dict[str, Any]] = None, retries: int = 3, wait: int = 2) -> str:
    """
    Async wrapper for download_audio. Returns the downloaded file path.
    """
    loop = asyncio.get_event_loop()
    fn = lambda: download_audio(url, out_dir=out_dir, filename_template=filename_template, opts=opts, retries=retries, wait=wait)
    return await loop.run_in_executor(_EXECUTOR, fn)


def get_direct_url(info: Dict[str, Any]) -> Optional[str]:
    """
    Try to extract a direct (streamable) URL from yt-dlp info dict.
    For some extractors, info['url'] is usable; for others, the 'formats' list contains direct format URLs.
    Returns first candidate URL or None.
    """
    if not info:
        return None
    # If info is a playlist choose first entry
    if info.get("_type") == "playlist" and info.get("entries"):
        info = info["entries"][0]
    # Direct URL field
    if "url" in info and isinstance(info["url"], str):
        return info["url"]
    # formats exist: pick best audio format that has 'url'
    formats = info.get("formats") or info.get("requested_formats")
    if formats:
        # prefer audio-only formats by acodec or vcodec == 'none'
        for f in sorted(formats, key=lambda x: (x.get("tbr") or 0), reverse=True):
            if f.get("acodec") and f.get("url"):
                return f.get("url")
    return None


async def async_get_direct_url(url: str, opts: Optional[Dict[str, Any]] = None, retries: int = 3, wait: int = 2) -> Optional[str]:
    """
    Convenience: extract info and return a direct stream URL (if available).
    """
    info = await async_extract_info(url, opts=opts, retries=retries, wait=wait)
    return get_direct_url(info)


# If module executed directly, run a small self-test (manual run)
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Simple test runner for core/yt_dlp.py")
    parser.add_argument("url", help="URL to test")
    parser.add_argument("--download", action="store_true", help="Actually download audio")
    parser.add_argument("--out", default=None, help="Output directory for download")
    args = parser.parse_args()

    test_url = args.url
    if args.download:
        try:
            path = download_audio(test_url, out_dir=args.out)
            print("Downloaded ->", path)
        except Exception as e:
            print("Download failed:", e)
    else:
        try:
            info = extract_info(test_url)
            print("Title:", info.get("title"))
            print("Direct URL:", get_direct_url(info))
        except Exception as e:
            print("Extract failed:", e)
