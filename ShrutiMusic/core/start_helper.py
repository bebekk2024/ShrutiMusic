# Helper untuk memulai Pyrogram/Client dengan penanganan FloodWait agar dyno tidak crash loop.
import asyncio
import logging
from typing import Optional

from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

async def safe_start(app,
