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


from pyrogram import filters

from ShrutiMusic import YouTube, app
from ShrutiMusic.utils.channelplay import get_channeplayCB
from ShrutiMusic.utils.decorators.language import languageCB
from ShrutiMusic.utils.stream.stream import stream
from config import BANNED_USERS
from ..logging import LOGGER  # gunakan LOGGER jika tersedia di package


@app.on_callback_query(filters.regex("LiveStream") & ~BANNED_USERS)
@languageCB
async def play_live_stream(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    video = True if mode == "v" else None
    user_name = CallbackQuery.from_user.first_name
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass
    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    try:
        details, track_id = await YouTube.track(vidid, True)
    except Exception as e:
        LOGGER(__name__).error(f"Failed to fetch track details for {vidid}: {e}")
        return await mystic.edit_text(_["play_3"])

    # Guard aman ketika metadata tidak lengkap.
    try:
        if not isinstance(details, dict):
            details = details or {}
        # Ambil duration_min bila tersedia, fallback ke duration (detik) lalu ubah ke menit.
        duration_min = details.get("duration_min")
        if duration_min is None:
            # Coba beberapa kemungkinan field lain yang mungkin berisi durasi
            duration = details.get("duration") or details.get("duration_seconds") or details.get("length")
            if duration is not None:
                try:
                    # beberapa extractor mengembalikan string, pastikan ke int detik lalu ke menit
                    duration_int = int(float(duration))
                    duration_min = int(duration_int / 60)
                except Exception:
                    duration_min = 0
            else:
                # Tidak ada metadata durasi sama sekali -> anggap live/unknown
                duration_min = 0

        # Jika duration_min == 0, anggap live atau durasi tidak diketahui -> lanjutkan streaming live
        if duration_min == 0:
            LOGGER(__name__).info(f"Detected live/unknown-duration for vid {vidid} (details keys: {list(details.keys())})")
            ffplay = True if fplay == "f" else None
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    CallbackQuery.message.chat.id,
                    video,
                    streamtype="live",
                    forceplay=ffplay,
                )
            except Exception as e:
                LOGGER(__name__).error(f"Error while starting live stream for {vidid}: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
        else:
            # Jika ada durasi > 0, ini bukan live stream
            return await mystic.edit_text("» ɴᴏᴛ ᴀ ʟɪᴠᴇ sᴛʀᴇᴀᴍ.")
    except Exception as e:
        # Jangan biarkan handler crash karena metadata tak terduga.
        LOGGER(__name__).error(f"Unhandled error when processing track details for {vidid}: {e}")
        # Fallback: anggap live dan coba lanjutkan
        try:
            ffplay = True if fplay == "f" else None
            await stream(
                _,
                mystic,
                user_id,
                details or {},
                chat_id,
                user_name,
                CallbackQuery.message.chat.id,
                video,
                streamtype="live",
                forceplay=ffplay,
            )
        except Exception as e2:
            LOGGER(__name__).error(f"Fallback live stream attempt failed for {vidid}: {e2}")
            ex_type = type(e2).__name__
            err = e2 if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)

    await mystic.delete()


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
