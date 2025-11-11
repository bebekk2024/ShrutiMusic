import re
from typing import Union

import aiohttp
from bs4 import BeautifulSoup
from youtubesearchpython.__future__ import VideosSearch

class AppleAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/music.apple.com\/)(.*)$"
        self.base = "https://music.apple.com/in/playlist/"

    async def valid(self, link: str):
        try:
            return bool(re.search(self.regex, link))
        except Exception as e:
            print(f"[AppleAPI.valid] Error: {e}")
            return False

    async def track(self, url, playid: Union[bool, str] = None):
        if playid:
            url = self.base + url
        # Fetch page
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[AppleAPI.track] Page GET failed: {response.status}")
                        return False
                    html = await response.text()
        except Exception as e:
            print(f"[AppleAPI.track] Error fetching Apple Music track: {e}")
            return False
        # Parse and query YouTube
        try:
            soup = BeautifulSoup(html, "html.parser")
            search = None
            for tag in soup.find_all("meta"):
                if tag.get("property", None) == "og:title":
                    search = tag.get("content", None)
            if search is None:
                print("[AppleAPI.track] No og:title meta found")
                return False
            results = VideosSearch(search, limit=1)
            resultdata = (await results.next()).get("result", [])
            if not resultdata:
                print(f"[AppleAPI.track] No search result in YouTube for {search}")
                return False
            result = resultdata[0]
            title = result.get("title")
            ytlink = result.get("link")
            vidid = result.get("id")
            duration_min = result.get("duration")
            thumbnail = result.get("thumbnails", [{}])[0].get("url","").split("?")[0]
            track_details = {
                "title": title,
                "link": ytlink,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }
            return track_details, vidid
        except Exception as e:
            print(f"[AppleAPI.track] Error in parsing/video lookup: {e}")
            return False

    async def playlist(self, url, playid: Union[bool, str] = None):
        if playid:
            url = self.base + url
        try:
            playlist_id = url.split("playlist/")[1]
        except Exception as e:
            print(f"[AppleAPI.playlist] Error extracting playlist_id: {e}")
            playlist_id = None
        # Fetch page
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[AppleAPI.playlist] Page GET failed: {response.status}")
                        return False
                    html = await response.text()
        except Exception as e:
            print(f"[AppleAPI.playlist] Error fetching playlist: {e}")
            return False
        # Parse and extract songs
        try:
            soup = BeautifulSoup(html, "html.parser")
            applelinks = soup.find_all("meta", attrs={"property": "music:song"})
            results = []
            for item in applelinks:
                try:
                    xx = (((item["content"]).split("album/")[1]).split("/")[0]).replace(
                        "-", " "
                    )
                except Exception as e:
                    xx = ((item["content"]).split("album/")[1]).split("/")[0]
                results.append(xx)
            return results, playlist_id
        except Exception as e:
            print(f"[AppleAPI.playlist] Error parsing songs: {e}")
            return False
