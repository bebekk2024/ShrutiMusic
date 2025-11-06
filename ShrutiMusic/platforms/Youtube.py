import asyncio
import os
import re
import json
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from ShrutiMusic import app, LOGGER
from ShrutiMusic.utils.formatters import time_to_seconds
import random
import yt_dlp
from urllib.parse import urlparse

# NOTE:
# This version uses yt-dlp + cookies (if available) directly (no external YOUR_API_URL).
# Downloads are performed via async subprocess calls to yt-dlp to avoid blocking the event loop.
# yt_dlp Python API is used for metadata/formats extraction inside a thread executor.

def cookie_txt_file():
    cookie_dir = "ShrutiMusic/cookies"
    if not os.path.exists(cookie_dir):
        return None
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        return None
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file

async def get_telegram_file(telegram_link: str, video_id: str, file_type: str) -> str:
    """
    Download file from Telegram link or channel/message (via Pyrogram).
    Returns local file path or None.
    """
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    try:
        extension = ".webm" if file_type == "audio" else ".mkv"
        file_path = os.path.join("downloads", f"{video_id}{extension}")

        # If already exists locally, return immediately
        if os.path.exists(file_path):
            logger.info(f"📂 [LOCAL] File exists: {video_id}")
            return file_path

        # Try parse telegram_link which may be like https://t.me/channel/123
        chat = None
        msg_id = None
        if telegram_link:
            parsed = urlparse(telegram_link)
            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 2:
                chat = f"@{parts[0]}"
                try:
                    msg_id = int(parts[1])
                except Exception:
                    msg_id = None

        # If not parseable from link, user might have provided a t.me shortlink or similar; fallback to get_messages directly if possible
        if not chat or not msg_id:
            # try to infer from full link or DB (caller may pass telegram_link only)
            try:
                # Attempt to get messages using the full link; Pyrogram supports get_messages(chat, id)
                # If telegram_link isn't parseable we skip.
                pass
            except Exception:
                pass

        if not chat or not msg_id:
            logger.error(f"❌ Invalid Telegram link/format: {telegram_link}")
            return None

        logger.info(f"📥 [TELEGRAM] Downloading from {chat}/{msg_id}")
        os.makedirs("downloads", exist_ok=True)
        msg = await app.get_messages(chat, msg_id)
        # msg may be None or empty; guard it
        if not msg:
            logger.error(f"❌ [TELEGRAM] Message not found: {chat}/{msg_id}")
            return None

        await msg.download(file_name=file_path)

        # wait a short while for file to exist
        timeout = 0.0
        while not os.path.exists(file_path) and timeout < 60.0:
            await asyncio.sleep(0.5)
            timeout += 0.5

        if os.path.exists(file_path):
            logger.info(f"✅ [TELEGRAM] Downloaded: {video_id}")
            return file_path
        else:
            logger.error(f"❌ [TELEGRAM] Timeout while downloading: {video_id}")
            return None

    except Exception as e:
        logger.error(f"❌ [TELEGRAM] Failed to download {video_id}: {e}")
        return None

# Helper to run yt-dlp as subprocess (async)
async def _run_yt_dlp_subprocess(args, logger):
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    stdout = out.decode(errors="ignore") if out else ""
    stderr = err.decode(errors="ignore") if err else ""
    return proc.returncode, stdout, stderr

