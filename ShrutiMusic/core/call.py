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


import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded

import config
from ShrutiMusic import LOGGER, YouTube, app
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from ShrutiMusic.utils.exceptions import AssistantErr
from ShrutiMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from ShrutiMusic.utils.inline.play import stream_markup
from ShrutiMusic.utils.stream.autoclear import auto_clean
from ShrutiMusic.utils.thumbnails import gen_thumb
from strings import get_string

autoend = {}
counter = {}


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="NandAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=100,
        )
        self.userbot2 = Client(
            name="NandAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(
            self.userbot2,
            cache_duration=100,
        )
        self.userbot3 = Client(
            name="NandAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(
            self.userbot3,
            cache_duration=100,
        )
        self.userbot4 = Client(
            name="NandAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(
            self.userbot4,
            cache_duration=100,
        )
        self.userbot5 = Client(
            name="NandAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(
            self.userbot5,
            cache_duration=100,
        )

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            if config.STRING1:
                await self.one.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING2:
                await self.two.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING3:
                await self.three.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING4:
                await self.four.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING5:
                await self.five.leave_group_call(chat_id)
        except:
            pass
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
        await assistant.change_stream(
            chat_id,
            stream,
        )

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        await assistant.join_group_call(
            config.LOG_GROUP_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOG_GROUP_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = (
                AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
                if video
                else AudioPiped(link, audio_parameters=HighQualityAudio())
            )
        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def stream_end_handler1(self, client, update: Update):
        """
        Defensive wrapper for stream end events so exceptions don't become "Task exception was never retrieved".
        This method logs any unexpected errors while delegating to change_stream.
        """
        try:
            # update.chat_id is expected; fallback to getattr for safety
            chat_id = getattr(update, "chat_id", None)
            if chat_id is None:
                LOGGER.debug("stream_end_handler1: update.chat_id is None, nothing to do. update=%r", update)
                return
            await self.change_stream(client, chat_id)
        except Exception as e:
            LOGGER.exception(
                "Unhandled exception in stream_end_handler1 for chat %s: %s",
                getattr(update, "chat_id", None),
                e,
            )

    async def change_stream(self, client, chat_id):
        """
        Robust change_stream implementation:
        - Validates `check` and `queued`.
        - If queued is missing/None or malformed, it will skip the bad entry and attempt to continue.
        - Logs helpful diagnostics instead of letting TypeError / others bubble uncaught.
        """
        try:
            check = db.get(chat_id)
            if not check:
                LOGGER.debug(
                    "change_stream: no queue found for chat %s, attempting clear and leave.", chat_id
                )
                try:
                    await _clear_(chat_id)
                    await client.leave_group_call(chat_id)
                except Exception:
                    LOGGER.debug(
                        "change_stream: leave_group_call failed for chat %s (may already be left).", chat_id
                    )
                return

            popped = None
            try:
                loop = await get_loop(chat_id)
            except Exception:
                LOGGER.debug(
                    "change_stream: could not fetch loop for chat %s, defaulting to 0.", chat_id
                )
                loop = 0

            # Pop or decrease loop accordingly
            try:
                if loop == 0:
                    # Defensive: ensure check is a list and non-empty
                    if isinstance(check, list) and len(check) > 0:
                        popped = check.pop(0)
                    else:
                        LOGGER.warning(
                            "change_stream: expected non-empty list for check for chat %s, got: %r",
                            chat_id,
                            check,
                        )
                        await _clear_(chat_id)
                        try:
                            await client.leave_group_call(chat_id)
                        except Exception:
                            pass
                        return
                else:
                    # decrement loop count
                    loop = loop - 1
                    await set_loop(chat_id, loop)
            except Exception as e:
                LOGGER.exception(
                    "change_stream: error while popping or adjusting loop for chat %s: %s", chat_id, e
                )
                # Try a safe clear and leave
                try:
                    await _clear_(chat_id)
                    await client.leave_group_call(chat_id)
                except Exception:
                    LOGGER.debug(
                        "change_stream: leave_group_call failed during exception handling for chat %s.",
                        chat_id,
                    )
                return

            # Clean up popped (if any)
            try:
                if popped:
                    await auto_clean(popped)
            except Exception:
                LOGGER.debug(
                    "change_stream: auto_clean failed for popped item in chat %s.", chat_id
                )

            # If queue is empty after pop, clear and leave
            if not check:
                LOGGER.debug(
                    "change_stream: queue empty after pop for chat %s, clearing and leaving.", chat_id
                )
                try:
                    await _clear_(chat_id)
                    await client.leave_group_call(chat_id)
                except Exception:
                    LOGGER.debug(
                        "change_stream: leave_group_call failed on empty queue for chat %s.", chat_id
                    )
                return

            # Safely fetch queued field
            first = check[0] if isinstance(check, list) and len(check) > 0 else None
            queued = None
            if isinstance(first, dict):
                queued = first.get("file")
            else:
                LOGGER.warning(
                    "change_stream: unexpected queue item type for chat %s: %r", chat_id, first
                )

            # If queued is missing or not a string, skip this entry and try next
            if not queued or not isinstance(queued, str):
                LOGGER.warning(
                    "change_stream: queued is invalid for chat %s: %r. Removing this entry and continuing.",
                    chat_id,
                    queued,
                )
                # Remove the bad entry and attempt to continue
                try:
                    if isinstance(check, list) and len(check) > 0:
                        bad = check.pop(0)
                        try:
                            await auto_clean(bad)
                        except Exception:
                            LOGGER.debug(
                                "change_stream: auto_clean failed for removed invalid item in chat %s", chat_id
                            )
                except Exception as e:
                    LOGGER.exception(
                        "change_stream: failed to pop invalid queued item for chat %s: %s", chat_id, e
                    )
                # If nothing remains, clear and leave, else recurse to handle next entry
                if not check:
                    LOGGER.debug(
                        "change_stream: queue empty after removing invalid item for chat %s, clearing and leaving.",
                        chat_id,
                    )
                    try:
                        await _clear_(chat_id)
                        await client.leave_group_call(chat_id)
                    except Exception:
                        pass
                    return
                # Recurse to process next entry (bounded because we removed one element)
                await self.change_stream(client, chat_id)
                return

            # At this point queued is a valid string; continue original logic
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0].get("title") or "").title()
            user = check[0].get("by")
            original_chat_id = check[0].get("chat_id")
            streamtype = check[0].get("streamtype")
            videoid = check[0].get("vidid")
            # reset played
            try:
                db[chat_id][0]["played"] = 0
            except Exception:
                LOGGER.debug("change_stream: failed to reset played for chat %s", chat_id)

            exis = (check[0]).get("old_dur")
            if exis:
                try:
                    db[chat_id][0]["dur"] = exis
                    db[chat_id][0]["seconds"] = check[0].get("old_second")
                    db[chat_id][0]["speed_path"] = None
                    db[chat_id][0]["speed"] = 1.0
                except Exception:
                    LOGGER.debug("change_stream: failed to restore old_dur for chat %s", chat_id)

            video = True if str(streamtype) == "video" else False

            # Safely check for live/vid/index strings inside queued
            try:
                if "live_" in queued:
                    n, link = await YouTube.video(videoid, True)
                    if n == 0:
                        return await app.send_message(original_chat_id, text=_["call_6"])
                    if video:
                        stream = AudioVideoPiped(
                            link,
                            audio_parameters=HighQualityAudio(),
                            video_parameters=MediumQualityVideo(),
                        )
                    else:
                        stream = AudioPiped(link, audio_parameters=HighQualityAudio())
                    try:
                        await client.change_stream(chat_id, stream)
                    except Exception as e:
                        LOGGER.exception(
                            "change_stream: change_stream failed for live_ link in chat %s: %s",
                            chat_id,
                            e,
                        )
                        return await app.send_message(original_chat_id, text=_["call_6"])
                    img = await gen_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0].get("dur"),
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                elif "vid_" in queued:
                    mystic = await app.send_message(original_chat_id, _["call_7"])
                    try:
                        file_path, direct = await YouTube.download(
                            videoid,
                            mystic,
                            videoid=True,
                            video=True if str(streamtype) == "video" else False,
                        )
                    except Exception as e:
                        LOGGER.exception(
                            "change_stream: YouTube.download failed for vid_ in chat %s: %s",
                            chat_id,
                            e,
                        )
                        return await mystic.edit_text(
                            _["call_6"], disable_web_page_preview=True
                        )
                    if video:
                        stream = AudioVideoPiped(
                            file_path,
                            audio_parameters=HighQualityAudio(),
                            video_parameters=MediumQualityVideo(),
                        )
                    else:
                        stream = AudioPiped(file_path, audio_parameters=HighQualityAudio())
                    try:
                        await client.change_stream(chat_id, stream)
                    except Exception as e:
                        LOGGER.exception(
                            "change_stream: change_stream failed for vid_ file in chat %s: %s",
                            chat_id,
                            e,
                        )
                        return await app.send_message(original_chat_id, text=_["call_6"])
                    img = await gen_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    try:
                        await mystic.delete()
                    except Exception:
                        LOGGER.debug(
                            "change_stream: unable to delete mystic message in chat %s", original_chat_id
                        )
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0].get("dur"),
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

                elif "index_" in queued:
                    stream = (
                        AudioVideoPiped(
                            videoid,
                            audio_parameters=HighQualityAudio(),
                            video_parameters=MediumQualityVideo(),
                        )
                        if str(streamtype) == "video"
                        else AudioPiped(videoid, audio_parameters=HighQualityAudio())
                    )
                    try:
                        await client.change_stream(chat_id, stream)
                    except Exception as e:
                        LOGGER.exception(
                            "change_stream: change_stream failed for index_ in chat %s: %s",
                            chat_id,
                            e,
                        )
                        return await app.send_message(original_chat_id, text=_["call_6"])
                    button = stream_markup(_, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.STREAM_IMG_URL,
                        caption=_["stream_2"].format(user),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                else:
                    # Normal URL/file stream
                    if video:
                        stream = AudioVideoPiped(
                            queued,
                            audio_parameters=HighQualityAudio(),
                            video_parameters=MediumQualityVideo(),
                        )
                    else:
                        stream = AudioPiped(queued, audio_parameters=HighQualityAudio())
                    try:
                        await client.change_stream(chat_id, stream)
                    except Exception as e:
                        LOGGER.exception(
                            "change_stream: change_stream failed for queued URL in chat %s: %s",
                            chat_id,
                            e,
                        )
                        return await app.send_message(original_chat_id, text=_["call_6"])

                    if videoid == "telegram":
                        button = stream_markup(_, chat_id)
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=config.TELEGRAM_AUDIO_URL
                            if str(streamtype) == "audio"
                            else config.TELEGRAM_VIDEO_URL,
                            caption=_["stream_1"].format(
                                config.SUPPORT_GROUP, title[:23], check[0].get("dur"), user
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                    elif videoid == "soundcloud":
                        button = stream_markup(_, chat_id)
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=config.SOUNCLOUD_IMG_URL,
                            caption=_["stream_1"].format(
                                config.SUPPORT_GROUP, title[:23], check[0].get("dur"), user
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                    else:
                        img = await gen_thumb(videoid)
                        button = stream_markup(_, chat_id)
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(
                                f"https://t.me/{app.username}?start=info_{videoid}",
                                title[:23],
                                check[0].get("dur"),
                                user,
                            ),
                            reply_markup=InlineKeyboardMarkup(button),
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"

        except Exception as e:
            # Catch-all to avoid unhandled exceptions bubbling out of the event loop
            LOGGER.exception("change_stream: unexpected error for chat %s: %s", chat_id, e)
            try:
                await _clear_(chat_id)
                await client.leave_group_call(chat_id)
            except Exception:
                LOGGER.debug(
                    "change_stream: failed to clear/leave after unexpected error for chat %s", chat_id
                )
            return
