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

# Initialize bootstrap names to None so later code can safely reference them
dirr = git = None
dbb = heroku = None
Nand = None
Userbot = None

# Core imports (wrap init calls to avoid breaking import on failure)
try:
    # Use relative imports to keep package import paths consistent
    from .core.bot import Nand
    from .core.dir import dirr
    from .core.git import git
    from .core.userbot import Userbot
    from .misc import dbb, heroku
except Exception:
    LOGGER.exception("Failed to import core components; package may be partially broken")
    # leave names as None so subsequent code can check before using them

# Run lightweight bootstrap steps; protected so failures won't break imports
_bootstrap_fns = ((dirr, "dirr"), (git, "git"), (dbb, "dbb"), (heroku, "heroku"))
for _fn, _name in _bootstrap_fns:
    try:
        if _fn and callable(_fn):
            _fn()
            LOGGER.debug("Successfully ran %s()", _name)
    except Exception:
        LOGGER.exception("Error running %s() during package bootstrap", _name)

# Create primary application objects; protect with try/except to prevent hard crashes
app: Optional[object] = None
userbot: Optional[object] = None
if Nand is not None:
    try:
        app = Nand()
        LOGGER.info("ShrutiMusic app initialized")
    except Exception:
        LOGGER.exception("Failed to initialize app (Nand)")
else:
    LOGGER.debug("Nand class unavailable; app not initialized")

if Userbot is not None:
    try:
        userbot = Userbot()
        LOGGER.info("Userbot initialized")
    except Exception:
        LOGGER.exception("Failed to initialize Userbot")
else:
    LOGGER.debug("Userbot class unavailable; userbot not initialized")

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
        Apple = AppleAPI() if "AppleAPI" in globals() else None
        Carbon = CarbonAPI() if "CarbonAPI" in globals() else None
        SoundCloud = SoundAPI() if "SoundAPI" in globals() else None
        Spotify = SpotifyAPI() if "SpotifyAPI" in globals() else None
        Resso = RessoAPI() if "RessoAPI" in globals() else None
        Telegram = TeleAPI() if "TeleAPI" in globals() else None
        YouTube = YouTubeAPI() if "YouTubeAPI" in globals() else None
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
