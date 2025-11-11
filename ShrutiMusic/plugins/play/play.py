import random
import string

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall
from pyrogram.errors import RPCError

import config
from ShrutiMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from ShrutiMusic.core.call import Nand
from ShrutiMusic.utils import seconds_to_min, time_to_seconds
from ShrutiMusic.utils.channelplay import get_channeplayCB
from ShrutiMusic.utils.decorators.language import languageCB
from ShrutiMusic.utils.decorators.play import PlayWrapper
from ShrutiMusic.utils.formatters import formats
from ShrutiMusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from ShrutiMusic.utils.logger import play_logs
from ShrutiMusic.utils.stream.stream import stream
from config import BANNED_USERS, lyrical

# PATCH: Tambahkan fungsi universal search
async def universal_track_search(query_or_link):
    apis = [YouTube, Spotify, Apple, Resso]
    for api in apis:
        try:
            details, track_id = await api.track(query_or_link)
            if details:
                print(f"Trek ditemukan di {api.__class__.__name__}")
                return details, track_id
        except Exception as e:
            print(f"Track gagal di {api.__class__.__name__}: {e}")
    print("Trek tidak ditemukan di semua platform.")
    return None, None

async def safe_edit(mystic_obj, fallback_target, text, reply_markup=None):
    try:
        if mystic_obj:
            return await mystic_obj.edit_text(text, reply_markup=reply_markup)
    except RPCError as e:
        try:
            if hasattr(fallback_target, "reply_text"):
                return await fallback_target.reply_text(text, reply_markup=reply_markup)
            else:
                return await app.send_message(chat_id=fallback_target, text=text, reply_markup=reply_markup)
        except Exception:
            return None
    except Exception:
        try:
            if hasattr(fallback_target, "reply_text"):
                return await fallback_target.reply_text(text, reply_markup=reply_markup)
            else:
                return await app.send_message(chat_id=fallback_target, text=text, reply_markup=reply_markup)
        except Exception:
            return None

