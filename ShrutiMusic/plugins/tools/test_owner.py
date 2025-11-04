# plugins/tools/test_owner.py
# Test command to verify OWNER_ID is reachable; robust config import to avoid startup crash.

from pyrogram import filters
from ShrutiMusic import app
from pyrogram.types import Message

# Robust import for config: try package import first, then top-level module.
try:
    from ShrutiMusic.config import OWNER_ID as _OWNER_ID
except Exception:
    try:
        from config import OWNER_ID as _OWNER_ID
    except Exception:
        _OWNER_ID = None

# ensure OWNER_ID is int when possible
try:
    OWNER_ID = int(_OWNER_ID) if _OWNER_ID is not None else None
except Exception:
    OWNER_ID = None


@app.on_message(filters.command("testowner") & filters.private)
async def test_owner_cmd(client, message: Message):
    """
    Perintah uji untuk memeriksa OWNER_ID tanpa membuat bot crash saat config tidak tersedia.
    Jalankan perintah ini dari chat pribadi bot (DM).
    """
    await message.reply_text(f"OWNER_ID dari config: {OWNER_ID}")
    if not OWNER_ID:
        await message.reply_text("⚠️ OWNER_ID tidak dikonfigurasi. Silakan periksa file config.py.")
        return
    try:
        await app.send_message(OWNER_ID, "Test DM: bot sudah aktif.")
        await message.reply_text("Mencoba mengirim DM ke owner... selesai.")
    except Exception as e:
        await message.reply_text(f"Test owner gagal: {type(e).__name__}: {e}")
