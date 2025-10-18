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


from datetime import datetime
import logging

from pyrogram import filters
from pyrogram.errors import RPCError
from pyrogram.types import Message

from ShrutiMusic import app
from ShrutiMusic.core.call import Nand
from ShrutiMusic.utils import bot_sys_stats
from ShrutiMusic.utils.decorators.language import language
from ShrutiMusic.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL

logger = logging.getLogger(__name__)


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    """
    Ping command:
    - Safely handles empty/invalid PING_IMG_URL (fallback to text)
    - Catches ValueError/TypeError when file id/url is invalid
    - Catches RPCError for API issues
    - Chooses edit_caption for photo responses, edit_text for text responses
    """
    start = datetime.now()
    photo = PING_IMG_URL if PING_IMG_URL else None
    sent_with_photo = False

    # Try to send the initial response as a photo if configured.
    try:
        if photo:
            response = await message.reply_photo(
                photo=photo,
                caption=_["ping_1"].format(app.mention),
            )
            sent_with_photo = True
        else:
            # No image configured, fallback to a simple text reply
            response = await message.reply_text(_["ping_1"].format(app.mention))
            sent_with_photo = False
    except (ValueError, TypeError) as e:
        # This happens when photo is "" or invalid file id/URL
        logger.warning("ping_com: invalid photo (%r): %s", photo, e)
        response = await message.reply_text(_["ping_1"].format(app.mention))
        sent_with_photo = False
    except RPCError as e:
        # API-related errors (rate limits, file not found on Telegram servers, etc.)
        logger.exception("ping_com: RPCError while sending initial ping response: %s", e)
        # Fallback to a minimal text reply so we can still edit with stats later
        try:
            response = await message.reply_text(_["ping_1"].format(app.mention))
        except Exception:
            # If even this fails, log and stop
            logger.exception("ping_com: failed to send any reply for ping command")
            return
        sent_with_photo = False

    # Gather stats
    try:
        pytgping = await Nand.ping()
    except Exception as e:
        logger.exception("ping_com: error getting pytg ping: %s", e)
        pytgping = "N/A"

    try:
        UP, CPU, RAM, DISK = await bot_sys_stats()
    except Exception as e:
        logger.exception("ping_com: error getting system stats: %s", e)
        UP, CPU, RAM, DISK = "N/A", "N/A", "N/A", "N/A"

    resp = (datetime.now() - start).microseconds / 1000

    # Prepare final message text
    final_text = _["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping)

    # Edit the previous response appropriately depending on whether it was a photo or text reply
    try:
        if sent_with_photo:
            # For photo messages, edit_caption updates the caption
            await response.edit_caption(final_text, reply_markup=supp_markup(_))
        else:
            await response.edit_text(final_text, reply_markup=supp_markup(_))
    except RPCError as e:
        logger.exception("ping_com: RPCError while editing ping response: %s", e)
        # Try a safe fallback: send a new text message with the final info
        try:
            await message.reply_text(final_text, reply_markup=supp_markup(_))
        except Exception:
            logger.exception("ping_com: failed to send fallback final ping message")
    except Exception as e:
        logger.exception("ping_com: unexpected error while editing ping response: %s", e)
        try:
            await message.reply_text(final_text, reply_markup=supp_markup(_))
        except Exception:
            logger.exception("ping_com: failed to send fallback final ping message")


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
