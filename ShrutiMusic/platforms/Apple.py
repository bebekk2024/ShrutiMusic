import re
from typing import Union, Optional, Tuple, Dict, List

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
        print(f"[AppleAPI/_yt_dlp_info] yt_dlp exception: {e}")
        return None

class AppleAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/music.apple.com\/)(.*)$"
        self.base = "https://music.apple.com/in/playlist/"
    
    async def valid(self, link: str) -> bool:
        try:
            return bool(re.search(self.regex, link))
        except Exception as e:
            print(f"[AppleAPI.valid] Error: {e}")
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
            print(f"[AppleAPI._search_youtube] Exception: {e}")
            return None

    async def track(self, url: str, playid: Union[bool, str] = None) -> Optional[Tuple[Dict, Optional[str]]]:
        if playid:
            url = self.base + url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[AppleAPI.track] Page GET failed: {response.status} {url}")
                        return None
                    html = await response.text()
        except Exception as e:
            print(f"[AppleAPI.track] Error fetching Apple Music track: {e}")
            return None

        # Ambil title dari og:title
        soup = BeautifulSoup(html, "html.parser")
        search_query = None
        for tag in soup.find_all("meta"):
            if tag.get("property") == "og:title":
                search_query = tag.get("content")
                break
        if not search_query:
            print(f"[AppleAPI.track] No og:title meta found in {url}")
            return None

        # YouTube search
        yt_result = await self._search_youtube(search_query)
        if yt_result is not None:
            return yt_result, yt_result.get("vidid")
        
        # Fallback: yt_dlp as search
        info = await asyncio.get_event_loop().run_in_executor(None, _yt_dlp_info, search_query)
        if info and info.get("title"):
            out = {
                "title": info.get("title"),
                "link": f"https://www.youtube.com/watch?v={info.get('id')}",
                "vidid": info.get("id"),
                "duration_min": info.get("duration"),
                "thumb": info.get("thumbnail"),
            }
            return out, info.get("id")
        
        print(f"[AppleAPI.track] No YouTube result for query: {search_query}")
        return None

    async def playlist(self, url: str, playid: Union[bool, str] = None) -> Optional[Tuple[List[str], Optional[str]]]:
        if playid:
            url = self.base + url
        playlist_id = None
        try:
            playlist_id = url.split("playlist/")[1]
        except Exception as e:
            print(f"[AppleAPI.playlist] Error extracting playlist_id: {e}")
        # Fetch HTML
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[AppleAPI.playlist] Page GET failed: {response.status} {url}")
                        return None
                    html = await response.text()
        except Exception as e:
            print(f"[AppleAPI.playlist] Error fetching playlist: {e}")
            return None
        # Parse and extract songs/titles (sangat bergantung pada struktur HTML Apple)
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Coba ambil semua judul lagu via meta[property=music:song] atau fallback meta og:title per track.
            applelinks = soup.find_all("meta", attrs={"property": "music:song"})
            results = []
            for item in applelinks:
                cont = item.get("content", "")
                try:
                    # kadang format URL: "https://music.apple.com/.../song/trackid"
                    if "/song/" in cont:
                        songid = cont.split("/song/")[1].split("?")[0]
                        results.append(songid)
                except Exception as e:
                    print(f"[AppleAPI.playlist] Error parsing song item: {e} -- {cont}")
                    continue
            if not results:
                print("[AppleAPI.playlist] No Apple songs found (property=music:song)")
            return results, playlist_id
        except Exception as e:
            print(f"[AppleAPI.playlist] Error parsing songs: {e}")
            return None
