import asyncio
import time
from logging import getLogger
from time import time

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFont
from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated

from ShrutiMusic import app
from ShrutiMusic.utils.database import get_assistant
from config import OWNER_ID

LOGGER = getLogger(__name__)

class AWelDatabase:
    def __init__(self):
        self.data = {}

    async def find_one(self, chat_id):
        return chat_id in self.data

    async def add_wlcm(self, chat_id):
        if chat_id not in self.data:
            self.data[chat_id] = {"state": "on"}

    async def rm_wlcm(self, chat_id):
        if chat_id in self.data:
            del self.data[chat_id]

wlcm = AWelDatabase()

user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

@app.on_message(filters.command("awelcome") & ~filters.private)
async def auto_state(_, message):
    user_id = message.from_user.id
    current_time = time()
    last_message_time = user_last_message_time.get(user_id, 0)

    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    usage = "ᴜsᴀɢᴇ:\n⦿ /awelcome [on|off]"
    if len(message.command) == 1:
        return await message.reply_text(usage)
    chat_id = message.chat.id
    user = await app.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in (
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ):
        A = await wlcm.find_one(chat_id)
        state = message.text.split(None, 1)[1].strip().lower()
        if state == "off":
            if A:
                await message.reply_text(
                    "ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ᴀʟʀᴇᴀᴅʏ ᴅɪsᴀʙʟᴇᴅ !"
                )
            else:
                await wlcm.add_wlcm(chat_id)
                await message.reply_text(
                    f"ᴅɪsᴀʙʟᴇᴅ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪɴ {message.chat.title} ʙʏ ᴀssɪsᴛᴀɴᴛ"
                )
        elif state == "on":
            if not A:
                await message.reply_text("ᴇɴᴀʙʟᴇᴅ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ.")
            else:
                await wlcm.rm_wlcm(chat_id)
                await message.reply_text(
                    f"ᴇɴᴀʙʟᴇᴅ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ ɪɴ  {message.chat.title}"
                )
        else:
            await message.reply_text(usage)
    else:
        await message.reply(
            "sᴏʀʀʏ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴇɴᴀʙʟᴇ ᴀssɪsᴛᴀɴᴛ ᴡᴇʟᴄᴏᴍᴇ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ!"
        )

@app.on_chat_member_updated(filters.group, group=5)
async def greet_new_members(_, member: ChatMemberUpdated):
    try:
        chat_id = member.chat.id
        chat_name = (await app.get_chat(chat_id)).title
        userbot = await get_assistant(chat_id)
        count = await app.get_chat_members_count(chat_id)
        A = await wlcm.find_one(chat_id)
        if A:
            return

        user = (
            member.new_chat_member.user if member.new_chat_member else member.from_user
        )

        # ONLY welcome if the joining user is OWNER
        if member.new_chat_member and not member.old_chat_member and user.id == OWNER_ID:
            owner_welcome_text = f"""
<blockquote expandable>
👋 <b>Selamat Datang Owner!</b> 👋
Halo {user.mention}, kamu adalah pemilik bot music ini!
🆔 <b>ID:</b> {user.id}
🌐 <b>Username:</b> @{user.username}
👥 <b>Total member:</b> {count}
🏠 <b>Grup:</b> {chat_name}

<blockquote><b><b>Terima kasih sudah hadir, Owner!</b></a></b></blockquote>
</blockquote>
"""
            await asyncio.sleep(3)
            await userbot.send_message(chat_id, text=owner_welcome_text)
        # Do nothing for other members (no welcome)
    except Exception:
        return