async def download_song(link: str) -> Union[str, None]:
    """
    Download audio using yt-dlp with cookies if available.
    Returns local file path on success, else None.
    """
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    # normalize link if only id passed
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger.info(f"🎵 [AUDIO] Starting download for: {video_id}")

    if not video_id or len(video_id) < 3:
        logger.error("Invalid video id for audio download")
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")

    if os.path.exists(file_path):
        logger.info(f"🎵 [LOCAL] File exists: {video_id}")
        return file_path

    cookie_file = cookie_txt_file()
    # Build yt-dlp args: prefer webm/opus audio
    ytdl_cmd = [
        "yt-dlp",
        "--no-playlist",
        "--newline",
        "-f", "bestaudio[ext=webm]/bestaudio",
        "-o", file_path,
        link,
    ]
    if cookie_file:
        ytdl_cmd[1:1] = ["--cookies", cookie_file]  # insert after yt-dlp

    logger.info(f"[AUDIO] Running yt-dlp for {video_id} (cookies: {'yes' if cookie_file else 'no'})")
    try:
        ret, out, err = await _run_yt_dlp_subprocess(ytdl_cmd, logger)
        if ret != 0:
            logger.error(f"[AUDIO] yt-dlp failed for {video_id}: {err.strip()}")
            # cleanup partial file if exists
            if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                try:
                    os.remove(file_path)
                except:
                    pass
            return None

        if os.path.exists(file_path):
            logger.info(f"🎉 [AUDIO] Downloaded: {video_id}")
            return file_path
        else:
            logger.error(f"[AUDIO] yt-dlp finished but file not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"[AUDIO] Exception while downloading {video_id}: {e}")
        return None

async def download_video(link: str) -> Union[str, None]:
    """
    Download video using yt-dlp with cookies if available.
    Returns local file path on success, else None.
    """
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    logger.info(f"🎥 [VIDEO] Starting download for: {video_id}")

    if not video_id or len(video_id) < 3:
        logger.error("Invalid video id for download")
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")

    if os.path.exists(file_path):
        logger.info(f"🎥 [LOCAL] File exists: {video_id}")
        return file_path

    cookie_file = cookie_txt_file()
    # Prefer bestvideo+bestaudio merged into mkv
    ytdl_cmd = [
        "yt-dlp",
        "--no-playlist",
        "--merge-output-format", "mkv",
        "-f", "bestvideo+bestaudio/best",
        "-o", file_path,
        link,
    ]
    if cookie_file:
        ytdl_cmd[1:1] = ["--cookies", cookie_file]

    logger.info(f"[VIDEO] Running yt-dlp for {video_id} (cookies: {'yes' if cookie_file else 'no'})")
    try:
        ret, out, err = await _run_yt_dlp_subprocess(ytdl_cmd, logger)
        if ret != 0:
            logger.error(f"[VIDEO] yt-dlp failed for {video_id}: {err.strip()}")
            if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                try:
                    os.remove(file_path)
                except:
                    pass
            return None

        if os.path.exists(file_path):
            logger.info(f"🎉 [VIDEO] Downloaded: {video_id}")
            return file_path
        else:
            logger.error(f"[VIDEO] yt-dlp finished but file not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"[VIDEO] Exception while downloading {video_id}: {e}")
        return None

async def check_file_size(link):
    """
    Use yt-dlp -J to get JSON info (requires cookies if needed).
    Returns total filesize (sum of formats' filesize) in bytes or None.
    """
    cookie_file = cookie_txt_file()
    cmd = ["yt-dlp"]
    if cookie_file:
        cmd += ["--cookies", cookie_file]
    cmd += ["-J", link]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        return None
    try:
        info = json.loads(out.decode())
    except Exception:
        return None
    total = 0
    for f in info.get("formats", []):
        fs = f.get("filesize") or f.get("filesize_approx") or 0
        if fs:
            total += int(fs)
    return total

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.logger = LOGGER("ShrutiMusic/platforms/Youtube.py")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if getattr(message_1, 'reply_to_message', False):
            messages.append(message_1.reply_to_message)
        for message in messages:
            if getattr(message, "entities", None):
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = getattr(message, "text", None) or getattr(message, "caption", None)
                        if text:
                            return text[entity.offset: entity.offset + entity.length]
            if getattr(message, "caption_entities", None):
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        resultdata = (await results.next()).get("result", [])
        if not resultdata:
            return (None, None, 0, None, None)
        result = resultdata[0]
        title = result.get("title")
        duration_min = result.get("duration")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0] if result.get("thumbnails") else None
        vidid = result.get("id")
        duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        resultdata = (await results.next()).get("result", [])
        return resultdata[0]["title"] if resultdata else None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        resultdata = (await results.next()).get("result", [])
        return resultdata[0]["duration"] if resultdata else None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        resultdata = (await results.next()).get("result", [])
        return resultdata[0]["thumbnails"][0]["url"].split("?")[0] if resultdata else None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + str(link)
        if "&" in link:
            link = link.split("&")[0]
        cookie_file = cookie_txt_file()
        if not cookie_file:
            # still try without cookies
            cookie_arg = ""
        else:
            cookie_arg = f"--cookies {cookie_file}"
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist {cookie_arg} --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        resultdata = (await results.next()).get("result", [])
        if not resultdata:
            return {}, None
        result = resultdata[0]
        track_details = {
            "title": result.get("title"),
            "link": result.get("link"),
            "vidid": result.get("id"),
            "duration_min": result.get("duration"),
            "thumb": result["thumbnails"][0]["url"].split("?")[0] if result.get("thumbnails") else None,
        }
        vidid = result.get("id")
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        """
        Extract formats using yt_dlp in a thread executor to avoid blocking.
        Returns (formats_available, link)
        """
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        cookie_file = cookie_txt_file()
        ytdl_opts = {"quiet": True}
        if cookie_file:
            ytdl_opts["cookiefile"] = cookie_file

        def _extract():
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            with ydl:
                formats_available = []
                r = ydl.extract_info(link, download=False)
                for fmt in r.get("formats", []):
                    try:
                        if "dash" not in str(fmt.get("format", "")).lower():
                            formats_available.append(
                                {
                                    "format": fmt.get("format"),
                                    "filesize": fmt.get("filesize") or fmt.get("filesize_approx"),
                                    "format_id": fmt.get("format_id"),
                                    "ext": fmt.get("ext"),
                                    "format_note": fmt.get("format_note"),
                                    "yturl": link,
                                }
                            )
                    except Exception:
                        continue
                return formats_available, link

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _extract)

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result", [])
        if not result or query_type >= len(result):
            return None, None, None, None
        res = result[query_type]
        title = res.get("title")
        duration_min = res.get("duration")
        vidid = res.get("id")
        thumbnail = res["thumbnails"][0]["url"].split("?")[0] if res.get("thumbnails") else None
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic=None,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + str(link)
        try:
            if songvideo:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            elif songaudio or not video:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            elif video:
                downloaded_file = await download_video(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
            else:
                downloaded_file = await download_song(link)
                if downloaded_file:
                    return downloaded_file, True
                else:
                    return None, False
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None, False
