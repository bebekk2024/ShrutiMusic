import asyncio
import inspect
import logging
from typing import Dict, Set, Optional, Any

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from ShrutiMusic import get_app
import config
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import music_on, get_lang
from strings import get_string

OWNER_ID = getattr(config, "OWNER_ID", 5779185981)

POLL_INTERVAL = 4
SCAN_INTERVAL = 6

_monitors: Dict[int, asyncio.Task] = {}
_scanner_task: Optional[asyncio.Task] = None
_handlers_registered = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ShrutiMusic.voice_monitor")


async def _get_participant_ids(assistant, chat_id: int) -> Set[int]:
    """Get participant IDs of a voice chat."""
    try:
        parts = await assistant.get_participants(chat_id)
        return {p.user.id for p in parts if getattr(p, "user", None)}
    except Exception as e:
        logger.error(f"Get participants error in chat {chat_id}: {e}", exc_info=True)
        return set()


async def _music_on_safe(chat_id: int) -> bool:
    """Safely determine if music is on for chat."""
    try:
        res = await music_on(chat_id)
    except Exception:
        logger.exception("music_on raised exception; treating as False")
        res = None

    if isinstance(res, bool):
        return res

    try:
        # Fallback check on db
        if chat_id in db or str(chat_id) in db:
            return True
    except Exception:
        logger.debug("Fallback db check failed in _music_on_safe", exc_info=True)
    return False


async def _resolve_group_assistant(chat_id: int) -> Optional[Any]:
    """
    Resolve and call group_assistant implementation present in ShrutiMusic.utils.database.
    Returns assistant instance or None.
    """
    try:
        import ShrutiMusic.utils.database as dbmod
    except Exception as e:
        logger.debug(f"Could not import ShrutiMusic.utils.database: {e}", exc_info=True)
        return None

    ga = getattr(dbmod, "group_assistant", None)
    if ga:
        try:
            sig = inspect.signature(ga)
            params = len(sig.parameters)
        except Exception:
            params = None

        try:
            if params == 1 or params is None:
                return await ga(chat_id)
            if params and params >= 2:
                return await ga(None, chat_id)
        except Exception as e:
            logger.debug(f"group_assistant call failed: {e}", exc_info=True)

    # Search for bound group_assistant method in dbmod
    for name, obj in vars(dbmod).items():
        if name.startswith("_"):
            continue
        candidate = getattr(obj, "group_assistant", None)
        if candidate and callable(candidate):
            try:
                if inspect.iscoroutinefunction(candidate):
                    return await candidate(chat_id)
                res = candidate(chat_id)
                if inspect.isawaitable(res):
                    return await res
            except Exception as e:
                logger.debug(f"Bound group_assistant failed on {name}: {e}", exc_info=True)

    # Try package-level manager (get_userbot)
    try:
        from ShrutiMusic import get_userbot
        manager = get_userbot()
        if manager:
            candidate = getattr(manager, "group_assistant", None)
            if callable(candidate):
                try:
                    if inspect.iscoroutinefunction(candidate):
                        return await candidate(chat_id)
                    res = candidate(chat_id)
                    if inspect.isawaitable(res):
                        return await res
                except Exception as e:
                    logger.debug(f"get_userbot().group_assistant failed: {e}", exc_info=True)
    except Exception:
        pass

    logger.error(f"Could not resolve a usable group_assistant for chat {chat_id}")
    return None


