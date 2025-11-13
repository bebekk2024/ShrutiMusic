import asyncio
import os
import re
import json
from typing import Union, Optional, Tuple, List
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from ShrutiMusic.utils.database import is_on_off
from ShrutiMusic import app, LOGGER
from ShrutiMusic.utils.formatters import time_to_seconds
import random
import aiohttp
from urllib.parse import urlparse

YOUR_API_URL = None


def cookie_txt_file() -> Optional[str]:
    """
    Try several plausible locations for the cookies folder:
      - cwd/ShrutiMusic/cookies
      - package-relative ../cookies or ../../cookies (in case file is executed from inside package)
    Return a random .txt cookie file path, or None if none found.
    """
    candidates = [
        os.path.join(os.getcwd(), "ShrutiMusic", "cookies"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cookies")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cookies")),
    ]
    for cookie_dir in candidates:
        if not cookie_dir:
            continue
        if os.path.exists(cookie_dir) and os.path.isdir(cookie_dir):
            cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
            if cookies_files:
                return os.path.join(cookie_dir, random.choice(cookies_files))
    return None


async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info("API URL loaded successfully")
                else:
                    logger.error(f"Failed to fetch API URL. HTTP Status: {response.status}")
    except Exception as e:
        logger.error(f"Error loading API URL: {e}")


async def get_api_url() -> Optional[str]:
    global YOUR_API_URL
    if not YOUR_API_URL:
        await load_api_url()
    return YOUR_API_URL


def _extract_telegram_channel_and_message(parsed_path_parts: List[str]) -> Optional[Tuple[Union[str, int], int]]:
    """
    Handle different t.me path formats:
      - /username/<message_id>
      - /c/<chat_id>/<message_id>  (channel posts forwarded from private chats)
    Returns (channel, message_id) where channel can be username string or numeric chat_id (-100<id>) as int.
    """
    if not parsed_path_parts:
        return None
    # /c/<chat_id>/<message_id>
    if parsed_path_parts[0] == "c" and len(parsed_path_parts) >= 3:
        chat_id = parsed_path_parts[1]
        msg_id = parsed_path_parts[2]
        try:
            channel = int(f"-100{int(chat_id)}")
            message_id = int(msg_id)
            return channel, message_id
        except Exception:
            return None
    # /<username>/<message_id>
    if len(parsed_path_parts) >= 2:
        username = parsed_path_parts[0]
        try:
            message_id = int(parsed_path_parts[1])
            return username, message_id
        except ValueError:
            return None
    return None


async def get_telegram_file(telegram_link: str, video_id: str, file_type: str) -> Optional[str]:
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    try:
        extension = ".webm" if file_type == "audio" else ".mkv"
        file_path = os.path.join("downloads", f"{video_id}{extension}")

        if os.path.exists(file_path):
            logger.info(f"📂 [LOCAL] File exists: {video_id}")
            return file_path

        parsed = urlparse(telegram_link)
        parts = [p for p in parsed.path.split("/") if p]
        parsed_result = _extract_telegram_channel_and_message(parts)
        if not parsed_result:
            logger.error(f"❌ Invalid Telegram link format: {telegram_link}")
            return None

        channel_name, message_id = parsed_result

        logger.info(f"📥 [TELEGRAM] Downloading from {channel_name}/{message_id}")
        # create downloads dir
        os.makedirs("downloads", exist_ok=True)

        try:
            msg = await app.get_messages(channel_name, message_id)
        except Exception as exc:
            logger.error(f"❌ Failed to fetch message @{channel_name}/{message_id}: {exc}")
            return None

        # If msg is None or file not present
        if not msg:
            logger.error(f"❌ Message not found: {telegram_link}")
            return None

        await msg.download(file_name=file_path)
        timeout = 0.0
        while not os.path.exists(file_path) and timeout < 60.0:
            await asyncio.sleep(0.5)
            timeout += 0.5
        if os.path.exists(file_path):
            logger.info(f"✅ [TELEGRAM] Downloaded: {video_id}")
            return file_path
        else:
            logger.error(f"❌ [TELEGRAM] Timeout: {video_id}")
            return None
    except Exception as e:
        logger.error(f"❌ [TELEGRAM] Failed to download {video_id}: {e}")
        return None


