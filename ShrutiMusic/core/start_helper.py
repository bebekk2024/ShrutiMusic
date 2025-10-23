# Helper untuk memulai Pyrogram/Client dengan penanganan FloodWait agar dyno tidak crash loop.
import asyncio
import logging
from typing import Optional

from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

async def safe_start(app, max_retries: int = 5, extra_wait: int = 5) -> None:
    """
    Mulai aplikasi Pyrogram (app.start()) dengan penanganan FloodWait.
    - app: instance pyrogram Client (mis. bot)
    - max_retries: maksimal percobaan ulang ketika terkena FloodWait
    - extra_wait: detik tambahan untuk safety setelah FloodWait selesai
    """
    retries = 0
    while True:
        try:
            logger.info("Attempting to start bot (safe_start).")
            await app.start()
            logger.info("Bot started successfully.")
            return
        except FloodWait as e:
            retries += 1
            # Try robust extraction of wait seconds
            wait = None
            for attr in ("x", "wait", "value", "seconds"):
                wait = getattr(e, attr, None)
                if wait:
                    break
            if wait is None:
                # fallback parse from message
                try:
                    wait = int(str(e).split()[-2])
                except Exception:
                    wait = 60
            wait = int(wait)
            logger.warning(
                "FloodWait received: must wait %ss (attempt %d/%d). Sleeping...",
                wait,
                retries,
                max_retries,
            )
            await asyncio.sleep(wait + extra_wait)
            if retries >= max_retries:
                logger.error("Max FloodWait retries reached, aborting safe_start to avoid crash loop.")
                raise
        except Exception:
            logger.exception("Unhandled exception while trying to start bot; re-raising.")
            raise
