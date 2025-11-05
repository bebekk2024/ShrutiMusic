from pyrogram import filters
from pyrogram.types import Message
import config
from ShrutiMusic import app
import asyncio

OWNER_ID = getattr(config, "OWNER_ID", None)
ALLOWED = [OWNER_ID] + (getattr(config, "SUDO_USERS", []) or [])

@app.on_message(filters.command("assist_check") & filters.user(ALLOWED))
async def assist_check(_, message: Message):
    """
    Usage:
      /assist_check              -> show general assistant state
      /assist_check <chat_id>    -> show state for that chat id
    """
    parts = message.text.split()
    chat = int(parts[1]) if len(parts) > 1 else None

    out = []
    out.append("🔧 Assist Check\n")

    # 1) userbot and get_userbot
    try:
        from ShrutiMusic import userbot, get_userbot
        try:
            gb = get_userbot()
        except Exception as e:
            gb = f"<get_userbot() error: {e}>"
        out.append(f"userbot.one: {getattr(userbot, 'one', None)}")
        out.append(f"get_userbot(): {gb}")
    except Exception as e:
        out.append(f"userbot/get_userbot: error: {e}")

    # 2) assistantdict keys
    try:
        from ShrutiMusic.utils import database as dbmod
        out.append(f"assistantdict keys sample: {list(dbmod.assistantdict.keys())[:20]}")
    except Exception as e:
        out.append(f"assistantdict: error: {e}")

    # 3) assistants list from core.userbot
    try:
        mod = __import__("ShrutiMusic.core.userbot", fromlist=["assistants"])
        out.append(f"assistants: {getattr(mod, 'assistants', None)}")
    except Exception as e:
        out.append(f"assistants read error: {e}")

    # 4) optional: check assdb entry for provided chat id
    if chat:
        try:
            rec = await dbmod.assdb.find_one({"chat_id": chat})
            out.append(f"assdb entry for {chat}: {rec}")
            out.append(f"assistantdict[{chat}] -> {dbmod.assistantdict.get(chat)}")
            try:
                # show what set_calls_assistant returns
                from ShrutiMusic.utils.database import set_calls_assistant, get_assistant
                asn = await set_calls_assistant(chat)
                got = await get_assistant(chat)
                out.append(f"set_calls_assistant(chat) returned: {asn}")
                out.append(f"get_assistant(chat) returned type: {type(got)}")
            except Exception as e:
                out.append(f"set/get assistant call failed: {e}")
        except Exception as e:
            out.append(f"assdb lookup failed: {e}")

    # send as one message (avoid very long output)
    text = "\n".join(out)
    await message.reply_text(text, quote=True)
