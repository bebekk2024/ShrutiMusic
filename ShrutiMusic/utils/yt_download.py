import os
import time
import logging
from typing import Optional, Dict, Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

def _build_ydl_opts(cookiefile: Optional[str], outtmpl: Optional[str] = None) -> dict:
    opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        # Perintah untuk memperkecil kemungkinan 403
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
            ),
            # "Referer": "https://www.youtube.com/"
        },
        # Jangan print progress ke stdout (heroku logs lebih rapi)
        "progress_hooks": [],
        # Nonaktifkan pemecahan playlist untuk safety
        "noplaylist": True,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    if outtmpl:
        opts["outtmpl"] = outtmpl
    return opts

def extract_info_with_retries(url: str,
                              download: bool = False,
                              cookiefile: Optional[str] = None,
                              max_retries: int = 4,
                              initial_backoff: float = 2.0,
                              outtmpl: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract metadata or download using yt-dlp with retry/backoff on HTTP 403 & transient errors.
    - url: video URL
    - download: jika True, akan mendownload file sesuai outtmpl
    - cookiefile: path ke cookies.txt (jika tersedia)
    - outtmpl: template output (mis. /tmp/%(id)s.%(ext)s)
    """
    ydl_opts = _build_ydl_opts(cookiefile, outtmpl)
    backoff = initial_backoff
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        try:
            logger.info("yt-dlp attempt %d for url %s (cookiefile=%s)", attempt, url, bool(cookiefile))
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=download)
                logger.info("yt-dlp success on attempt %d", attempt)
                return info
        except DownloadError as e:
            msg = str(e).lower()
            logger.warning("yt-dlp DownloadError on attempt %d: %s", attempt, msg)
            # Spesifik 403 -> coba retry dengan backoff dan saran cookiefile
            if "http error 403" in msg or "403" in msg:
                logger.warning("Detected HTTP 403 (Forbidden). Common fixes: update yt-dlp, use cookiefile (logged-in), or change headers/proxy.")
                # Jika tidak ada cookiefile, hentikan lebih cepat dan beri pesan bermakna
                if not cookiefile:
                    # satu percobaan lagi untuk retry singkat, lalu exit ke caller untuk langkah manual
                    if attempt >= 2:
                        raise RuntimeError("yt-dlp: HTTP 403 repeated. Try using a cookiefile (login cookies) or update yt-dlp.")
                time.sleep(backoff)
                backoff *= 2
                continue
            # Timeout / transient network
            if "timed out" in msg or "timeout" in msg or "temporarily unavailable" in msg:
                time.sleep(backoff)
                backoff *= 2
                continue
            # Lainnya -> angkat error ke caller
            raise
        except Exception as e:
            logger.exception("Unexpected error on yt-dlp attempt %d", attempt)
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError(f"yt-dlp failed after {max_retries} attempts for url: {url}")
