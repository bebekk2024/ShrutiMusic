import asyncio
import random
import config

from ...utils.query_group import sangmata_group
from ShrutiMusic import app, userbot
from pyrogram import filters, raw
from ShrutiMusic.utils.query_group import sangmata_group
from ShrutiMusic.utils.database import dB
from ShrutiMusic.utils.decorators import ONLY_ADMIN, ONLY_GROUP
from pyrogram.types import Message

"""
SangMata plugin
- Lokasi file: ShrutiMusic/plugins/sangmata.py
- Disesuaikan untuk struktur paket ShrutiMusic (import dari paket).
- Perbaikan filter BANNED_USERS: gunakan filters.user(...) karena config.BANNED_USERS
  diinisialisasi sebagai set di __main__.py.
- Hindari client.mention (tidak selalu tersedia) — gunakan message.from_user.mention.
"""

@app.on_message(
    filters.group & ~filters.bot & ~filters.via_bot,
    group=sangmata_group,
)
async def sang_mata(client: app.__class__, message: Message):
    # Abaikan pesan dari sender_chat (anonymous channel)
    if message.sender_chat:
        return

    if not message.from_user:
        return

    user_id = message.from_user.id
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    username = message.from_user.username or ""

    # Simpan user pertama kali
    if not await dB.cek_userdata(user_id):
        await dB.add_userdata(user_id, first, last, username)
        return

    data = await dB.get_userdata(user_id)
    if not data:
        return

    old_first = data.get("depan", "")
    old_last = data.get("belakang", "")
    old_username = data.get("username", "")

    # Jika grup dinonaktifkan SangMata pada chat ini, skip
    if await dB.get_var(message.chat.id, "SICEPU"):
        return

    changes = []

    if old_username != username:
        old_u = f"@{old_username}" if old_username else "<b>Tanpa Username</b>"
        new_u = f"@{username}" if username else "<b>Tanpa Username</b>"
        changes.append(f"<b>🔄 Mengubah username dari <code>{old_u}</code> ke <code>{new_u}</code></b>.")

    if old_first != first:
        changes.append(f"<b>🔄 Mengubah nama depan dari <code>{old_first}</code> menjadi <code>{first}</code>.</b>")

    if old_last != last:
        old_l = old_last or "<b>Tanpa Nama Belakang</b>"
        new_l = last or "<b>Tanpa Nama Belakang</b>"
        changes.append(f"<b>🔄 Mengubah nama belakang dari <code>{old_l}</code> menjadi <code>{new_l}</code>.</b>")

    if changes:
        msg = "<b>👀 SangMata</b>\n\n"
        msg += f"<b>Pengguna : {message.from_user.mention} [<code>{user_id}</code>]</b>\n\n"
        msg += "\n".join(changes)
        await message.reply_text(msg, quote=True)

        # Perbarui data user di database
        await dB.add_userdata(user_id, first, last, username)


@app.on_message(filters.command("sangmata") & ~filters.bot & ~filters.via_bot)
@ONLY_ADMIN
@ONLY_GROUP
async def sangmata_cmd(client: app.__class__, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "><b>Gunakan format <code>/sangmata on</code>, untuk mengaktifkan sangmata.\n"
            "Jika Anda ingin menonaktifkan, Anda dapat menggunakan perintah <code>/sangmata off</code>.</b>"
        )
    state = message.command[1].lower()
    if state not in ["on", "off"]:
        return await message.reply_text(
            "><b>Gunakan format <code>/sangmata on</code>, untuk mengaktifkan sangmata.\n"
            "Jika Anda ingin menonaktifkan, Anda dapat menggunakan perintah <code>/sangmata off</code>.</b>"
        )
    if state == "on":
        # Jika var SICEPU ada berarti dinonaktifkan, jadi hapus untuk mengaktifkan
        if not await dB.get_var(message.chat.id, "SICEPU"):
            return await message.reply_text(">**Sangmata sudah diaktifkan**")
        await dB.remove_var(message.chat.id, "SICEPU")
        return await message.reply_text(">**Sangmata berhasil diaktifkan.**")
    else:
        # Set var SICEPU untuk menonaktifkan
        if await dB.get_var(message.chat.id, "SICEPU"):
            return await message.reply_text(">**Sangmata sudah dinonaktifkan**")
        await dB.set_var(message.chat.id, "SICEPU", True)
        return await message.reply_text(">**Sangmata berhasil dinonaktifkan.**")


# Perbaikan filter: config.BANNED_USERS di __main__ merupakan set, gunakan filters.user(...)
@app.on_message(filters.command(["sg"]) & ~filters.user(config.BANNED_USERS))
async def history(client: app.__class__, message: Message):
    reply = message.reply_to_message
    try:
        target = reply.from_user.id if reply else message.text.split()[1]
    except (AttributeError, IndexError):
        return await message.reply(">**Balas pesan pengguna atau berikan username pengguna.**")
    try:
        user_id = (await client.get_users(target)).id
    except Exception:
        try:
            user_id = int(message.command[1])
        except Exception:
            return await message.reply(">**ID pengguna tidak valid.**")
    proses = await message.reply(">**Please wait...**")
    bot_list = ["@Sangmata_bot", "@SangMata_beta_bot"]
    babu = userbot.clients[0]
    getbot = random.choice(bot_list)
    try:
        await babu.unblock_user(getbot)
    except Exception:
        # Jika gagal unblock, lanjutkan — userbot mungkin sudah bisa kirim
        pass
    try:
        txt = await babu.send_message(getbot, user_id)
    except Exception as e:
        await proses.edit(f"<b>❌ Gagal mengirim ke {getbot}: {e}</b>")
        return
    await asyncio.sleep(4)
    try:
        await txt.delete()
    except Exception:
        pass
    try:
        await proses.delete()
    except Exception:
        pass

    async for name in babu.search_messages(getbot, limit=2):
        if not getattr(name, "text", None):
            await message.reply(f"<b>❌ {getbot} ERROR, Silahkan kirim manual id pengguna ke {''.join(bot_list)}!</b>")
        else:
            await message.reply(name.text)

    try:
        user_info = await babu.resolve_peer(getbot)
        await babu.invoke(raw.functions.messages.DeleteHistory(peer=user_info, max_id=0, revoke=True))
    except Exception:
        # Jika tidak bisa menghapus history, abaikan
        pass


__MODULE__ = "SangMata"
__HELP__ = """
<blockquote expandable>
<b>🕵️‍♂️ SangMata Tracker</b>

<b>★ /sangmata</b> [on/off] – Enable or disable name change tracking in the group.  
<b>★ /sg</b> [userID/reply] – View user name history.
</blockquote>
"""
