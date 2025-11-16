# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com

from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS, db
from ShrutiMusic.utils.database import (
    get_authuser_names,
    get_cmode,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_maintenance,
    is_nonadmin_chat,
    is_skipmode,
)
from config import SUPPORT_GROUP, adminlist, confirmer
from strings import get_string

from ..formatters import int_to_alpha


def AdminRightsCheck(mystic):
    async def wrapper(client, message):
        # maintenance check
        try:
            maintenance = await is_maintenance()
        except Exception:
            maintenance = True  # if check fails, be conservative

        if maintenance is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=(
                        f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴠɪsɪᴛ "
                        f"<a href={SUPPORT_GROUP}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a> ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ."
                    ),
                    disable_web_page_preview=True,
                )

        # try to delete the invoking message where appropriate
        try:
            await message.delete()
        except Exception:
            pass

        # load language strings safely
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
        except Exception:
            _ = get_string("en")

        # anonymous sender (channel) handling
        if getattr(message, "sender_chat", False):
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʜᴏᴡ ᴛᴏ ғɪx ?",
                            callback_data="AnonymousAdmin",
                        ),
                    ]
                ]
            )
            return await message.reply_text(_["general_3"], reply_markup=upl)

        # ensure message.command exists to avoid IndexError
        cmd_list = getattr(message, "command", []) or []

        # check for cplay mode (commands prefixed with 'c')
        if cmd_list and cmd_list[0] and cmd_list[0][0] == "c":
            chat_id = await get_cmode(message.chat.id)
            if chat_id is None:
                return await message.reply_text(_["setting_7"])
            try:
                await app.get_chat(chat_id)
            except Exception:
                return await message.reply_text(_["cplay_4"])
        else:
            chat_id = message.chat.id

        # check whether chat is active
        if not await is_active_chat(chat_id):
            return await message.reply_text(_["general_5"])

        # non-admin/chat settings handling
        is_non_admin = await is_nonadmin_chat(message.chat.id)
        if not is_non_admin:
            if message.from_user.id not in SUDOERS:
                admins = adminlist.get(message.chat.id)
                if not admins:
                    return await message.reply_text(_["admin_13"])
                else:
                    if message.from_user.id not in admins:
                        if await is_skipmode(message.chat.id):
                            upvote = await get_upvote_count(chat_id)
                            text = (
                                f"<b>ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɴᴇᴇᴅᴇᴅ</b>\n\n"
                                "ʀᴇғʀᴇsʜ ᴀᴅᴍɪɴ ᴄᴀᴄʜᴇ ᴠɪᴀ : /reload\n\n"
                                f"» {upvote} ᴠᴏᴛᴇs ɴᴇᴇᴅᴇᴅ ғᴏʀ ᴘᴇʀғᴏʀᴍɪɴɢ ᴛʜɪs ᴀᴄᴛɪᴏɴ."
                            )

                            command = cmd_list[0] if cmd_list else ""
                            if command and command[0] == "c":
                                command = command[1:]
                            if command == "speed":
                                return await message.reply_text(_["admin_14"])
                            MODE = command.title() if command else "Action"
                            upl = InlineKeyboardMarkup(
                                [
                                    [
                                        InlineKeyboardButton(
                                            text="ᴠᴏᴛᴇ",
                                            callback_data=f"ADMIN  UpVote|{chat_id}_{MODE}",
                                        ),
                                    ]
                                ]
                            )
                            if chat_id not in confirmer:
                                confirmer[chat_id] = {}
                            try:
                                # safe access to db structure
                                vidid = db.get(chat_id, [{}])[0].get("vidid")
                                file = db.get(chat_id, [{}])[0].get("file")
                            except Exception:
                                vidid = None
                                file = None

                            if not vidid or not file:
                                return await message.reply_text(_["admin_14"])

                            senn = await message.reply_text(text, reply_markup=upl)
                            confirmer[chat_id][senn.id] = {"vidid": vidid, "file": file}
                            return
                        else:
                            return await message.reply_text(_["admin_14"])

        # pass language and chat_id to decorated function
        return await mystic(client, message, _, chat_id)

    return wrapper


def AdminActual(mystic):
    async def wrapper(client, message):
        try:
            maintenance = await is_maintenance()
        except Exception:
            maintenance = True

        if maintenance is False:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=(
                        f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴠɪsɪᴛ "
                        f"<a href={SUPPORT_GROUP}>sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ</a> ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ."
                    ),
                    disable_web_page_preview=True,
                )

        try:
            await message.delete()
        except Exception:
            pass

        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
        except Exception:
            _ = get_string("en")

        if getattr(message, "sender_chat", False):
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʜᴏᴡ ᴛᴏ ғɪx ?",
                            callback_data="AnonymousAdmin",
                        ),
                    ]
                ]
            )
            return await message.reply_text(_["general_3"], reply_markup=upl)

        if message.from_user.id not in SUDOERS:
            try:
                member = (await app.get_chat_member(message.chat.id, message.from_user.id)).privileges
            except Exception:
                return
            if not getattr(member, "can_manage_video_chats", False):
                return await message.reply_text(_["general_4"])

        return await mystic(client, message, _)

    return wrapper


def ActualAdminCB(mystic):
    async def wrapper(client, CallbackQuery):
        try:
            maintenance = await is_maintenance()
        except Exception:
            maintenance = True

        if maintenance is False:
            if CallbackQuery.from_user.id not in SUDOERS:
                return await CallbackQuery.answer(
                    f"{app.mention} ɪs ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ, ᴠɪsɪᴛ sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ ғᴏʀ ᴋɴᴏᴡɪɴɢ ᴛʜᴇ ʀᴇᴀsᴏɴ.",
                    show_alert=True,
                )

        try:
            language = await get_lang(CallbackQuery.message.chat.id)
            _ = get_string(language)
        except Exception:
            _ = get_string("en")

        if CallbackQuery.message.chat.type == ChatType.PRIVATE:
            return await mystic(client, CallbackQuery, _)

        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            try:
                a = (await app.get_chat_member(CallbackQuery.message.chat.id, CallbackQuery.from_user.id)).privileges
            except Exception:
                return await CallbackQuery.answer(_["general_4"], show_alert=True)
            if not getattr(a, "can_manage_video_chats", False):
                if CallbackQuery.from_user.id not in SUDOERS:
                    token = await int_to_alpha(CallbackQuery.from_user.id)
                    _check = await get_authuser_names(CallbackQuery.from_user.id)
                    if token not in _check:
                        try:
                            return await CallbackQuery.answer(_["general_4"], show_alert=True)
                        except Exception:
                            return

        return await mystic(client, CallbackQuery, _)

    return wrapper


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots
