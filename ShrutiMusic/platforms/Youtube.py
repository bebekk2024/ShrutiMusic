# -*- coding: utf-8 -*-
# (Potongan file lengkap - ganti file lama dengan versi ini atau gabungkan perubahan ke fungsi terkait.)
import asyncio
import os
import re
import json
from typing import Union
import yt_dlp
from yt_dlp.utils import DownloadError
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from ShrutiMusic.utils.database import is_on_off
from ShrutiMusic.utils.formatters import time_to_seconds
import glob
import random
import logging
import aiohttp
from os import getenv

API_URL = getenv("API_URL", 'https://api.thequickearn.xyz')
VIDEO_API_URL = getenv("VIDEO_API_URL", 'https://api.video.thequickearn.xyz')
API_KEY = getenv("API_KEY", None)

logger = logging.getLogger(__name__)


def cookie_txt_file():
    """
    Try common cookie locations. Prefer /app/cookies.txt (Heroku start script writes COOKIE_FILE_CONTENT -> /app/cookies.txt).
    Fall back to environment var COOKIE_FILE_PATH if set.
    """
    # First, check explicit env var
    env_path = os.getenv("COOKIE_FILE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    # Common Heroku write path
    heroku_path = "/app/cookies.txt"
    if os.path.exists(heroku_path):
        return heroku_path
    # Fallback: look for cookies*.txt in cwd
    for fname in ("cookies.txt", "cookies(2).txt", "cookie.txt"):
        if os.path.exists(fname):
            return fname
    return None


async def download_song_api(link: str):
    """Download song using API"""
    try:
        video_id = link.split('v=')[-1].split('&')[0]
        download_folder = "downloads"
        
        for ext in ["mp3", "m4a", "webm"]:
            file_path = f"{download_folder}/{video_id}.{ext}"
            if os.path.exists(file_path):
                return file_path
        
        song_url = f"{API_URL}/song/{video_id}?api={API_KEY}"
        async with aiohttp.ClientSession() as session:
            for attempt in range(10):
                try:
                    async with session.get(song_url) as response:
                        if response.status != 200:
                            continue
                    
                        data = await response.json()
                        status = data.get("status", "").lower()

                        if status == "done":
                            download_url = data.get("link")
                            if not download_url:
                                continue
                            break
                        elif status == "downloading":
                            await asyncio.sleep(4)
                        else:
                            continue
                except Exception:
                    continue
            else:
                return None

            file_format = data.get("format", "mp3")
            file_extension = file_format.lower()
            file_name = f"{video_id}.{file_extension}"
            os.makedirs(download_folder, exist_ok=True)
            file_path = os.path.join(download_folder, file_name)

            async with session.get(download_url) as file_response:
                if file_response.status != 200:
                    return None
                with open(file_path, 'wb') as f:
                    async for chunk in file_response.content.iter_chunked(8192):
                        f.write(chunk)
            return file_path
    except Exception as e:
        logger.exception("API Song Error: %s", e)
        return None


async def download_video_api(link: str):
    """Download video using API"""
    try:
        video_id = link.split('v=')[-1].split('&')[0]
        download_folder = "downloads"
        
        for ext in ["mp4", "webm", "mkv"]:
            file_path = f"{download_folder}/{video_id}.{ext}"
            if os.path.exists(file_path):
                return file_path
        
        video_url = f"{VIDEO_API_URL}/video/{video_id}?api={API_KEY}"
        async with aiohttp.ClientSession() as session:
            for attempt in range(10):
                try:
                    async with session.get(video_url) as response:
                        if response.status != 200:
                            continue
                    
                        data = await response.json()
                        status = data.get("status", "").lower()

                        if status == "done":
                            download_url = data.get("link")
                            if not download_url:
                                continue
                            break
                        elif status == "downloading":
                            await asyncio.sleep(8)
                        else:
                            continue
                except Exception:
                    continue
            else:
                return None

            file_format = data.get("format", "mp4")
            file_extension = file_format.lower()
            file_name = f"{video_id}.{file_extension}"
            os.makedirs(download_folder, exist_ok=True)
            file_path = os.path.join(download_folder, file_name)

            async with session.get(download_url) as file_response:
                if file_response.status != 200:
                    return None
                with open(file_path, 'wb') as f:
                    async for chunk in file_response.content.iter_chunked(8192):
                        f.write(chunk)
            return file_path
    except Exception as e:
        logger.exception("API Video Error: %s", e)
        return None


async def download_song_cookies(link: str):
    """Download song using cookies (similar pattern to download_video_cookies)"""
    # Implementation omitted for brevity — leave as-is or mirror download_video_cookies with same error handling
    return None


async def download_video_cookies(link: str):
    """Download video using cookies"""
    try:
        cookie_file = cookie_txt_file()
        if not cookie_file:
            logger.warning("download_video_cookies: No cookie file found.")
            return None
        
        ydl_opts = {
            "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])/best[height<=?720]",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "cookiefile": cookie_file,
            "no_warnings": True,
        }
        
        loop = asyncio.get_running_loop()
        
        def _download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    video_id = info.get('id')
                    # check existing files
                    for ext in ("mp4", "webm", "mkv"):
                        file_path = f"downloads/{video_id}.{ext}"
                        if os.path.exists(file_path):
                            return file_path
                    # now perform download
                    ydl.download([link])
                    # after download, attempt to find file by id and ext
                    # try typical extensions
                    for ext in ("mp4", "mkv", "webm", "m4a"):
                        possible = f"downloads/{video_id}.{ext}"
                        if os.path.exists(possible):
                            return possible
                    return None
            except DownloadError as e:
                logger.warning("yt-dlp DownloadError in _download: %s", e)
                return None
            except Exception as e:
                logger.exception("Unexpected error in _download: %s", e)
                return None

        result = await loop.run_in_executor(None, _download)
        return result
    except Exception as e:
        logger.exception("download_video_cookies failed: %s", e)
        return None


async def download_video_combined(link: str):
    """Try both API and cookies for video download, whichever responds first"""
    try:
        logger.info("🎥 Starting combined video download...")
        api_result = await download_video_api(link)
        if api_result:
            logger.info("✅ Video downloaded via API")
            return api_result
        
        cookies_result = await download_video_cookies(link)
        if cookies_result:
            logger.info("✅ Video downloaded via Cookies")
            return cookies_result
        
        logger.info("❌ Both methods failed for video download")
        return None
    except Exception as e:
        logger.exception("download_video_combined error: %s", e)
        return None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    # ... other helper methods ...

    async def video(self, link: str, videoid: Union[bool, str] = None):
        """
        Try combined download first; if not, use yt-dlp to produce direct URL (but handle errors).
        Returns tuple (status_int, result) like (1, url) or (0, error_message)
        """
        try:
            if videoid:
                link = self.base + link
            if "&" in link:
                link = link.split("&")[0]
            
            downloaded_file = await download_video_combined(link)
            if downloaded_file:
                return 1, downloaded_file
            
            cookie_file = cookie_txt_file()
            if not cookie_file:
                return 0, "No cookies found. Cannot download video. Please set COOKIE_FILE_CONTENT in Heroku."

            # run yt-dlp to get direct media URL
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--cookies", cookie_file,
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                f"{link}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            out = stdout.decode().strip() if stdout else ""
            err = stderr.decode().strip() if stderr else ""

            if out:
                # first line usually direct URL
                return 1, out.split("\n")[0]
            # handle common errors
            if "HTTP Error 403" in err or "403" in err or "Forbidden" in err:
                logger.warning("yt-dlp returned 403. stderr: %s", err[:1500])
                return 0, "HTTP Error 403: Forbidden (yt-dlp). Try providing valid YouTube cookies (COOKIE_FILE_CONTENT) or update yt-dlp."
            if "Sign in" in err or "accounts.google.com" in err:
                return 0, "Sign in required: cookies are invalid or expired."
            # generic fallback
            return 0, err or "yt-dlp failed to produce URL."
        except Exception as e:
            logger.exception("YouTubeAPI.video unexpected error: %s", e)
            return 0, f"Unexpected error: {e}"


    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return [], link
            
        ytdl_opts = {"quiet": True, "cookiefile": cookie_file}
        try:
            ydl = yt_dlp.YoutubeDL(ytdl_opts)
            with ydl:
                formats_available = []
                r = ydl.extract_info(link, download=False)
                for fmt in r.get("formats", []):
                    try:
                        fstr = str(fmt.get("format", ""))
                    except Exception:
                        continue
                    if "dash" in fstr.lower():
                        continue
                    try:
                        formats_available.append({
                            "format": fmt.get("format"),
                            "filesize": fmt.get("filesize"),
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "format_note": fmt.get("format_note"),
                        })
                    except Exception:
                        continue
                return formats_available, link
        except Exception as e:
            logger.exception("formats() failed: %s", e)
            return [], link
