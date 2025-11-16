import asyncio
import random
import importlib
import config

# Try to import sangmata_group from project's utils; fallback to default.
try:
    # prefer package-level utils.query_group
    from ShrutiMusic.utils.query_group import sangmata_group  # type: ignore
except Exception:
    try:
        # try relative import if package executed differently
        from ..utils.query_group import sangmata_group  # type: ignore
    except Exception:
        sangmata_group = 50  # default handler group/order if module missing

from ShrutiMusic import app, userbot
from pyrogram import filters, raw
from pyrogram.types import Message

# --- Normalize BANNED_USERS to a set of ints to avoid "unhashable type: 'user'" ---
def _normalize_banned_users(raw_banned):
    """
    Accepts:
      - set/list of ints
      - set/list of strings (usernames or numeric strings)
      - set/list of pyrogram.types.User objects
    Returns a set of ints (user ids). Non-convertible entries are ignored.
    """
    out = set()
    if not raw_banned:
        return out
    for item in raw_banned:
        try:
            # If item is a User object from pyrogram, it has .id
            uid = getattr(item, "id", None)
            if uid is None:
                # maybe it's numeric string or int
                uid = int(item)
            out.add(int(uid))
        except Exception:
            # ignore entries we cannot convert to int
            continue
    return out

_BANNED_USER_IDS = _normalize_banned_users(getattr(config, "BANNED_USERS", set()))

# --- Decorator compatibility (ONLY_ADMIN / ONLY_GROUP) ---
try:
    from ShrutiMusic.utils.decorators import ONLY_ADMIN, ONLY_GROUP  # type: ignore
