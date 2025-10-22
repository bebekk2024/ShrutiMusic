# simplified, robust /vid handler with fallback to internal downloader
from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic import app
import requests
import os
import logging
import tempfile
from ShrutiMusic.platforms.Youtube import download_video_combined

logger = logging.getLogger("ShrutiMusic.plugins.downloader")

@app.on_message(filters.command("vid"))
async def video_downloader(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Please provide a video URL.\n\nExample:\n/vid Any_video_url"
        )

    video_url = message.text.split(None, 1)[1].strip()
    msg = await message.reply("🔍 Fetching video...")

    payload = {"url": video_url, "token": "c99f113fab0762d216b4545e5c3d615eefb30f0975fe107caab629d17e51b52d"}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }

    try:
        try:
            r = requests.post("https://allvideodownloader.cc/wp-json/aio-dl/video-data/", data=payload, headers=headers, timeout=15)
        except requests.RequestException as e:
            logger.warning("External downloader request failed: %s", e)
            r = None

        if r is None or r.status_code == 403:
            await msg.edit("❌ External service refused connection (403) or failed. Trying internal downloader...")
            internal_path = await download_video_combined(video_url)
            if internal_path:
                await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                await msg.delete()
                try:
                    os.remove(internal_path)
                except Exception:
                    pass
                return
            else:
                await msg.edit("❌ External service blocked and internal downloader failed.")
                return

        if r.status_code != 200:
            await msg.edit(f"⚠️ External service returned status {r.status_code}. Trying internal downloader...")
            internal_path = await download_video_combined(video_url)
            if internal_path:
                await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                await msg.delete()
                try:
                    os.remove(internal_path)
                except Exception:
                    pass
                return
            else:
                await msg.edit(f"❌ External service error {r.status_code} and internal downloader failed.")
                return

        try:
            data = r.json()
        except Exception as e:
            logger.exception("Failed to parse JSON from external service: %s", e)
            await msg.edit("❌ Unexpected response from external service. Trying internal downloader...")
            internal_path = await download_video_combined(video_url)
            if internal_path:
                await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                await msg.delete()
                try:
                    os.remove(internal_path)
                except Exception:
                    pass
                return
            else:
                await msg.edit("❌ External service failed and internal downloader failed.")
                return

        if "medias" not in data or not data["medias"]:
            await msg.edit("❌ No downloadable video found by external service. Trying internal downloader...")
            internal_path = await download_video_combined(video_url)
            if internal_path:
                await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                await msg.delete()
                try:
                    os.remove(internal_path)
                except Exception:
                    pass
                return
            else:
                await msg.edit("❌ Both external service and internal downloader failed to find the video.")
                return

        best_video = sorted(data["medias"], key=lambda x: x.get("quality", ""), reverse=True)[0]
        video_link = best_video.get("url")
        if not video_link:
            await msg.edit("❌ External service did not return a direct video link. Trying internal downloader...")
            internal_path = await download_video_combined(video_url)
            if internal_path:
                await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                await msg.delete()
                try:
                    os.remove(internal_path)
                except Exception:
                    pass
                return
            else:
                await msg.edit("❌ Could not obtain a direct video link.")
                return

        await msg.edit("⬇️ Downloading video (external link)...")
        tmp_file = None
        try:
            with requests.get(video_link, headers=headers, stream=True, timeout=30) as v:
                if v.status_code == 403:
                    await msg.edit("❌ Download link returned 403. Trying internal downloader...")
                    internal_path = await download_video_combined(video_url)
                    if internal_path:
                        await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                        await msg.delete()
                        try:
                            os.remove(internal_path)
                        except Exception:
                            pass
                        return
                    else:
                        await msg.edit("❌ Direct link blocked and internal downloader failed.")
                        return

                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
                tmp_file = tmp_path
                os.close(tmp_fd)
                with open(tmp_path, "wb") as f:
                    for chunk in v.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except requests.RequestException as e:
            logger.exception("Error downloading direct video link: %s", e)
            await msg.edit("❌ Error downloading from external link. Trying internal downloader...")
            internal_path = await download_video_combined(video_url)
            if internal_path:
                await app.send_video(chat_id=message.chat.id, video=internal_path, caption=f"🎬 Downloaded: {os.path.basename(internal_path)}")
                await msg.delete()
                try:
                    os.remove(internal_path)
                except Exception:
                    pass
                return
            else:
                await msg.edit("❌ Could not download the video.")
                return

        try:
            await app.send_video(chat_id=message.chat.id, video=tmp_file, caption=f"🎬 {data.get('title', 'Video')}\n\n✅ ", supports_streaming=True)
            await msg.delete()
        except Exception as e:
            logger.exception("Failed to send video to user: %s", e)
            await msg.edit(f"❌ Error sending video: {e}")
        finally:
            try:
                if tmp_file and os.path.exists(tmp_file):
                    os.remove(tmp_file)
            except Exception:
                pass

    except Exception as e:
        logger.exception("Unhandled error in /vid handler: %s", e)
        try:
            await msg.edit(f"❌ Error: {str(e)}")
        except Exception:
            pass