def _is_youtube_url(query: str) -> bool:
    query = str(query)
    return "youtube.com" in query or "youtu.be" in query

def _is_video_id(query: str) -> bool:
    query = str(query).strip()
    return bool(re.fullmatch(r"[0-9A-Za-z_-]{11}", query))

def _get_youtube_id_from_url(url: str) -> str:
    # prioritaskan ambil video id dari url
    patterns = [
        r"v=([0-9A-Za-z_-]{11})",
        r"youtu.be/([0-9A-Za-z_-]{11})",
        r"/embed/([0-9A-Za-z_-]{11})",
        r"shorts/([0-9A-Za-z_-]{11})"
    ]
    for pat in patterns:
        match = re.search(pat, url)
        if match:
            return match.group(1)
    return url  # fallback

def _yt_dlp_info(video_param: str):
    """video_param: video id atau url"""
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_param, download=False)
        return info
    except Exception as e:
        print(f"yt_dlp exception: {e}")
        return None


def _extract_youtube_id(url: str) -> str:
    """
    Extract a YouTube video id from a variety of URL formats.
    If not found, return the original string (the code that uses it may accept full URLs).
    """
    # Typical 11-char id pattern
    id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?#]|$)", url)
    if id_match:
        return id_match.group(1)
    # youtu.be short link
    match = re.search(r"youtu\.be\/([0-9A-Za-z_-]{11})(?:[&?#]|$)", url)
    if match:
        return match.group(1)
    # fallback to return original
    return url


async def download_song(link: str) -> Optional[str]:
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    api_url = await get_api_url()
    if not api_url:
        logger.error("API URL not available")
        return None
    video_id = _extract_youtube_id(link)
    logger.info(f"🎵 [AUDIO] Starting download for: {video_id}")

    if not video_id or len(str(video_id)) < 3:
        return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.webm")
    if os.path.exists(file_path):
        logger.info(f"🎵 [LOCAL] File exists: {video_id}")
        return file_path
    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            async with session.get(
                f"{api_url}/download", params=params, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"[AUDIO] API error: {response.status} - {text}")
                    return None
                data = await response.json()
                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    logger.info(f"🔗 [AUDIO] Telegram link received: {telegram_link}")
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "audio")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        logger.warning(f"⚠️ [AUDIO] Telegram download failed")
                        return None
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    logger.info(f"[AUDIO] Stream URL obtained: {video_id}")
                    async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=300)) as file_response:
                        if file_response.status != 200:
                            logger.error(f"[AUDIO] Download failed: {file_response.status}")
                            return None
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                if not chunk:
                                    continue
                                f.write(chunk)
                        logger.info(f"🎉 [AUDIO] Downloaded: {video_id}")
                        return file_path
                else:
                    logger.error(f"[AUDIO] Invalid response: {data}")
                    return None
    except asyncio.TimeoutError:
        logger.error(f"[AUDIO] Timeout: {video_id}")
        return None
    except Exception as e:
        logger.error(f"[AUDIO] Exception: {video_id} - {e}")
        return None


