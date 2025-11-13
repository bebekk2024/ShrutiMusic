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

import logging
from os import path

from yt_dlp import YoutubeDL

from ShrutiMusic.utils.formatters import seconds_to_min

class SoundAPI:
    def __init__(self):
        self.opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "format": "bestaudio/best",
            "retries": 3,
            "nooverwrites": False,
            "continuedl": True,
        }

    async def valid(self, link: str):
        return "soundcloud" in str(link).lower()

    async def download(self, url):
        d = YoutubeDL(self.opts)
        try:
            info = d.extract_info(url)
        except Exception as e:
            logging.error(f"[SoundAPI.download] yt_dlp extract_info error: {e}")
            return None
        # Defensive: check all info keys
        for key in ["id", "ext", "duration", "title", "uploader"]:
            if key not in info:
                logging.error(f"[SoundAPI.download] Missing info key: {key}")
                return None
        xyz = path.join("downloads", f"{info['id']}.{info['ext']}")
        duration_min = seconds_to_min(info["duration"]) if info["duration"] is not None else "0:00"
        track_details = {
            "title": info.get("title", "Unknown"),
            "duration_sec": info.get("duration", 0),
            "duration_min": duration_min,
            "uploader": info.get("uploader", "Unknown"),
            "filepath": xyz,
        }
        return track_details, xyz

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================

# ❤️ Love From ShrutiBots 
