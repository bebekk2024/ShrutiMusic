from functools import wraps
import traceback
from datetime import datetime

from ShrutiMusic import app
from ShrutiMusic.config import OWNER_ID


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
    if small_msg:
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
            command_text = message.text or message.caption or '-'
            error_text = (
                f"**[AUTO BUG REPORT]**\n"
                f"**Time:** {waktu}\n"
                f"**User:** {user_mention}\n"
                f"**Chat:** {chat_info}\n"
                f"**Command:** `{command_text}`\n"
                f"**Traceback:**\n```python\n{errors}\n```\n"
                f"Silakan hubungi OWNER agar masalah segera diperbaiki."
            )

            error_feedback = split_limits(error_text)

            # Kirim notifikasi langsung ke OWNER_ID
            send_failed = False
            send_exceptions = []
            for chunk in error_feedback:
                try:
                    await app.send_message(OWNER_ID, chunk)
                except Exception as e:
                    send_failed = True
                    send_exceptions.append((type(e).__name__, str(e)))

            # Jika pengiriman ke OWNER gagal, balas ke pengirim agar ada notifikasi
            if send_failed:
                # Gabungkan error kecil jadi satu pesan singkat untuk pengirim
                reasons = "; ".join([f"{n}: {m}" for n, m in send_exceptions])
                try:
                    await message.reply_text(
                        "⚠️ Laporan error gagal dikirim ke owner.\n"
                        f"Alasan: {reasons}\n"
                        "Silakan hubungi owner secara langsung."
                    )
                except Exception:
                    # Jika bahkan reply ke pengirim gagal, print ke console sebagai fallback
                    print("Gagal memberi feedback ke user dan owner. Errors:", send_exceptions)

            # Jangan swallow exception; biarkan naik sehingga pipeline lain (jika ada) tahu
            raise err
    return capture
