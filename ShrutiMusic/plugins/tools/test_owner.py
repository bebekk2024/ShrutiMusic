from pyrogram import filters
from ShrutiMusic import app
from ShrutiMusic.config import OWNER_ID

@app.on_message(filters.command("testowner") & filters.private)
async def test_owner_cmd(client, message):
    """
    Perintah uji untuk memeriksa OWNER_ID tanpa menggunakan LOG_GROUP_ID.
    Jalankan perintah ini dari chat pribadi bot (DM).
    """
    await message.reply_text(f"OWNER_ID dari config: {OWNER_ID}")
    try:
        await app.send_message(OWNER_ID, "Test DM: bot sudah aktif.")
        await message.reply_text("Mencoba mengirim DM ke owner... selesai.")
    except Exception as e:
        # Beri tahu pemanggil bahwa pengiriman gagal dan sertakan tipe error singkat
        await message.reply_text(f"Test owner gagal: {type(e).__name__}: {e}")