async def download_video(link: str) -> Optional[str]:
    logger = LOGGER("ShrutiMusic/platforms/Youtube.py")
    api_url = await get_api_url()
    if not api_url:
        logger.error("API URL not available")
        return None
    video_id = _extract_youtube_id(link)
    logger.info(f"🎥 [VIDEO] Starting download for: {video_id}")
    if not video_id or len(str(video_id)) < 3:
        return None
    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mkv")
    if os.path.exists(file_path):
        logger.info(f"🎥 [LOCAL] File exists: {video_id}")
        return file_path
    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            async with session.get(f"{api_url}/download", params=params, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"[VIDEO] API error: {response.status} - {text}")
                    return None
                data = await response.json()
                if data.get("link") and "t.me" in str(data.get("link")):
                    telegram_link = data["link"]
                    logger.info(f"🔗 [VIDEO] Telegram link received: {telegram_link}")
                    downloaded_file = await get_telegram_file(telegram_link, video_id, "video")
                    if downloaded_file:
                        return downloaded_file
                    else:
                        logger.warning(f"⚠️ [VIDEO] Telegram download failed")
                        return None
                elif data.get("status") == "success" and data.get("stream_url"):
                    stream_url = data["stream_url"]
                    logger.info(f"[VIDEO] Stream URL obtained: {video_id}")
                    async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=600)) as file_response:
                        if file_response.status != 200:
                            logger.error(f"[VIDEO] Download failed: {file_response.status}")
                            return None
                        with open(file_path, "wb") as f:
                            async for chunk in file_response.content.iter_chunked(16384):
                                if not chunk:
                                    continue
                                f.write(chunk)
                        logger.info(f"🎉 [VIDEO] Downloaded: {video_id}")
                        return file_path
                else:
                    logger.error(f"[VIDEO] Invalid response: {data}")
                    return None
    except asyncio.TimeoutError:
        logger.error(f"[VIDEO] Timeout: {video_id}")
        return None
    except Exception as e:
        logger.error(f"[VIDEO] Exception: {video_id} - {e}")
        return None


async def check_file_size(link: str) -> Optional[int]:
    def parse_size(formats):
        total_size = 0
        for fmt in formats:
            try:
                if fmt.get("filesize"):
                    total_size += int(fmt.get("filesize"))
            except Exception:
                continue
        return total_size

    async def get_format_info(link):
        cookie_file = cookie_txt_file()
        if not cookie_file:
            # try without cookies as a fallback
            cmd = ["yt-dlp", "-J", link]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--cookies",
                cookie_file,
                "-J",
                link,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            # return None but log stderr
            try:
                err_text = stderr.decode()
            except Exception:
                err_text = str(stderr)
            print(f'Error:\n{err_text}')
            return None
        try:
            return json.loads(stdout.decode())
        except Exception:
            return None

    info = await get_format_info(link)
    if info is None:
        return None
    formats = info.get("formats", [])
    if not formats:
        print("No formats found.")
        return None
    total_size = parse_size(formats)
    return total_size


async def shell_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    out, errorz = await proc.communicate()
    err = errorz.decode("utf-8", errors="ignore")
    if errorz and "unavailable videos are hidden" in err.lower():
        return out.decode("utf-8", errors="ignore")
    elif errorz:
        return err
    return out.decode("utf-8", errors="ignore")


