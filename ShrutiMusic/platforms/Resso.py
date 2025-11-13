import re
from typing import Union, Tuple, Optional, Dict

import aiohttp
from bs4 import BeautifulSoup
from youtubesearchpython.__future__ import VideosSearch
import yt_dlp
import asyncio

def _yt_dlp_info(query: str):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(query, download=False)
        return info
    except Exception as e:
        print(f"[RessoAPI/_yt_dlp_info] yt_dlp exception: {e}")
        return None

class RessoAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/m.resso.com\/)(.*)$"
        self.base = "https://m.resso.com/"

    async def valid(self, link: str) -> bool:
        try:
            return bool(re.search(self.regex, link))
        except Exception as e:
            print(f"[RessoAPI.valid] Error: {e}")
            return False

    async def _search_youtube(self, query: str) -> Optional[Dict]:
        try:
            vs = VideosSearch(query, limit=1)
            resultdata = (await vs.next()).get("result", [])
            if not resultdata:
                return None
            r = resultdata[0]
            return {
                "title": r.get("title"),
                "link": r.get("link"),
                "vidid": r.get("id"),
                "duration_min": r.get("duration"),
                "thumb": r.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
            }
        except Exception as e:
            print(f"[RessoAPI._search_youtube] Exception: {e}")
            return None

    async def track(self, url: str, playid: Union[bool, str] = None) -> Optional[Tuple[Dict, Optional[str]]]:
        if playid:
            url = self.base + url

        # Fetch page
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[RessoAPI.track] Page GET failed: {response.status} {url}")
                        return None
                    html = await response.text()
        except Exception as e:
            print(f"[RessoAPI.track] Error fetching Resso page: {e}")
            return None

        # Parse and get title from meta
        soup = BeautifulSoup(html, "html.parser")
        title, des = None, ""
        for tag in soup.find_all("meta"):
            if tag.get("property") == "og:title":
                title = tag.get("content")
            if tag.get("property") == "og:description":
                des = tag.get("content", "")
                try:
                    des = des.split("·")[0]
                except Exception:
                    pass
        if not title or des == "":
            print(f"[RessoAPI.track] Missing title or empty description.")
            return None

        # YouTube search
        yt_result = await self._search_youtube(title)
        if yt_result is not None:
            return yt_result, yt_result.get("vidid")

        # Fallback: yt_dlp as search
        info = await asyncio.get_event_loop().run_in_executor(None, _yt_dlp_info, title)
        if info and info.get("title"):
            out = {
                "title": info.get("title"),
                "link": f"https://www.youtube.com/watch?v={info.get('id')}",
                "vidid": info.get("id"),
                "duration_min": info.get("duration"),
                "thumb": info.get("thumbnail"),
            }
            return out, info.get("id")

        print(f"[RessoAPI.track] No YouTube result for query: {title}")
        return None
