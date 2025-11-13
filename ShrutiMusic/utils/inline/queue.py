from typing import Union
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Aesthetic buttons
Q_SHOW_QUEUE = "📜 Daftar Putar"
Q_PROGRESS = "⏳ {}/{}"
Q_CLOSE = "❌ Tutup"
Q_BACK = "🔙 Kembali"

def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    not_dur = [
        [
            InlineKeyboardButton(
                text=Q_SHOW_QUEUE,
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text=Q_CLOSE,
                callback_data="close",
            ),
        ]
    ]
    dur = [
        [
            InlineKeyboardButton(
                text=Q_PROGRESS.format(played, dur),
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text=Q_SHOW_QUEUE,
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text=Q_CLOSE,
                callback_data="close",
            ),
        ],
    ]
    upl = InlineKeyboardMarkup(not_dur if DURATION == "Unknown" else dur)
    return upl

def queue_back_markup(_, CPLAY):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=Q_BACK,
                    callback_data=f"queue_back_timer {CPLAY}",
                ),
                InlineKeyboardButton(
                    text=Q_CLOSE,
                    callback_data="close",
                ),
            ]
        ]
    )
    return upl

def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(
                text=Q_CLOSE,
                callback_data="close",
            ),
        ],
    ]
    return buttons

# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ❤️ Love From ShrutiBots 
