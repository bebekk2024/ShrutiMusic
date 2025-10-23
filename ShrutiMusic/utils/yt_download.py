# Helper untuk download/ambil metadata audio menggunakan yt-dlp
# Menangani HTTP 403 dengan retry, dan memberi opsi cookiefile / user agent.

import time
import logging
from typing import Optional, Dict, Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)

def extract_info_with_retries(url: str,
                              download: bool = False,
                              cookiefile: Optional[str] = None,
                              max_retries: int = 3,
                              initial_backoff: float = 2.0,
                              timeout_seconds: int = 30) -> Dict[str, Any]:
    """
    Extract info (or download) using yt-dlp with retry on HTTP 403 and transient errors.
    - url: target video URL
    - download: jika True, akan mengunduh file; jika False hanya mengambil metadata
    - cookiefile: path ke cookies.txt jika diperlukan untuk video restricted
    """
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        # Kalau mau simpan file hasil download, tambahkan 'outtmpl'
        # 'outtmpl': '/tmp/%(id)s.%(ext)s'
    }
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile

    # set user agent untuk mengurangi kemungkinan 403
    ydl_opts["http_headers"] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
    }

    backoff = initial_backoff
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            logger.info("yt-dlp attempt %d for url %s", attempt, url)
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=download)
                logger.info("yt-dlp success on attempt %d", attempt)
                return info
        except DownloadError as e:
            msg = str(e).lower()
            logger.warning("yt-dlp DownloadError on attempt %d: %s", attempt, msg)
            # Cek indikasi 403
            if "http error 403" in msg or "403" in msg:
                # Jika ada cookies dan belum dipakai, sarankan pakai cookiefile
                logger.warning("Detected HTTP 403. Consider using a cookiefile or updating yt-dlp.")
                # backoff then retry
                time.sleep(backoff)
                backoff *= 2
                continue
            # Jika error lain yang transient, coba retry juga
            if "timed out" in msg or "timeout" in msg or "temporarily unavailable" in msg:
                time.sleep(backoff)
                backoff *= 2
                continue
            # Untuk error fatal, raise
            raise
        except Exception as e:
            logger.exception("Unexpected error using yt-dlp on attempt %d", attempt)
            time.sleep(backoff)
            backoff *= 2
    # Jika mencapai sini, semua percobaan gagal
    raise RuntimeError(f"yt-dlp failed after {max_retries} attempts for url: {url}")
