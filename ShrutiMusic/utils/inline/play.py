import math
from pyrogram.types import InlineKeyboardButton
from ShrutiMusic.utils.formatters import time_to_seconds
from config import BOT_USERNAME, SUPPORT_GROUP, SUPPORT_CHANNEL

# Aesthetic button texts
P_AUDIO = "🎼 Audio"
P_VIDEO = "🎬 Video"
P_CLOSE = "✖️ Tutup"
P_LIVE = "🔴 Live Stream"
P_SUPPORT = "💬 Support"
P_CHANNEL = "📢 Channel"
P_RESUME = "▶️ Lanjut"
P_PAUSE = "⏸ Jeda"
P_REPLAY = "🔄 Ulang"
P_SKIP = "⏭️ Lewati"
P_STOP = "⏹️ Stop"

def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=P_AUDIO,
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=P_VIDEO,
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=P_CLOSE,
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]
    return buttons

def stream_markup_timer(_, chat_id, played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec > 0 else 0
    # Animated progress bar aesthetic
    bars = [
        "▁▁▁▁▁▁▁▁▁▁",  # 0%
        "▃▁▁▁▁▁▁▁▁▁",  # 10%
        "▃▄▁▁▁▁▁▁▁▁",  # 20%
        "▃▄▅▁▁▁▁▁▁▁",  # 30%
        "▃▄▅▆▁▁▁▁▁▁",  # 40%
        "▃▄▅▆▇▁▁▁▁▁",  # 50%
        "▃▄▅▆▇█▁▁▁▁",  # 60%
        "▃▄▅▆▇█▉▁▁▁",  # 70%
        "▃▄▅▆▇█▉▊▁▁",  # 80%
        "▃▄▅▆▇█▉▊▋▁",  # 90%
        "▃▄▅▆▇█▉▊▋▌",  # 100%
    ]
    idx = min(len(bars)-1, int(percentage // 10))
    bar = bars[idx]
    buttons = [
        [
            InlineKeyboardButton(
                text=f"⏳ {played} {bar} {dur}",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(text=P_RESUME, callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text=P_PAUSE, callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text=P_REPLAY, callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text=P_SKIP, callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text=P_STOP, callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(text=P_SUPPORT, url=SUPPORT_GROUP),
            InlineKeyboardButton(text=P_CHANNEL, url=SUPPORT_CHANNEL),
        ],
        [InlineKeyboardButton(text=P_CLOSE, callback_data="close")],
    ]
    return buttons

def stream_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text=P_RESUME, callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text=P_PAUSE, callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text=P_REPLAY, callback_data=f"ADMIN Replay|{chat_id}"),
            InlineKeyboardButton(text=P_SKIP, callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text=P_STOP, callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [InlineKeyboardButton(text=P_CLOSE, callback_data="close")],
    ]
    return buttons

def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=P_AUDIO,
                callback_data=f"NandPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=P_VIDEO,
                callback_data=f"NandPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=P_CLOSE,
                callback_data=f"forceclose {videoid}|{user_id}",
            ),
        ],
    ]
    return buttons

def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=P_LIVE,
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=P_CLOSE,
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
                text=P_AUDIO,
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=P_VIDEO,
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
            InlineKeyboardButton(
                text=P_CLOSE,
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}",
            ),
        ],
    ]
    return buttons

# 🎵 Aesthetic Caption Example 🎵
def build_track_caption(details, track_id=None):
    title = details.get("title", "Unknown")
    duration = details.get("duration_min", "??")
    uploader = details.get("uploader") or details.get("artist") or "??"
    link = details.get("link", None)
    yt_id = track_id or details.get("vidid", None)
    cap = (
        "<b>✨ Now Playing! ✨</b>\n"
        "╭─────────────⩺\n"
        f"🎶 <b>Judul:</b> <i>{title}</i>\n"
        f"⏱️ <b>Durasi:</b> <code>{duration} menit</code>\n"
        f"👤 <b>Oleh:</b> <code>{uploader}</code>\n"
    )
    if link:
        cap += f"🔗 <b>Link:</b> <a href='{link}'>Play</a>\n"
    if yt_id:
        cap += f"🆔 <b>ID Track:</b> <code>{yt_id}</code>\n"
    cap += "╰────────────⩺\n"
    cap += "<i>Selamat menikmati musiknya! 🎧</i>"
    return cap

# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ❤️ Love From ShrutiBots 
