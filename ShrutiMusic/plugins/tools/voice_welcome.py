from typing import Dict, Set
import asyncio

from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic import app
import OWNER_ID
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import music_on, group_assistant, get_lang
from strings import get_string

# Intervals (seconds)
POLL_INTERVAL = 4          # how often to poll participants for each monitored chat
SCAN_INTERVAL = 6          # how often to scan for chats where music_on(chat) is True

# Map chat_id -> asyncio.Task (participant monitor)
_monitors: Dict[int, asyncio.Task] = {}

# Background scanner task
_scanner_task: asyncio.Task | None = None


async def _get_participant_ids(assistant, chat_id) -> Set[int]:
    try:
        parts = await assistant.get_participants(chat_id)
        return {p.user.id for p in parts if getattr(p, "user", None)}
    except Exception:
        return set()


async def _monitor_chat(chat_id: int):
    """
    Poll participants while music_on(chat_id) == True.
    Sends welcome when someone joins and goodbye when someone leaves.
    Special greetings for OWNER_ID.
    """
    try:
        assistant = await group_assistant(None, chat_id)
    except Exception:
        return

    prev = await _get_participant_ids(assistant, chat_id)

    while await music_on(chat_id):
        try:
            cur = await _get_participant_ids(assistant, chat_id)
            joined = cur - prev
            left = prev - cur

            language = await get_lang(chat_id)
            _ = get_string(language)

            if joined:
                for uid in joined:
                    try:
                        if uid == OWNER_ID:
                            await app.send_message(
                                chat_id,
                                text=(
                                    f"👑 Selamat datang Owner!\n"
                                    f"<a href='tg://user?id={uid}'>Owner</a> telah bergabung ke obrolan suara.\n"
                                    "Bot sedang streaming sekarang."
                                ),
                                parse_mode="html",
                            )
                        else:
                            await app.send_message(
                                chat_id,
                                text=(
                                    f"👋 Selamat datang!\n"
                                    f"<a href='tg://user?id={uid}'>User</a> telah bergabung ke obrolan suara.\n"
                                    "Terima kasih sudah bergabung. (Bot sedang streaming sekarang.)"
                                ),
                                parse_mode="html",
                            )
                    except Exception:
                        pass

            if left:
                for uid in left:
                    try:
                        if uid == OWNER_ID:
                            await app.send_message(
                                chat_id,
                                text=(
                                    f"👑 Owner <a href='tg://user?id={uid}'>telah meninggalkan</a> obrolan suara.\n"
                                    "Terima kasih sudah berkunjung!"
                                ),
                                parse_mode="html",
                            )
                        else:
                            await app.send_message(
                                chat_id,
                                text=(
                                    f"👋 <a href='tg://user?id={uid}'>User</a> telah meninggalkan obrolan suara.\n"
                                    "Semoga nanti bergabung kembali!"
                                ),
                                parse_mode="html",
                            )
                    except Exception:
                        pass

            prev = cur
            await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(POLL_INTERVAL)

    _monitors.pop(chat_id, None)


async def _ensure_monitor(chat_id: int):
    if chat_id in _monitors:
        return
    task = asyncio.create_task(_monitor_chat(chat_id))
    _monitors[chat_id] = task


async def _stop_monitor(chat_id: int):
    task = _monitors.pop(chat_id, None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass


async def _scan_loop():
    """
    Periodically scan for chats that have music_on(chat) == True and ensure monitors run.
    Uses ShrutiMusic.misc.db keys as source of known chats if no helper exists.
    """
    try:
        while True:
            # Derive candidate active chats from db keys (fallback)
            try:
                candidate_chats = list(db.keys())
            except Exception:
                candidate_chats = []

            for cid in candidate_chats:
                try:
                    if await music_on(cid):
                        await _ensure_monitor(cid)
                except Exception:
                    pass

            # Stop monitors that are no longer active
            monitors_snapshot = list(_monitors.keys())
            for cid in monitors_snapshot:
                try:
                    if not await music_on(cid):
                        await _stop_monitor(cid)
                except Exception:
                    pass

            await asyncio.sleep(SCAN_INTERVAL)
    except asyncio.CancelledError:
        return


# Start scanner when bot event loop is running
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        if _scanner_task is None:
            _scanner_task = loop.create_task(_scan_loop())
except RuntimeError:
    _scanner_task = None
