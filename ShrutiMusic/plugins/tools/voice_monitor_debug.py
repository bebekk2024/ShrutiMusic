# Debug helper for ShrutiMusic voice monitor — temporary file
# Place in ShrutiMusic/ and restart bot. Only OWNER and SUDO_USERS can use.
import asyncio
import logging
from typing import List

from pyrogram import filters
from pyrogram.types import Message

from ShrutiMusic import app
import config
from ShrutiMusic.misc import db
from ShrutiMusic.utils.database import music_on
# import internals if available
try:
    from ShrutiMusic import voice_monitor
except Exception:
    voice_monitor = None

OWNER_ID = getattr(config, "OWNER_ID", None)
SUDO = getattr(config, "SUDO_USERS", None) or []

ALLOWED = [x for x in ([OWNER_ID] + list(SUDO) if SUDO else [OWNER_ID]) if x]

logger = logging.getLogger("ShrutiMusic.voice_monitor_debug")

def _short_task_repr(t):
    try:
        return f"{t.get_name() if hasattr(t,'get_name') else t!r} done={t.done()}"
    except Exception:
        return repr(t)

@app.on_message(filters.command("scanner_debug") & filters.user(ALLOWED))
async def _scanner_debug(_, message: Message):
    """
    Usage: /scanner_debug
    Returns:
      - Whether voice_monitor module imported
      - _scanner_task status
      - active monitor chat ids
      - db keys sample and music_on result for first key
      - lists currently running asyncio tasks (short)
    """
    out_lines: List[str] = []
    out_lines.append("🔍 Scanner debug\n")

    # voice_monitor import check
    if voice_monitor is None:
        out_lines.append("voice_monitor module: NOT IMPORTED")
    else:
        out_lines.append("voice_monitor module: IMPORTED")

    # scanner task and monitors
    try:
        if voice_monitor is not None:
            st = getattr(voice_monitor, "_scanner_task", None)
            monitors = getattr(voice_monitor, "_monitors", {})
            out_lines.append(f"_scanner_task: {st} (None means not started)")
            out_lines.append(f"_monitors count: {len(monitors)}")
            out_lines.append(f"_monitors keys: {list(monitors.keys())}")
        else:
            out_lines.append("_scanner_task: unknown (module not imported)")
            out_lines.append("_monitors: unknown (module not imported)")
    except Exception as e:
        out_lines.append(f"Error reading monitor globals: {e}")

    # db keys
    try:
        keys = list(db.keys())
        out_lines.append(f"db keys count: {len(keys)}")
        out_lines.append(f"db sample (first 10): {keys[:10]}")
    except Exception as e:
        out_lines.append(f"Error accessing db.keys(): {e}")

    # music_on check for first key
    if keys:
        try:
            val = await music_on(keys[0])
            out_lines.append(f"music_on({keys[0]}) => {val}")
        except Exception as e:
            out_lines.append(f"music_on check error for {keys[0]}: {e}")
    else:
        out_lines.append("No keys to check music_on")

    # asyncio tasks snapshot
    try:
        tasks = asyncio.all_tasks()
        out_lines.append(f"Total asyncio tasks: {len(tasks)} (showing up to 20)")
        sample = [ _short_task_repr(t) for t in list(tasks)[:20] ]
        out_lines.append("Tasks sample: " + ", ".join(sample))
    except Exception as e:
        out_lines.append(f"Error enumerating tasks: {e}")

    # join and send
    await message.reply_text("\n".join(out_lines), quote=True)
