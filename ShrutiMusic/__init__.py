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

# Pastikan ada event loop sebelum import yang memicu pyrogram
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Use relative imports and avoid importing heavy objects at module import time
from .core.dir import dirr
from .core.git import git
from .core.userbot import Userbot
from .misc import mongodb
from .misc import dbb, heroku
from .misc import SUDOERS
from .logging import LOGGER

# Run lightweight initialization (these should not import core.bot)
dirr()
git()
dbb()
heroku()

# Lazily created singletons to avoid circular imports
_app_instance = None
_userbot_instance = None

def get_app(*args, **kwargs):
    """
    Lazily import and return the Nand bot instance.
    Use this instead of importing Nand at package import-time to avoid circular imports.
    """
    global _app_instance
    if _app_instance is None:
        from .core.bot import Nand  # local import to break possible cycles
        _app_instance = Nand(*args, **kwargs)
    return _app_instance

def get_userbot(*args, **kwargs):
    """
    Lazily import and return the Userbot instance.
    """
    global _userbot_instance
    if _userbot_instance is None:
        _userbot_instance = Userbot(*args, **kwargs)
    return _userbot_instance

# Provide module-level lazy attributes for backward compatibility:
def __getattr__(name: str):
    """
    Lazy attribute loader for:
    - app, userbot: return instances
    - Nand, Userbot: return classes
    - platform singletons: Apple, Carbon, SoundCloud, Spotify, Resso, Telegram, YouTube
    """
    if name == "app":
        return get_app()
    if name == "userbot":
        return get_userbot()
    if name == "Nand":
        from .core.bot import Nand as _Nand
        return _Nand
    if name == "Userbot":
        return Userbot

    if name in {
        "Apple",
        "Carbon",
        "SoundCloud",
        "Spotify",
        "Resso",
        "Telegram",
        "YouTube",
    }:
        # Import platforms lazily to avoid triggering package-level cycles
        from .platforms import (
            AppleAPI,
            CarbonAPI,
            SoundAPI,
            SpotifyAPI,
            RessoAPI,
            TeleAPI,
            YouTubeAPI,
        )
        mapping = {
            "Apple": AppleAPI,
            "Carbon": CarbonAPI,
            "SoundCloud": SoundAPI,
            "Spotify": SpotifyAPI,
            "Resso": RessoAPI,
            "Telegram": TeleAPI,
            "YouTube": YouTubeAPI,
        }
        # Return a singleton instance per attribute name
        instance_name = f"_{name.lower()}_instance"
        if not hasattr(globals().get("__builtins__", {}), instance_name):
            # store on module globals to preserve instance
            globals()[instance_name] = mapping[name]()
        return globals()[instance_name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Public API
__all__ = [
    "get_app",
    "get_userbot",
    "app",
    "userbot",
    "Nand",
    "Userbot",
    "Apple",
    "Carbon",
    "SoundCloud",
    "Spotify",
    "Resso",
    "Telegram",
    "YouTube",
    "mongodb",
    "SUDOERS",
    "LOGGER",
]

# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================

# ❤️ Love From ShrutiBots