except Exception:
    # fallback no-op decorators (compatible with @DECORATOR and @DECORATOR())
    def _noop_deco(*d_args, **d_kwargs):
        if len(d_args) == 1 and callable(d_args[0]) and not d_kwargs:
            func = d_args[0]
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        def inner(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return inner
    ONLY_ADMIN = _noop_deco()
    ONLY_GROUP = _noop_deco()

# --- Database proxy (not using symbol `dB`) ---
class _FallbackDB:
    def __init__(self):
        self._users = {}
        self._vars = {}

    async def cek_userdata(self, user_id):
        return user_id in self._users

    async def add_userdata(self, user_id, first, last, username):
        self._users[user_id] = {"depan": first or "", "belakang": last or "", "username": username or ""}
        return True

    async def get_userdata(self, user_id):
        return self._users.get(user_id)

    async def get_var(self, chat_id, name):
        return self._vars.get((chat_id, name))

    async def set_var(self, chat_id, name, value):
        self._vars[(chat_id, name)] = value
        return True

    async def remove_var(self, chat_id, name):
        return self._vars.pop((chat_id, name), None) is not None

# try to import project's database module and wrap it, else fallback
_db_mod = None
try:
    _db_mod = importlib.import_module("ShrutiMusic.utils.database")
except Exception:
    try:
        _db_mod = importlib.import_module("..utils.database", package=__package__)
    except Exception:
        _db_mod = None

class _DBProxy:
    def __init__(self, mod):
        self._mod = mod

    async def _call(self, func, *args, **kwargs):
        res = func(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return await res
        return res

    async def cek_userdata(self, user_id):
        func = getattr(self._mod, "cek_userdata", None)
        if callable(func):
            return await self._call(func, user_id)
        return await _FallbackDB().cek_userdata(user_id)

    async def add_userdata(self, user_id, first, last, username):
        func = getattr(self._mod, "add_userdata", None)
        if callable(func):
            return await self._call(func, user_id, first, last, username)
        return await _FallbackDB().add_userdata(user_id, first, last, username)

    async def get_userdata(self, user_id):
        func = getattr(self._mod, "get_userdata", None)
        if callable(func):
            return await self._call(func, user_id)
        return await _FallbackDB().get_userdata(user_id)

    async def get_var(self, chat_id, name):
        func = getattr(self._mod, "get_var", None)
        if callable(func):
            return await self._call(func, chat_id, name)
        return await _FallbackDB().get_var(chat_id, name)

    async def set_var(self, chat_id, name, value):
        func = getattr(self._mod, "set_var", None)
        if callable(func):
            return await self._call(func, chat_id, name, value)
        return await _FallbackDB().set_var(chat_id, name, value)

    async def remove_var(self, chat_id, name):
        func = getattr(self._mod, "remove_var", None)
        if callable(func):
            return await self._call(func, chat_id, name)
        return await _FallbackDB().remove_var(chat_id, name)

db = _DBProxy(_db_mod or _FallbackDB())


@app.on_message(
    filters.group & ~filters.bot & ~filters.via_bot,
    group=sangmata_group,
)
async def sang_mata(client: app.__class__, message: Message):
    if message.sender_chat:
        return

    if not message.from_user:
        return

    user_id = message.from_user.id
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    username = message.from_user.username or ""

    if not await db.cek_userdata(user_id):
        await db.add_userdata(user_id, first, last, username)
        return

    data = await db.get_userdata(user_id)
    if not data:
        return

    old_first = data.get("depan", "")
    old_last = data.get("belakang", "")
    old_username = data.get("username", "")

    if await db.get_var(message.chat.id, "SICEPU"):
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
        await db.add_userdata(user_id, first, last, username)


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
        if not await db.get_var(message.chat.id, "SICEPU"):
            return await message.reply_text(">**Sangmata sudah diaktifkan**")
        await db.remove_var(message.chat.id, "SICEPU")
        return await message.reply_text(">**Sangmata berhasil diaktifkan.**")
    else:
        if await db.get_var(message.chat.id, "SICEPU"):
            return await message.reply_text(">**Sangmata sudah dinonaktifkan**")
        await db.set_var(message.chat.id, "SICEPU", True)
        return await message.reply_text(">**Sangmata berhasil dinonaktifkan.**")


# Use normalized banned user ids in the filter to avoid TypeError
if _BANNED_USER_IDS:
    banned_filter = ~filters.user(_BANNED_USER_IDS)
else:
    # if empty, use a permissive filter (no banned users)
    banned_filter = ~filters.user([])

@app.on_message(filters.command(["sg"]) & banned_filter)
async def history(client: app.__class__, message: Message):
    reply = message.reply_to_message
    try:
        target = reply.from_user.id if reply else message.text.split()[1]
    except (AttributeError, IndexError):
        return await message.reply_text(">**Balas pesan pengguna atau berikan username pengguna.**")
    try:
        user_id = (await client.get_users(target)).id
    except Exception:
        try:
            user_id = int(message.command[1])
        except Exception:
            return await message.reply_text(">**ID pengguna tidak valid.**")
    proses = await message.reply_text(">**Please wait...**")
    bot_list = ["@Sangmata_bot", "@SangMata_beta_bot"]
    babu = userbot.clients[0]
    getbot = random.choice(bot_list)
    try:
        await babu.unblock_user(getbot)
    except Exception:
        pass
    try:
        txt = await babu.send_message(getbot, user_id)
    except Exception as e:
        await proses.edit_text(f"<b>❌ Gagal mengirim ke {getbot}: {e}</b>")
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
            await message.reply_text(f"<b>❌ {getbot} ERROR, Silahkan kirim manual id pengguna ke {''.join(bot_list)}!</b>")
        else:
            await message.reply_text(name.text)

    try:
        user_info = await babu.resolve_peer(getbot)
        await babu.invoke(raw.functions.messages.DeleteHistory(peer=user_info, max_id=0, revoke=True))
    except Exception:
        pass


__MODULE__ = "SangMata"
__HELP__ = """
<blockquote expandable>
<b>🕵️‍♂️ SangMata Tracker</b>

<b>★ /sangmata</b> [on/off] – Enable or disable name change tracking in the group.  
<b>★ /sg</b> [userID/reply] – View user name history.
</blockquote>
"""
