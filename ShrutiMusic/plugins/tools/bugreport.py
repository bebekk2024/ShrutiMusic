from pyrogram import filters
from ShrutiMusic import app
from ShrutiMusic.utils.error import capture_err
from ShrutiMusic.config import OWNER_ID  # Pastikan import ini!

@app.on_message(filters.command("bug") & filters.group)
@capture_err
async def bug_command(client, message):
    user = message.from_user.mention if message.from_user else "Pengguna"
    pesan_laporan = (
        f"<blockquote><b>{user} telah melaporkan bug:\n\n{message.text}\n\n</b></blockquote>"
        f"<blockquote><b>Di grup: {message.chat.title} ({message.chat.id}</b></blockquote>)"
    )
    await message.reply_text(
        f"<blockquote><b>Terima kasih {user} sudah melaporkan bug. Tim admin akan segera memeriksa laporan ini.</b></blockquote>"
    )
    try:
        await client.send_message(
            OWNER_ID,
            pesan_laporan
        )
    except Exception as e:
        await message.reply_text(f"<blockquote><b>Gagal mengirim laporan ke owner: {e}</b></blockquote>")
