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

# Pastikan ada event loop sebelum mengimpor modul yang memicu pyrogram (mis. core.bot)
# Ini mencegah RuntimeError: "There is no current event loop in thread 'MainThread'".
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from ShrutiMusic.core.bot import Nand
from ShrutiMusic.core.dir import dirr
from ShrutiMusic.core.git import git
from ShrutiMusic.core.userbot import Userbot
from ShrutiMusic.misc import mongodb
from ShrutiMusic.misc import dbb, heroku
from ShrutiMusic.misc import SUDOERS
from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Nand()
userbot = Userbot()

from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi
