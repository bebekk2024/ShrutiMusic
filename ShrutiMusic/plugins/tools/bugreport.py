from pyrogram import filters
from ShrutiMusic import app
from ShrutiMusic.utils.error import capture_err

@app.on_message(filters.command("bug") & filters.group)
@capture_err
async def bug_command(client, message):
    await message.reply_text(
        "Terima kasih sudah melaporkan bug. Tim admin akan segera memeriksa laporan ini."
    )
    # kode utama lain jika perlu
