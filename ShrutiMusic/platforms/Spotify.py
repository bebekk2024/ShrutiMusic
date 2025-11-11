import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython.__future__ import VideosSearch

import config

class SpotifyAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/open.spotify.com\/)(.*)$"
        self.client_id = config.SPOTIFY_CLIENT_ID
        self.client_secret = config.SPOTIFY_CLIENT_SECRET
        try:
            if config.SPOTIFY_CLIENT_ID and config.SPOTIFY_CLIENT_SECRET:
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

    async def valid(self, link: str):
        try:
            return bool(re.search(self.regex, link))
        except Exception as e:
            print(f"[SpotifyAPI.valid] Error: {e}")
            return False

    async def track(self, link: str):
        if not self.spotify:
            print("[SpotifyAPI.track] Spotify client not initialized.")
            return False
        try:
            track = self.spotify.track(link)
            info = track["name"]
            for artist in track["artists"]:
                fetched = f' {artist["name"]}'
                if "Various Artists" not in fetched:
                    info += fetched
            try:
                results = VideosSearch(info, limit=1)
                resultdata = (await results.next())["result"]
                if not resultdata:
                    print(f"[SpotifyAPI.track] No YouTube result for {info}")
                    return False
                result = resultdata[0]
                ytlink = result.get("link")
                title = result.get("title")
                vidid = result.get("id")
                duration_min = result.get("duration")
                thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
                track_details = {
                    "title": title,
                    "link": ytlink,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumbnail,
                }
                return track_details, vidid
            except Exception as e:
                print(f"[SpotifyAPI.track] Error querying YouTube: {e}")
                return False
        except Exception as e:
            print(f"[SpotifyAPI.track] Error fetching Spotify track: {e}")
            return False

    async def playlist(self, url):
        if not self.spotify:
            print("[SpotifyAPI.playlist] Spotify client not initialized.")
            return False
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
            return False

    async def album(self, url):
        if not self.spotify:
            print("[SpotifyAPI.album] Spotify client not initialized.")
            return False
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
            return False

    async def artist(self, url):
        if not self.spotify:
            print("[SpotifyAPI.artist] Spotify client not initialized.")
            return False
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
            return False