@app.on_message(
    filters.command([
        "play", "vplay", "cplay", "cvplay",
        "playforce", "vplayforce", "cplayforce", "cvplayforce"
    ])
    & filters.group
    & ~BANNED_USERS
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )
    if audio_telegram:
        if audio_telegram.file_size > 104857600:
            return await safe_edit(mystic, message, _["play_5"])
        duration_min = seconds_to_min(audio_telegram.duration)
        if (audio_telegram.duration) > config.DURATION_LIMIT:
            return await safe_edit(
                mystic, message, _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
        file_path = await Telegram.get_filepath(audio=audio_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(audio_telegram, audio=True)
            dur = await Telegram.get_duration(audio_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await safe_edit(mystic, message, err)
            try:
                return await mystic.delete()
            except Exception:
                return None
        return
    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await safe_edit(
                        mystic, message, _["play_7"].format(f"{' | '.join(formats)}")
                    )
            except:
                return await safe_edit(
                    mystic, message, _["play_7"].format(f"{' | '.join(formats)}")
                )
        if video_telegram.file_size > config.TG_VIDEO_FILESIZE_LIMIT:
            return await safe_edit(mystic, message, _["play_8"])
        file_path = await Telegram.get_filepath(video=video_telegram)
        if await Telegram.download(_, message, mystic, file_path):
            message_link = await Telegram.get_link(message)
            file_name = await Telegram.get_filename(video_telegram)
            dur = await Telegram.get_duration(video_telegram, file_path)
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
            }
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await safe_edit(mystic, message, err)
            try:
                return await mystic.delete()
            except Exception:
                return None
        return
    elif url:
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]
            else:
                try:
                    details, track_id = await YouTube.track(url)
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "youtube"
                img = details.get("thumb", config.PLAYLIST_IMG_URL)
                cap = _["play_10"].format(
                    details.get("title", "Unknown"),
                    details.get("duration_min", "Unknown"),
                )
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await safe_edit(
                    mystic, message, "» sᴘᴏᴛɪғʏ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n\nᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
                )
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "youtube"
                img = details.get("thumb", config.SPOTIFY_PLAYLIST_IMG_URL)
                cap = _["play_10"].format(details.get("title", "Unknown"), details.get("duration_min", "Unknown"))
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_11"].format(message.from_user.first_name)
            else:
                return await safe_edit(mystic, message, _["play_15"])
        elif await Apple.valid(url):
            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "youtube"
                img = details.get("thumb", config.PLAYLIST_IMG_URL)
                cap = _["play_10"].format(details.get("title", "Unknown"), details.get("duration_min", "Unknown"))
            elif "playlist" in url:
                spotify = True
                try:
                    details, plist_id = await Apple.playlist(url)
                except:
                    return await safe_edit(mystic, message, _["play_3"])
                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_12"].format(app.mention, message.from_user.mention)
                img = url
            else:
                return await safe_edit(mystic, message, _["play_3"])
        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)
            except:
                return await safe_edit(mystic, message, _["play_3"])
            streamtype = "youtube"
            img = details.get("thumb", config.PLAYLIST_IMG_URL)
            cap = _["play_10"].format(details.get("title", "Unknown"), details.get("duration_min", "Unknown"))
        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
            except:
                return await safe_edit(mystic, message, _["play_3"])
            duration_sec = details.get("duration_sec", 0)
            if duration_sec > config.DURATION_LIMIT:
                return await safe_edit(
                    mystic, message, _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                )
            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await safe_edit(mystic, message, err)
            try:
                return await mystic.delete()
            except Exception:
                return None
        else:
            try:
                await Nand.stream_call(url)
            except NoActiveGroupCall:
                await safe_edit(mystic, message, _["black_9"])
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=_["play_17"],
                )
            except Exception as e:
                print(f"Error: {e}")
                return await safe_edit(mystic, message, _["general_2"].format(type(e).__name__))
            await safe_edit(mystic, message, _["str_2"])
            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )
            except Exception as e:
                print(f"Error: {e}")
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await safe_edit(mystic, message, err)
            return await play_logs(message, streamtype="M3u8 or Index Link")
    else:
        # PATCH: Bagian ini diubah menjadi universal query
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)
            return await safe_edit(
                mystic, message, _["play_18"], reply_markup=InlineKeyboardMarkup(buttons)
            )
        slider = True
        query = message.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")
        try:
            details, track_id = await universal_track_search(query)
            if not details:
                return await safe_edit(mystic, message, _["play_3"])  # PATCH: Fallback semua platform
            streamtype = "universal"
        except Exception as e:
            print(f"Universal search error: {e}")
            return await safe_edit(mystic, message, _["play_3"])
    # Bagian berikut tetap sesuai logika asli play.py
    if str(playmode) == "Direct":
        if not plist_type:
            if details.get("duration_min"):
                duration_sec = time_to_seconds(details.get("duration_min"))
                if duration_sec > config.DURATION_LIMIT:
                    return await safe_edit(
                        mystic, message, _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                    )
            else:
                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                return await safe_edit(
                    mystic, message, _["play_13"], reply_markup=InlineKeyboardMarkup(buttons)
                )
        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )
        except Exception as e:
            print(f"Error: {e}")
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await safe_edit(mystic, message, err)
        try:
            await mystic.delete()
        except Exception:
            pass
        return await play_logs(message, streamtype=streamtype)
    else:
        if plist_type:
            ran_hash = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            try:
                await mystic.delete()
            except Exception:
                pass
            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return await play_logs(message, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                try:
                    await mystic.delete()
                except Exception:
                    pass
                await message.reply_photo(
                    photo=details.get("thumb", config.PLAYLIST_IMG_URL),
                    caption=_["play_10"].format(
                        details.get("title", "Unknown").title(),
                        details.get("duration_min", "Unknown"),
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"Searched on Youtube")
            else:
                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                try:
                    await mystic.delete()
                except Exception:
                    pass
                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return await play_logs(message, streamtype=f"URL Searched Inline")

# ... kode selebihnya tetap SAMA seperti file aslinya ...

# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================

# ❤️ Love From ShrutiBots  
