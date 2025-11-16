# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# Initialization for ShrutiMusic package.
# This module performs lightweight bootstrap and exposes the main
# application objects (app, userbot) and several platform API wrappers.
#
# Notes:
# - Heavy/long-running side-effects are wrapped in try/except to avoid
#   breaking imports in case of an initialization error.
# - If you prefer, move dirr()/git()/dbb()/heroku() calls to a dedicated
#   startup script instead of running them on import.
from typing import Optional

# Prefer package logger if available; fallback to Python logging
try:
    from .logging import LOGGER  # local project logger (preferred)
except Exception:
    import logging
    LOGGER = logging.getLogger(__name__)
    LOGGER.debug("Falling back to stdlib logger for ShrutiMusic package")

# Core imports (wrap init calls to avoid breaking import on failure)
try:
    from ShrutiMusic.core.bot import Nand
    from ShrutiMusic.core.dir import dirr
    from ShrutiMusic.core.git import git
    from ShrutiMusic.core.userbot import Userbot
    from ShrutiMusic.misc import dbb, heroku
except Exception:
    LOGGER.exception("Failed to import core components; package may be partially broken")
    # Re-raise if you want import-time failure; otherwise continue with fallback behavior
    # raise

# Run lightweight bootstrap steps; protected so failures won't break imports
for _fn, _name in ((dirr, "dirr"), (git, "git"), (dbb, "dbb"), (heroku, "heroku")):
    try:
        if callable(_fn):
            _fn()
            LOGGER.debug("Successfully ran %s()", _name)
    except Exception:
        LOGGER.exception("Error running %s() during package bootstrap", _name)

# Create primary application objects; protect with try/except to prevent hard crashes
app: Optional[object] = None
userbot: Optional[object] = None
try:
    app = Nand()
    LOGGER.info("ShrutiMusic app initialized")
except Exception:
    LOGGER.exception("Failed to initialize app (Nand)")

try:
    userbot = Userbot()
    LOGGER.info("Userbot initialized")
except Exception:
    LOGGER.exception("Failed to initialize Userbot")

# Import and instantiate platform API wrappers.
# Wrap in try/except to avoid circular import or missing class issues.
Apple = Carbon = SoundCloud = Spotify = Resso = Telegram = YouTube = None
try:
    from .platforms import (
        AppleAPI,
        CarbonAPI,
        SoundAPI,
        SpotifyAPI,
        RessoAPI,
        TeleAPI,
        YouTubeAPI,
    )

    try:
        Apple = AppleAPI()
        Carbon = CarbonAPI()
        SoundCloud = SoundAPI()
        Spotify = SpotifyAPI()
        Resso = RessoAPI()
        Telegram = TeleAPI()
        YouTube = YouTubeAPI()
        LOGGER.info("Platform API wrappers initialized")
    except Exception:
        LOGGER.exception("Failed to instantiate one or more platform API wrappers")
except Exception:
    LOGGER.exception("Failed to import .platforms module; platform APIs unavailable")

# Public API of the package
__all__ = [
    "app",
    "userbot",
    "Apple",
    "Carbon",
    "SoundCloud",
    "Spotify",
    "Resso",
    "Telegram",
    "YouTube",
]

# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi
# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================
