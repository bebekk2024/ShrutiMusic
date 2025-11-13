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


from typing import Union, Any, List

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Aesthetic constants (kosmetik saja, tidak mengubah callback_data)
_EMOJI_PLAY = "🎵"
_EMOJI_TIMER = "⌛"
_EMOJI_CLOSE = "❌"
_EMOJI_BACK = "◀️"
_SEPARATOR = "  "


def _format_time(t: Union[None, bool, int, str]) -> str:
    """
    Format waktu dari detik (int) menjadi H:MM:SS atau MM:SS.
    Jika nilai falsy atau tidak valid, kembalikan "Unknown".
    """
    if t in (None, False, "Unknown"):
        return "Unknown"
    try:
        if isinstance(t, str) and ":" in t:
            return t
        seconds = int(t)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except Exception:
        return str(t)


def _progress_bar(played: Union[int, bool, None], dur: Union[int, bool, None], length: int = 12) -> str:
    """
    Buat progress-bar teks menggunakan blok unicode.
    Jika dur tidak valid, kembalikan garis minimal.
    """
    if not played or not dur or dur in (False, "Unknown"):
        return "—" * (length // 2)
    try:
        p = float(played) / float(dur)
        p = max(0.0, min(1.0, p))
        filled = int(round(p * length))
        empty = length - filled
        bar = "▰" * filled + "▱" * empty
        percent = int(round(p * 100))
        return f"{bar} {percent}%"
    except Exception:
        return "—" * (length // 2)


def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
) -> InlineKeyboardMarkup:
    """
    Menghasilkan InlineKeyboardMarkup untuk daftar antrian:
    - Bila DURATION == "Unknown" tampilkan tombol GetQueued + Close (sama seperti versi awal)
    - Bila dur tersedia tampilkan progress bar (tombol yang memanggil GetTimer) + tombol lain
    Perhatikan: callback_data untuk GetQueued masih menggunakan format semula
    f"GetQueued {CPLAY}|{videoid}" agar kompatibel dengan handler yang ada.
    """
    # tetap gunakan format waktu / progress yang estetis
    played_str = _format_time(played)
    dur_str = _format_time(dur)
    bar = _progress_bar(played, dur, length=12)

    if DURATION == "Unknown" or dur in (None, False, "Unknown"):
        # dur tidak diketahui -> sama seperti implementasi awal, satu baris (GetQueued, Close)
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"{_EMOJI_PLAY}{_SEPARATOR}{_['QU_B_1']}",
                    callback_data=f"GetQueued {CPLAY}|{videoid}",
                ),
                InlineKeyboardButton(
                    text=f"{_EMOJI_CLOSE}{_SEPARATOR}{_['CLOSE_BUTTON']}",
                    callback_data="close",
                ),
            ]
        ]
    else:
        # dur diketahui -> tampilkan progress bar (memanggil GetTimer) di bar atas,
        # lalu bar waktu (played / dur) sebagai teks (tidak memanggil handler lain),
        # lalu tombol utama (GetQueued) + Close.
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"{_EMOJI_TIMER}{_SEPARATOR}{bar}",
                    callback_data="GetTimer",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⏺ {_SEPARATOR}{played_str}",
                    callback_data="GetTimer",
                ),
                InlineKeyboardButton(
                    text=f"⏹ {_SEPARATOR}{dur_str}",
                    callback_data="GetTimer",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"{_EMOJI_PLAY}{_SEPARATOR}{_['QU_B_1']}",
                    callback_data=f"GetQueued {CPLAY}|{videoid}",
                ),
                InlineKeyboardButton(
                    text=f"{_EMOJI_CLOSE}{_SEPARATOR}{_['CLOSE_BUTTON']}",
                    callback_data="close",
                ),
            ],
        ]

    return InlineKeyboardMarkup(buttons)


def queue_back_markup(_, CPLAY):
    """
    Tombol 'kembali' — kembalikan InlineKeyboardMarkup (seperti semula).
    """
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=f"{_EMOJI_BACK}{_SEPARATOR}{_['BACK_BUTTON']}",
                    callback_data=f"queue_back_timer {CPLAY}",
                ),
                InlineKeyboardButton(
                    text=f"{_EMOJI_CLOSE}{_SEPARATOR}{_['CLOSE_BUTTON']}",
                    callback_data="close",
                ),
            ]
        ]
    )
    return upl


def aq_markup(_, chat_id):
    """
    Kompatibilitas: kembalikan 'buttons' (list of list of InlineKeyboardButton)
    sama seperti versi original agar pemanggil lama tidak rusak.
    Jika caller membutuhkan InlineKeyboardMarkup, tinggal wrap dengan InlineKeyboardMarkup(buttons).
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
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
