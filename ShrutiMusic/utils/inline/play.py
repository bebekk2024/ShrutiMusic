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


import math
from pyrogram.types import InlineKeyboardButton
from ShrutiMusic.utils.formatters import time_to_seconds
from config import BOT_USERNAME, SUPPORT_GROUP, SUPPORT_CHANNEL


def _build_progress_bar(played_sec: int, duration_sec: int, length: int = 14) -> (str, int):
    """
    Build a stylized progress bar with a glowing pointer.
    Returns (bar_string, percent_int).
    """
    if duration_sec <= 0:
        duration_sec = 1
    ratio = max(0.0, min(1.0, played_sec / duration_sec))
    percent = int(ratio * 100)

    filled = int(math.floor(ratio * length))
    # ensure pointer is visible even when progress is 100%
    if filled >= length:
        filled = length - 1

    parts = []
    for i in range(length):
        if i < filled:
            parts.append("▰")  # filled block
        elif i == filled:
            parts.append("🔹")  # pointer
        else:
            parts.append("▱")  # empty block

    bar = "".join(parts)
    return bar, percent


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎧 {_['P_B_1']}",
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=f"🎥 {_['P_B_2']}",
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"✖ {_['CLOSE_BUTTON']}",
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons


def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur) or 1

    bar, percent = _build_progress_bar(played_sec, duration_sec, length=16)

    # compact, elegant display
    top_text = f"⏳ {played}   {bar}   {dur} • {percent}%"

    buttons = [
        [
            InlineKeyboardButton(
                text=top_text,
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(text="⟵", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏯", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="🔁", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="⏹", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP),
            InlineKeyboardButton(text="📢 ᴄʜᴀɴɴᴇʟ", url=SUPPORT_CHANNEL),
        ],
        [InlineKeyboardButton(text=f"✖ {_['CLOSE_BUTTON']}", callback_data="close")],
    ]
    return buttons


def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="⟵", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="⏯", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="🔁", callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text="⏭", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="⏹", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [InlineKeyboardButton(text=f"✖ {_['CLOSE_BUTTON']}", callback_data="close")],
    ]
    return buttons


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎼 {_['P_B_1']}",
                callback_data=f"NandPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=f"🎞 {_['P_B_2']}",
                callback_data=f"NandPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"✖ {_['CLOSE_BUTTON']}",
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🔴 {_['P_B_3']}",
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"✖ {_['CLOSE_BUTTON']}",
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"🎧 {_['P_B_1']}",
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=f"🎥 {_['P_B_2']}",
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⟪",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=f"✖ {_['CLOSE_BUTTON']}",
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="⟫",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