async def _monitor_chat(chat_id: int):
    """Monitor a chat's voice participants."""
    assistant = await _resolve_group_assistant(chat_id)
    if not assistant:
        logger.error(f"Assistant resolving failed for {chat_id}: no assistant available")
        return
    logger.info(f"Assistant fetched for chat {chat_id}: {type(assistant)}")

    prev = await _get_participant_ids(assistant, chat_id)
    logger.info(f"Starting voice monitor for chat {chat_id}")

    while await _music_on_safe(chat_id):
        try:
            cur = await _get_participant_ids(assistant, chat_id)
            joined = cur - prev
            left = prev - cur

            language = await get_lang(chat_id)
            _ = get_string(language)

            for uid in joined:
                try:
                    if uid == OWNER_ID:
                        await get_app().send_message(
                            chat_id,
                            text=(
                                f"👑 Selamat datang Owner!\n"
                                f"<a href='tg://user?id={uid}'>Owner</a> telah bergabung ke obrolan suara.\n"
                                "Bot sedang streaming sekarang."
                            ),
                            parse_mode="html",
                        )
                    else:
                        await get_app().send_message(
                            chat_id,
                            text=(
                                "👋 Selamat datang!\n"
                                f"<a href='tg://user?id={uid}'>User</a> telah bergabung ke obrolan suara.\n"
                                "Terima kasih sudah bergabung. (Bot sedang streaming sekarang.)"
                            ),
                            parse_mode="html",
                        )
                    logger.info(f"Sent welcome for user {uid} in chat {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send welcome message for {uid} in chat {chat_id}: {e}", exc_info=True)

            for uid in left:
                try:
                    if uid == OWNER_ID:
                        await get_app().send_message(
                            chat_id,
                            text=(
                                f"👑 Owner <a href='tg://user?id={uid}'>telah meninggalkan</a> obrolan suara.\n"
                                "Terima kasih sudah berkunjung!"
                            ),
                            parse_mode="html",
                        )
                    else:
                        await get_app().send_message(
                            chat_id,
                            text=(
                                f"👋 <a href='tg://user?id={uid}'>User</a> telah meninggalkan obrolan suara.\n"
                                "Semoga nanti bergabung kembali!"
                            ),
                            parse_mode="html",
                        )
                    logger.info(f"Sent leave for user {uid} in chat {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send leave message for {uid} in chat {chat_id}: {e}", exc_info=True)

            prev = cur
            await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            logger.info(f"Voice monitor for chat {chat_id} cancelled")
            break
        except Exception as e:
            logger.error(f"Voice monitor loop error in chat {chat_id}: {e}", exc_info=True)
            await asyncio.sleep(POLL_INTERVAL)

    _monitors.pop(chat_id, None)
    logger.info(f"Voice monitor STOP for chat {chat_id}")


async def _ensure_monitor(chat_id: int):
    """Ensure a monitor is running for a chat."""
    if chat_id in _monitors:
        return
    task = asyncio.create_task(_monitor_chat(chat_id))
    _monitors[chat_id] = task


async def _stop_monitor(chat_id: int):
    """Stop monitoring a chat."""
    task = _monitors.pop(chat_id, None)
    if task:
        task.cancel()
        try:
            await task
        except Exception as e:
            logger.error(f"Error stopping monitor for chat {chat_id}: {e}", exc_info=True)


async def _scan_loop():
    """Scans active chats and creates monitors as needed."""
    logger.info("Voice scanner loop started")
    try:
        while True:
            try:
                candidate_chats = list(db.keys())
            except Exception as e:
                logger.error(f"DB scan error: {e}", exc_info=True)
                candidate_chats = []

            for cid in candidate_chats:
                try:
                    if await _music_on_safe(cid):
                        await _ensure_monitor(cid)
                except Exception as e:
                    logger.error(f"Ensure monitor error for chat {cid}: {e}", exc_info=True)

            monitors_snapshot = list(_monitors.keys())
            for cid in monitors_snapshot:
                try:
                    if not await _music_on_safe(cid):
                        await _stop_monitor(cid)
                except Exception as e:
                    logger.error(f"Stop monitor error for chat {cid}: {e}", exc_info=True)

            await asyncio.sleep(SCAN_INTERVAL)
    except asyncio.CancelledError:
        logger.info("Scan loop cancelled.")
        return
    except Exception:
        logger.exception("Unexpected error in scan loop, restarting waiter")


async def start_scanner_manual():
    """Start scanner manually from your main code (awaitable)."""
    global _scanner_task
    if _scanner_task is None:
        loop = asyncio.get_running_loop()
        t = loop.create_task(_scan_loop())
        _scanner_task = t
        logger.info("Voice scanner started manually.")


