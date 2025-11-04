# plugins/tools/bugreport.py
# Handler perintah /bug — kirim konfirmasi ke pengirim dan laporkan ke OWNER_ID (robust import)

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


@app.on_message(filters.command("bug") & filters.group)
async def bug_command(client, message: Message):
    user = message.from_user
    user_mention = user.mention if user else "Pengguna"
    # Ambil teks laporan (pesan setelah /bug) — jika tidak ada, gunakan reply/placeholder
    payload = ""
    if message.command and len(message.command) > 1:
        # /bug <laporan>
        payload = message.text.split(None, 1)[1]
    elif message.reply_to_message:
        # jika reply ke pesan, gunakan teks pesan yang direply
        payload = message.reply_to_message.text or message.reply_to_message.caption or ""
    else:
        payload = "(tidak ada detail diberikan)"

    await message.reply_text(
        f"Terima kasih {user_mention} sudah melaporkan bug. Tim admin akan segera memeriksa laporan ini."
    )

    # Susun laporan yang dikirim ke owner (jika tersedia)
    report = (
        f"[BUG REPORT]\n"
        f"User: {user_mention} (id: {getattr(user, 'id', '-')})\n"
        f"Chat: {getattr(message.chat, 'title', message.chat.id)} ({message.chat.id})\n"
        f"Time: {message.date}\n\n"
        f"Report:\n{payload}"
    )

    if OWNER_ID:
        try:
            await app.send_message(OWNER_ID, report)
        except Exception as e:
            # jika gagal kirim ke owner, beri tahu di grup bahwa pengiriman gagal
            await message.reply_text(f"⚠️ Gagal mengirim laporan ke owner: {type(e).__name__}: {e}")
    else:
        # fallback: owner id tidak dikonfigurasi
        await message.reply_text(
            "⚠️ OWNER_ID belum dikonfigurasi, laporan tidak dapat dikirim ke owner. "
            "Silakan hubungi owner secara manual."
        )
