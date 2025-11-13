import re
from typing import Union, Optional, Tuple, Dict, List

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython.__future__ import VideosSearch
import yt_dlp
import asyncio

import config

def _yt_dlp_info(query: str):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(query, download=False)
        return info
    except Exception as e:
        print(f"[SpotifyAPI/_yt_dlp_info] yt_dlp exception: {e}")
        return None

class SpotifyAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/open.spotify.com\/)(.*)$"
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET
        try:
            if self.client_id and self.client_secret:
                self.client_credentials_manager = SpotifyClientCredentials(
                    self.client_id, self.client_secret
                )
                self.spotify = spotipy.Spotify(
                    client_credentials_manager=self.client_credentials_manager
                )
            else:
                self.spotify = None
        except Exception as e:
            print(f"[SpotifyAPI.__init__] Error initializing Spotipy: {e}")
            self.spotify = None

    async def valid(self, link: str) -> bool:
        try:
            return bool(re.search(self.regex, link))
        except Exception as e:
            print(f"[SpotifyAPI.valid] Error: {e}")
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
            print(f"[SpotifyAPI._search_youtube] Exception: {e}")
            return None

    async def track(self, link: str) -> Optional[Tuple[Dict, Optional[str]]]:
        if not self.spotify:
            print("[SpotifyAPI.track] Spotify client not initialized.")
            return None
        try:
            track = self.spotify.track(link)
            info = track["name"]
            for artist in track["artists"]:
                fetched = f' {artist["name"]}'
                if "Various Artists" not in fetched:
                    info += fetched
            # cari di youtube
            yt_result = await self._search_youtube(info)
            if yt_result is not None:
                return yt_result, yt_result.get("vidid")
            # fallback pakai yt-dlp
            info_dlp = await asyncio.get_event_loop().run_in_executor(None, _yt_dlp_info, info)
            if info_dlp and info_dlp.get("title"):
                out = {
                    "title": info_dlp.get("title"),
                    "link": f"https://www.youtube.com/watch?v={info_dlp.get('id')}",
                    "vidid": info_dlp.get("id"),
                    "duration_min": info_dlp.get("duration"),
                    "thumb": info_dlp.get("thumbnail"),
                }
                return out, info_dlp.get("id")
            print(f"[SpotifyAPI.track] No YouTube result for {info}")
            return None
        except Exception as e:
            print(f"[SpotifyAPI.track] Error fetching Spotify track: {e}")
            return None

    async def playlist(self, url: str) -> Optional[Tuple[List[str], str]]:
        if not self.spotify:
            print("[SpotifyAPI.playlist] Spotify client not initialized.")
            return None
        try:
            playlist = self.spotify.playlist(url)
            playlist_id = playlist.get("id", "")
            results = []
            for item in playlist.get("tracks", {}).get("items", []):
                music_track = item.get("track", {})
                info = music_track.get("name", "")
                for artist in music_track.get("artists", []):
                    fetched = f' {artist.get("name", "")}'
                    if "Various Artists" not in fetched:
                        info += fetched
                results.append(info)
            return results, playlist_id
        except Exception as e:
            print(f"[SpotifyAPI.playlist] Error fetching playlist: {e}")
            return None

    async def album(self, url: str) -> Optional[Tuple[List[str], str]]:
        if not self.spotify:
            print("[SpotifyAPI.album] Spotify client not initialized.")
            return None
        try:
            album = self.spotify.album(url)
            album_id = album.get("id", "")
            results = []
            for item in album.get("tracks", {}).get("items", []):
                info = item.get("name", "")
                for artist in item.get("artists", []):
                    fetched = f' {artist.get("name", "")}'
                    if "Various Artists" not in fetched:
                        info += fetched
                results.append(info)
            return results, album_id
        except Exception as e:
            print(f"[SpotifyAPI.album] Error fetching album: {e}")
            return None

    async def artist(self, url: str) -> Optional[Tuple[List[str], str]]:
        if not self.spotify:
            print("[SpotifyAPI.artist] Spotify client not initialized.")
            return None
        try:
            artistinfo = self.spotify.artist(url)
            artist_id = artistinfo.get("id", "")
            results = []
            artisttoptracks = self.spotify.artist_top_tracks(url)
            for item in artisttoptracks.get("tracks", []):
                info = item.get("name", "")
                for artist in item.get("artists", []):
                    fetched = f' {artist.get("name", "")}'
                    if "Various Artists" not in fetched:
                        info += fetched
                results.append(info)
            return results, artist_id
        except Exception as e:
            print(f"[SpotifyAPI.artist] Error fetching artist: {e}")
            return None