async def stop_scanner_manual():
    """Stop scanner manually."""
    global _scanner_task
    if _scanner_task:
        _scanner_task.cancel()
        try:
            await _scanner_task
        except Exception:
            pass
        _scanner_task = None
        logger.info("Voice scanner stopped manually.")


def _get_allowed_users() -> list:
    """Get allowed user ids for using the scanner commands."""
    allowed = {OWNER_ID}
    sudo_users = getattr(config, "SUDO_USERS", None)
    if sudo_users:
        try:
            allowed.update(sudo_users)
        except Exception:
            pass
    return list(allowed)


ALLOWED_USERS = _get_allowed_users()


async def _scanner_command_handler(client, message: Message):
    """Handle /scanner commands to control the scanner."""
    try:
        cmd = message.command
    except Exception:
        cmd = []

    if len(cmd) < 2:
        await message.reply_text(
            "Usage: /scanner <start|stop|status>\nExample: /scanner start",
            quote=True,
        )
        return

    action = cmd[1].lower()

    if action in ("start", "on"):
        try:
            await start_scanner_manual()
            await message.reply_text("✅ Voice scanner started.", quote=True)
        except Exception as e:
            logger.error(f"Failed to start scanner via command: {e}", exc_info=True)
            await message.reply_text(f"⚠️ Failed to start scanner: {e}", quote=True)

    elif action in ("stop", "off"):
        try:
            await stop_scanner_manual()
            await message.reply_text("🛑 Voice scanner stopped.", quote=True)
        except Exception as e:
            logger.error(f"Failed to stop scanner via command: {e}", exc_info=True)
            await message.reply_text(f"⚠️ Failed to stop scanner: {e}", quote=True)

    elif action in ("status",):
        running = _scanner_task is not None and not getattr(_scanner_task, "done", lambda: False)()
        await message.reply_text(f"🔎 Voice scanner status: {'running' if running else 'stopped'}", quote=True)

    else:
        await message.reply_text("Unknown action. Use start, stop, or status.", quote=True)


def _register_handlers():
    global _handlers_registered
    if _handlers_registered:
        return
    try:
        app = get_app()
        app.add_handler(
            MessageHandler(
                _scanner_command_handler,
                filters.command(["scanner", "scannerv"]) & filters.user(ALLOWED_USERS),
            )
        )
        _handlers_registered = True
        logger.info("voice_monitor: command handlers registered")
    except Exception as e:
        logger.error(f"Failed to register voice_monitor handlers: {e}", exc_info=True)


def _autostart():
    """Run autostart for scanner at import time."""
    global _scanner_task
    try:
        try:
            loop = asyncio.get_running_loop()
            logger.debug("Using running loop from get_running_loop()")
        except RuntimeError:
            loop = asyncio.get_event_loop()
            logger.debug("No running loop; falling back to get_event_loop()")

        logger.info(f"Autostart configured with loop={loop!r}. is_running={loop.is_running()}")

        async def _wait_and_start():
            global _scanner_task
            logger.info("Autostart waiter started")
            await asyncio.sleep(0)
            tries = 0
            while not get_app().is_connected:
                tries += 1
                logger.info(f"Autostart: app.is_connected is False (try #{tries}), sleeping 2s")
                await asyncio.sleep(2)
            logger.info("Autostart: app.is_connected is True, registering handlers and creating scanner task")
            try:
                _register_handlers()
            except Exception as e:
                logger.error(f"Error registering handlers: {e}", exc_info=True)
            if _scanner_task is None:
                t = loop.create_task(_scan_loop())
                _scanner_task = t
                logger.info("Voice scanner started automatically (app connected)")

        if loop.is_running():
            loop.create_task(_wait_and_start())
            logger.info("Autostart waiter scheduled with loop.create_task()")
        else:
            loop.call_soon(lambda: asyncio.ensure_future(_wait_and_start()))
            logger.info("Loop not running yet; scheduled waiter with call_soon()")
    except Exception as e:
        logger.error(f"Cannot start scan loop (autostart): {e}", exc_info=True)
        _scanner_task = None


# Try autostart immediately on import
_autostart()
