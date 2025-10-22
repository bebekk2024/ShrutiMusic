import os
import base64
import tempfile
import logging

logger = logging.getLogger("ShrutiMusic.utils.cookies")

def write_cookies_from_env(env_var: str = "YT_COOKIES_BASE64") -> str | None:
    """
    If you put a base64-encoded cookies.txt into the env var YT_COOKIES_BASE64,
    this writes it to a temp file and returns its path.
    Use this file as yt-dlp cookiefile.
    """
    b64 = os.getenv(env_var)
    if not b64:
        logger.debug("No YT_COOKIES_BASE64 env var found")
        return None
    try:
        data = base64.b64decode(b64)
        tmp = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(tmp, "wb") as f:
            f.write(data)
        logger.info("Wrote cookies to %s", tmp)
        return tmp
    except Exception:
        logger.exception("Failed to write cookies from env")
        return None
