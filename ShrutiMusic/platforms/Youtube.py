import asyncio
import os
import re
import json
from typing import Union
import yt_dlp
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

def cookie_txt_file():
    cookie_dir = "ShrutiMusic/cookies"
    if not os.path.exists(cookie_dir):
        return None
    cookies_files = [f for f in os.listdir(cookie_dir) if f.endswith(".txt")]
    if not cookies_files:
        return None
    cookie_file = os.path.join(cookie_dir, random.choice(cookies_files))
    return cookie_file

async def download_song_api(link: str):
    """Download song using API"""
    try:
        video_id = link.split('v=')[-1].split('&')[0]
        download_folder = "downloads"
        
        # Check if file already exists
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

            # Download the file
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
        print(f"API Song Error: {e}")
        return None

async def download_song_cookies(link: str):
    """Download song using cookies"""
    try:
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return None
        
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "cookiefile": cookie_file,
            "no_warnings": True,
        }
        
        loop = asyncio.get_running_loop()
        
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                video_id = info['id']
                
                # Check if file already exists
                for ext in ["webm", "m4a", "mp3"]:
                    file_path = f"downloads/{video_id}.{ext}"
                    if os.path.exists(file_path):
                        return file_path
                
                # Download if not exists
                return ydl.download([link])
        
        result = await loop.run_in_executor(None, _download)
        
        # Get the actual file path
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            video_id = info['id']
            ext = info['ext']
            file_path = f"downloads/{video_id}.{ext}"
            
            if os.path.exists(file_path):
                return file_path
        return None
    except Exception as e:
        print(f"Cookies Song Error: {e}")
        return None

async def download_video_api(link: str):
    """Download video using API"""
    try:
        video_id = link.split('v=')[-1].split('&')[0]
        download_folder = "downloads"
        
        # Check if file already exists
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

            # Download the file
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
        print(f"API Video Error: {e}")
        return None

async def download_video_cookies(link: str):
    """Download video using cookies"""
    try:
        cookie_file = cookie_txt_file()
        if not cookie_file:
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                video_id = info['id']
                
                # Check if file already exists
                for ext in ["mp4", "webm", "mkv"]:
                    file_path = f"downloads/{video_id}.{ext}"
                    if os.path.exists(file_path):
                        return file_path
                
                # Download if not exists
                return ydl.download([link])
        
        result = await loop.run_in_executor(None, _download)
        
        # Get the actual file path
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            video_id = info['id']
            ext = info['ext']
            file_path = f"downloads/{video_id}.{ext}"
            
            if os.path.exists(file_path):
                return file_path
        return None
    except Exception as e:
        print(f"Cookies Video Error: {e}")
        return None

async def download_song_combined(link: str):
    """Try both API and cookies for song download, whichever responds first"""
    print("🔊 Starting combined song download...")
    
    # Try API first
    api_result = await download_song_api(link)
    if api_result:
        print("✅ Song downloaded via API")
        return api_result
    
    # If API fails, try cookies
    cookies_result = await download_song_cookies(link)
    if cookies_result:
        print("✅ Song downloaded via Cookies")
        return cookies_result
    
    print("❌ Both methods failed for song download")
    return None

async def download_video_combined(link: str):
    """Try both API and cookies for video download, whichever responds first"""
    print("🎥 Starting combined video download...")
    
    # Try API first
    api_result = await download_video_api(link)
    if api_result:
        print("✅ Video downloaded via API")
        return api_result
    
    # If API fails, try cookies
    cookies_result = await download_video_cookies(link)
    if cookies_result:
        print("✅ Video downloaded via Cookies")
        return cookies_result
    
    print("❌ Both methods failed for video download")
    return None

async def check_file_size(link):
    """Check file size using cookies"""
    async def get_format_info(link):
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return None
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    """Execute shell command"""
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

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        # Try combined download first
        downloaded_file = await download_video_combined(link)
        if downloaded_file:
            return 1, downloaded_file
        
        # Fallback to direct URL extraction
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return 0, "No cookies found. Cannot download video."
            
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
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return []
            
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file} --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return [], link
            
        ytdl_opts = {"quiet": True, "cookiefile": cookie_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        
        loop = asyncio.get_running_loop()
        
        def song_video_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download song video.")
                
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie_file,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            cookie_file = cookie_txt_file()
            if not cookie_file:
                raise Exception("No cookies found. Cannot download song audio.")
                
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie_file,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            # Try combined video download
            downloaded_file = await download_video_combined(link)
            if downloaded_file:
                direct = True
                return downloaded_file, direct
            
            # Fallback to direct URL
            if not await is_on_off(1):
                cookie_file = cookie_txt_file()
                if cookie_file:
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
                    if stdout:
                        downloaded_file = stdout.decode().split("\n")[0]
                        direct = False
                        return downloaded_file, direct
            
            # Check file size and download if within limits
            file_size = await check_file_size(link)
            if file_size:
                total_size_mb = file_size / (1024 * 1024)
                if total_size_mb <= 250:
                    # Try cookies download for video
                    cookies_result = await download_video_cookies(link)
                    if cookies_result:
                        direct = True
                        return cookies_result, direct
            
            return None, None
        else:
            # Audio download using combined method
            direct = True
            downloaded_file = await download_song_combined(link)
            return downloaded_file, direct
