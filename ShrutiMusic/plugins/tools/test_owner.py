from pyrogram import filters
from ShrutiMusic import app
from pyrogram.types import Message

try:
    from ShrutiMusic import config
except ImportError:
    try:
        import config
    except ImportError:
        config = None

if config:
    OWNER_ID = getattr(config, "OWNER_ID", 5779185981)
else:
    OWNER_ID = 5779185981

@app.on_message(filters.command("testowner") & filters.private)
async def test_owner_cmd(client, message: Message):
    await message.reply_text(f"OWNER_ID dari config: {OWNER_ID}")
    if not OWNER_ID:
        await message.reply_text("⚠️ OWNER_ID tidak dikonfigurasi. Silakan periksa file config.py.")
        return
    try:
        await app.send_message(OWNER_ID, "Test DM: bot sudah aktif.")
        await message.reply_text("Mencoba mengirim DM ke owner... selesai.")
    except Exception as e:
        await message.reply_text(f"Test owner gagal: {type(e).__name__}: {e}")
