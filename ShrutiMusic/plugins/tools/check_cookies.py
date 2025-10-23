# file: plugins/check_cookies.py

import os
import time
import tempfile
import asyncio
import subprocess
from datetime import datetime, timezone
import requests
import http.cookiejar as cookiejar

from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic import app


YOUTUBE_TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def load_cookies(path: str) -> requests.cookies.RequestsCookieJar:
    """Load cookies from file (netscape format or raw string)."""
    jar = requests.cookies.RequestsCookieJar()
    try:
        mj = cookiejar.MozillaCookieJar()
        mj.load(path, ignore_discard=True, ignore_expires=True)
        for c in mj:
            jar.set(c.name, c.value, domain=c.domain, path=c.path, expires=c.expires)
        return jar
    except Exception:
        # fallback: read as raw text
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                jar.set(k.strip(), v.strip())
        return jar


def format_exp(ts):
    if not ts:
        return "no-expiry"
    try:
        dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ts)


def check_login(jar):
    """Check if cookie works on subscriptions feed."""
    s = requests.Session()
    s.cookies = jar
    s.headers.update({"User-Agent": USER_AGENT})
    r = s.get("https://www.youtube.com/feed/subscriptions", allow_redirects=True, timeout=15)
    if "signin" in r.url or "accounts.google.com" in r.url:
        return False
    if "ytInitialData" in r.text:
        return True
    return False


def simulate_yt_dlp(cookie_path):
    """Run yt-dlp simulate check (no actual download)."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--cookies", cookie_path, "--simulate", "--no-warnings", "-g", YOUTUBE_TEST_VIDEO],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and "youtube.com" in result.stdout:
            return True, result.stdout.strip()
        elif "Sign in" in result.stderr or "Forbidden" in result.stderr:
            return False, result.stderr.strip()
        else:
            return False, (result.stdout + result.stderr).strip()
    except Exception as e:
        return False, str(e)


@app.on_message(filters.command("check") & filters.reply)
async def check_cookie_file(_, message: Message):
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("<b>Reply to a message that contains the cookie file.</b>")
        return

    m = await message.reply_text("<b>🔎 Checking cookies...</b>")

    file_path = None
    try:
        if reply.document:
            tmp = tempfile.gettempdir()
            file_path = os.path.join(tmp, f"cookie_{int(time.time())}.txt")
            await app.download_media(reply.document, file_name=file_path)
        elif reply.text:
            tmp = tempfile.gettempdir()
            file_path = os.path.join(tmp, f"cookie_{int(time.time())}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(reply.text)
        else:
            await m.edit("<b>No cookie data found in reply message.</b>")
            return

        # Check login
        jar = load_cookies(file_path)
        cookies_list = []
        for c in jar:
            cookies_list.append(f"<code>{c.name}</code> — {format_exp(getattr(c, 'expires', None))}")
        cookies_text = "<br>".join(cookies_list) or "No cookies parsed."

        login_ok = check_login(jar)
        valid_text = "✅ <b>VALID / LOGGED IN</b>" if login_ok else "❌ <b>EXPIRED / SIGNED OUT</b>"

        # yt-dlp simulate
        dl_ok, dl_log = simulate_yt_dlp(file_path)
        dl_text = "✅ <b>Download Works (yt-dlp OK)</b>" if dl_ok else "⚠️ <b>Download Failed</b>"
        dl_details = dl_log[:1500].replace("<", "&lt;").replace(">", "&gt;")

        text = (
            f"{valid_text}<br><br>"
            f"<b>Cookies found:</b><br>{cookies_text}<br><br>"
            f"{dl_text}<br>"
            f"<b>yt-dlp log:</b><br><code>{dl_details}</code><br><br>"
            "<i>Note: This test uses yt-dlp simulate mode; no actual file downloaded.</i>"
        )

        await m.edit_text(text, disable_web_page_preview=True)

    except Exception as e:
        await m.edit_text(f"<b>Error:</b> <code>{e}</code>")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
