import re
from typing import Union

import aiohttp
from bs4 import BeautifulSoup
from youtubesearchpython.__future__ import VideosSearch


class RessoAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/m.resso.com\/)(.*)$"
        self.base = "https://m.resso.com/"

    async def valid(self, link: str):
        try:
            return bool(re.search(self.regex, link))
        except Exception as e:
            print(f"[RessoAPI.valid] Error: {e}")
            return False

    async def track(self, url, playid: Union[bool, str] = None):
        if playid:
            url = self.base + url
        
        # Fetch page
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"[RessoAPI.track] Page GET failed: {response.status}")
                        return False
                    html = await response.text()
        except Exception as e:
            print(f"[RessoAPI.track] Error fetching Resso page: {e}")
            return False

        # Parse and query YouTube
        try:
            soup = BeautifulSoup(html, "html.parser")
            title, des = None, ""
            for tag in soup.find_all("meta"):
                if tag.get("property", None) == "og:title":
                    title = tag.get("content", None)
                if tag.get("property", None) == "og:description":
                    des = tag.get("content", None)
                    try:
                        des = des.split("·")[0]
                    except Exception:
                        pass
            if not title or des == "":
                print(f"[RessoAPI.track] Missing title or empty description.")
                return False
            results = VideosSearch(title, limit=1)
            resultdata = (await results.next()).get("result", [])
            if not resultdata:
                print(f"[RessoAPI.track] No search result in YouTube for {title}")
                return False
            result = resultdata[0]
            yt_title = result.get("title")
            ytlink = result.get("link")
            vidid = result.get("id")
            duration_min = result.get("duration")
            thumbnail = result.get("thumbnails", [{}])[0].get("url","").split("?")[0]
            track_details = {
                "title": yt_title,
                "link": ytlink,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }
            return track_details, vidid
        except Exception as e:
            print(f"[RessoAPI.track] Error in parsing or YouTube lookup: {e}")
            return False
