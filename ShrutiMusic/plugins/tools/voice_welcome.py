import asyncio
import logging
from typing import Dict, Set

from ShrutiMusic import app
import config
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import music_on, group_assistant, get_lang
from strings import get_string

OWNER_ID = getattr(config, "OWNER_ID", 5779185981)

POLL_INTERVAL = 4
SCAN_INTERVAL = 6

_monitors: Dict[int, asyncio.Task] = {}
_scanner_task: asyncio.Task | None = None

logging.basicConfig(level=logging.INFO)

async def _get_participant_ids(assistant, chat_id) -> Set[int]:
    try:
        parts = await assistant.get_participants(chat_id)
        return {p.user.id for p in parts if getattr(p, "user", None)}
    except Exception as e:
        logging.error(f"Get participants error in chat {chat_id}: {e}")
        return set()

async def _monitor_chat(chat_id: int):
    try:
        assistant = await group_assistant(None, chat_id)
        logging.info(f"Assistant fetched for chat {chat_id}")
    except Exception as e:
        logging.error(f"Assistant resolving failed for {chat_id}: {e}")
        return

    prev = await _get_participant_ids(assistant, chat_id)
    logging.info(f"Starting voice monitor for chat {chat_id}")

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
                        logging.info(f"Send welcome for user {uid} in chat {chat_id}")
                    except Exception as e:
                        logging.error(f"Failed to send welcome message for {uid} in chat {chat_id}: {e}")

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
                        logging.info(f"Send leave for user {uid} in chat {chat_id}")
                    except Exception as e:
                        logging.error(f"Failed to send leave message for {uid} in chat {chat_id}: {e}")

            prev = cur
            await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            logging.info(f"Voice monitor for chat {chat_id} cancelled")
            break
        except Exception as e:
            logging.error(f"Voice monitor loop error in chat {chat_id}: {e}")
            await asyncio.sleep(POLL_INTERVAL)

    _monitors.pop(chat_id, None)
    logging.info(f"Voice monitor STOP for chat {chat_id}")

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
        except Exception as e:
            logging.error(f"Error stopping monitor for chat {chat_id}: {e}")

async def _scan_loop():
    logging.info("Voice scanner loop started")
    try:
        while True:
            try:
                candidate_chats = list(db.keys())
            except Exception as e:
                logging.error(f"DB scan error: {e}")
                candidate_chats = []

            for cid in candidate_chats:
                try:
                    if await music_on(cid):
                        await _ensure_monitor(cid)
                except Exception as e:
                    logging.error(f"Ensure monitor error for chat {cid}: {e}")

            monitors_snapshot = list(_monitors.keys())
            for cid in monitors_snapshot:
                try:
                    if not await music_on(cid):
                        await _stop_monitor(cid)
                except Exception as e:
                    logging.error(f"Stop monitor error for chat {cid}: {e}")

            await asyncio.sleep(SCAN_INTERVAL)
    except asyncio.CancelledError:
        logging.info("Scan loop cancelled.")
        return

# Auto start when imported (event loop detection)
def _autostart():
    global _scanner_task  # <-- Tambahkan ini di baris atas fungsi sebelum segala assignment!
    try:
        loop = asyncio.get_event_loop()
        def run_when_app_started():
            if app.is_connected:
                if _scanner_task is None:
                    _scanner_task = loop.create_task(_scan_loop())
                    logging.info("Voice scanner started automatically (detected app running)")
            else:
                loop.call_later(2, run_when_app_started)
        run_when_app_started()
    except Exception as e:
        logging.error(f"Cannot start scan loop: {e}")
        _scanner_task = None  # assignment ini juga ke global

_autostart()  # Import = langsung running di background!
