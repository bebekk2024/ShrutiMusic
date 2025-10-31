import traceback
from functools import wraps
from datetime import datetime

from config import LOG_GROUP_ID, OWNER_ID
from ShrutiMusic import app

def split_limits(text):
    if len(text) < 2048:
        return [text]
    lines = text.splitlines(True)
    small_msg = ""
    result = []
    for line in lines:
        if len(small_msg) + len(line) < 2048:
            small_msg += line
        else:
            result.append(small_msg)
            small_msg = line
    result.append(small_msg)
    return result

def capture_err(func):
    @wraps(func)
    async def capture(client, message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as err:
            errors = traceback.format_exc()
            waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_mention = getattr(message.from_user, 'mention', 'Unknown')
            chat_info = (
                f"@{getattr(message.chat, 'username', '-')}"
                if message.chat and getattr(message.chat, 'username', None)
                else f"`{message.chat.id}`" if message.chat else '-'
            )
            error_feedback = split_limits(
                f"**[AUTO BUG REPORT]**\n"
                f"**Time:** {waktu}\n"
                f"**User:** {user_mention}\n"
                f"**Chat:** {chat_info}\n"
                f"**Command:** `{message.text or message.caption}`\n"
                f"**Traceback:**\n```python\n{errors}\n```\n"
                f"Silakan hubungi OWNER agar masalah segera diperbaiki."
            )
            # Kirim ke grup log
            for x in error_feedback:
                await app.send_message(LOG_GROUP_ID, x)
            # Kirim notifikasi langsung ke OWNER_ID
            for x in error_feedback:
                await app.send_message(OWNER_ID, x)
            raise err
    return capture