async def get_video_details(query: str):
    """
    Return: dict {
        'title', 'duration', 'id', 'thumbnail', 'link'
    } or error msg
    """
    data = {}
    query = query.strip()
    prefer_dlp = False
    if _is_youtube_url(query):
        vid = _get_youtube_id_from_url(query)
        prefer_dlp = True
    elif _is_video_id(query):
        vid = query
        prefer_dlp = True
    else:
        vid = query

    # Langsung gunakan yt_dlp jika prefer_dlp True
    if prefer_dlp:
        info = await asyncio.get_event_loop().run_in_executor(None, _yt_dlp_info, vid)
        if info and info.get("title"):
            data['title'] = info.get('title')
            data['duration'] = info.get('duration')
            data['id'] = info.get('id')
            data['thumbnail'] = info.get('thumbnail')
            data['link'] = f"https://www.youtube.com/watch?v={info.get('id')}"
            return data
        # fallback VideosSearch jika tidak ketemu pakai yt_dlp:
        try:
            search = VideosSearch(vid, limit=1)
            result = (await search.next()).get("result", [])
            if result:
                r = result[0]
                data['title'] = r['title']
                data['duration'] = r.get('duration')  # bisa jadi None
                data['id'] = r['id']
                data['thumbnail'] = r['thumbnails'][0]['url'].split("?")[0] if r.get('thumbnails') else None
                data['link'] = r.get('link')
                return data
        except Exception as e:
            pass
        return {"error": "Judul tidak ditemukan. Pastikan link/ID benar."}

    # Jika bukan id/url, coba VideosSearch keyword dulu
    try:
        search = VideosSearch(vid, limit=1)
        result = (await search.next()).get("result", [])
        if result:
            r = result[0]
            data['title'] = r['title']
            data['duration'] = r.get('duration')
            data['id'] = r['id']
            data['thumbnail'] = r['thumbnails'][0]['url'].split("?")[0] if r.get('thumbnails') else None
            data['link'] = r.get('link')
            return data
    except Exception as e:
        pass
    # Fallback, coba yt_dlp dari query
    info = await asyncio.get_event_loop().run_in_executor(None, _yt_dlp_info, query)
    if info and info.get("title"):
        data['title'] = info.get('title')
        data['duration'] = info.get('duration')
        data['id'] = info.get('id')
        data['thumbnail'] = info.get('thumbnail')
        data['link'] = f"https://www.youtube.com/watch?v={info.get('id')}"
        return data

    return {"error": "Judul tidak ditemukan. Cek koneksi dan kata kunci Anda."}


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.logger = LOGGER("ShrutiMusic/platforms/Youtube.py")

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + str(link)
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Optional[str]:
        messages = [message_1]
        if getattr(message_1, "reply_to_message", False):
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

    async def details(self, link: str, videoid: Union[bool, str] = None) -> Tuple[Optional[str], Optional[str], int, Optional[str], Optional[str]]:
        info = await get_video_details(link)
        if "error" in info:
            return None, None, 0, None, None
        title = info.get("title")
        duration_sec = info.get("duration")
        # Support for both time string and int (yt_dlp returns int detik, VideosSearch string MM:SS)
        if isinstance(duration_sec, str):
            duration_min = duration_sec
            try:
                duration_sec_int = int(time_to_seconds(duration_sec))
            except Exception:
                duration_sec_int = 0
        else:
            duration_min = str(duration_sec // 60) + ":" + str(duration_sec % 60).zfill(2) if duration_sec else None
            duration_sec_int = duration_sec or 0
        thumb = info.get("thumbnail")
        vidid = info.get("id")
        return title, duration_min, duration_sec_int, thumb, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> Optional[str]:
        info = await get_video_details(link)
        return info.get("title") if "title" in info else None

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> Optional[str]:
        info = await get_video_details(link)
        d = info.get("duration") if "duration" in info else None
        if d is not None:
            if isinstance(d, str):
                return d
            else:
                return str(d // 60) + ":" + str(d % 60).zfill(2)
        return None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> Optional[str]:
        info = await get_video_details(link)
        return info.get("thumbnail") if "thumbnail" in info else None

    async def video(self, link: str, videoid: Union[bool, str] = None) -> Tuple[int, Union[str, None]]:
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None) -> List[str]:
        if videoid:
            link = self.listbase + str(link)
        if "&" in link:
            link = link.split("&")[0]
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return []
        playlist_raw = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file} --playlist-end {limit} --skip-download {link}"
        )
        return [key.strip() for key in playlist_raw.split("\n") if key.strip()]

    async def track(self, link: str, videoid: Union[bool, str] = None) -> Tuple[dict, Optional[str]]:
        info = await get_video_details(link)
        if "error" in info:
            return {}, None
        vidid = info.get("id")
        return info, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        if "&" in link:
            link = link.split("&")[0]
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return [], link
        ytdl_opts = {"quiet": True, "cookiefile": cookie_file}
        def _extract_formats():
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
                                    "filesize": fmt.get("filesize"),
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
        return await loop.run_in_executor(None, _extract_formats)

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        info_list = []
        search = VideosSearch(link, limit=10)
        try:
            result = (await search.next()).get("result", [])
            if not result or query_type >= len(result):
                return None, None, None, None
            res = result[query_type]
            title = res.get("title")
            duration_min = res.get("duration")
            vidid = res.get("id")
            thumbnail = res["thumbnails"][0]["url"].split("?")[0] if res.get("thumbnails") else None
            return title, duration_min, thumbnail, vidid
        except Exception:
            return None, None, None, None

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
    ) -> Tuple[Optional[str], bool]:
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
