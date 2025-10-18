# antigcst plugin for ShrutiMusic
# Adds per-chat anti-gcast/anti-spam protections with global owner-only toggle and SUDOERS override.
# New feature: "delete_all" (strict) mode which deletes any non-exempt message immediately.
# New feature: notifications — bot sends a group notification message when protect or delete_all is toggled.
#
# - /protect or /antigcast [on|off]         -> toggle protection (respects global only-owner & sudo override)
# - /protectmode or /antigcstmode all on|off -> per-chat: enable/disable delete-all (strict) mode
# - /antigcstconfig                         -> OWNER only: manage global settings (onlyowner, sudooverride)
# - /free, /unfree, /listwhite, /clearwhite -> whitelist users (approved)
# - /addblack, /delblack, /listblack, /clearblack -> blacklist users (silent)
# - /bl, /unbl, /listbl                     -> text blacklist (delete messages containing listed phrases)
#
# Stored in MongoDB collections: antigcst (per-chat) and antigcst_config (global)
# Access: chat admin commands are protected by AdminActual; global config is OWNER-only.

import asyncio
import logging

from typing import List

from pyrogram import filters, errors, enums
from pyrogram.types import Message

from ShrutiMusic import app, LOGGER
import config
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.utils.decorators import AdminActual

# Logger setup (fixes AttributeError issue)
LOGGER = logging.getLogger(__name__)

COL = mongodb.antigcst  # per-chat collection
CFG = mongodb.antigcst_config  # global config collection


def _chat_doc_key(chat_id: int):
    return {"chat_id": chat_id}


async def _get_doc(chat_id: int) -> dict:
    doc = await COL.find_one(_chat_doc_key(chat_id))
    if not doc:
        doc = {
            "chat_id": chat_id,
            "protect": False,
            "delete_all": False,  # strict mode: delete any message (except exempt)
            "approved_users": [],
            "silent_users": [],
            "delete_words": [],
        }
        await COL.insert_one(doc)
    return doc


async def _set_protect(chat_id: int, value: bool):
    await COL.update_one(_chat_doc_key(chat_id), {"$set": {"protect": value}}, upsert=True)


async def _set_delete_all(chat_id: int, value: bool):
    await COL.update_one(_chat_doc_key(chat_id), {"$set": {"delete_all": value}}, upsert=True)


async def _add_to_list(chat_id: int, field: str, value):
    await COL.update_one(_chat_doc_key(chat_id), {"$addToSet": {field: value}}, upsert=True)


async def _remove_from_list(chat_id: int, field: str, value):
    await COL.update_one(_chat_doc_key(chat_id), {"$pull": {field: value}}, upsert=True)


async def _get_list(chat_id: int, field: str) -> List:
    doc = await COL.find_one(_chat_doc_key(chat_id))
    if not doc:
        return []
    return doc.get(field, [])


# Global config helpers
async def _get_global_config() -> dict:
    cfg = await CFG.find_one({"_id": "settings"})
    if not cfg:
        cfg = {"_id": "settings", "only_owner_toggle": False, "sudo_override": True}
        await CFG.insert_one(cfg)
    return cfg


async def _set_global_config(field: str, value):
    await CFG.update_one({"_id": "settings"}, {"$set": {field: value}}, upsert=True)


async def _notify_chat_toggle(chat_id: int, text: str):
    """
    Send a persistent notification to the chat about toggles.
    This helps members know that strict mode / protect changed.
    """
    try:
        await app.send_message(chat_id, text)
    except Exception:
        LOGGER.warning("Failed to send antigcst toggle notification to %s", chat_id)


@app.on_message(filters.command(["protect", "antigcast"]) & filters.group)
@AdminActual
async def antigcst_toggle(client, message: Message, _):
    """
    /protect on|off
    /antigcast on|off

    Behavior:
    - If global only_owner_toggle is True then only OWNER_ID can toggle per-chat protect,
      unless sudo_override is True and the invoking user is in SUDOERS.
    - Sends a notification message to the chat when toggled.
    """
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply_text("<blockquote><b>Gunakan format: /protect [on|off]</b></blockquote>")

    mode = message.command[1].lower()

    # load global config and enforce owner-only toggle if enabled
    try:
        cfg = await _get_global_config()
    except Exception:
        cfg = {"only_owner_toggle": False, "sudo_override": True}

    only_owner = cfg.get("only_owner_toggle", False)
    sudo_override = cfg.get("sudo_override", True)
    user_id = message.from_user.id
    user_mention = message.from_user.mention

    if only_owner:
        # owner always allowed
        owner_id = getattr(config, "OWNER_ID", 5779185981)
        if user_id != owner_id:
            # allow SUDOERS only if sudo_override enabled
            if not (sudo_override and user_id in SUDOERS):
                return await message.reply_text(
                    "<blockquote><b>Hanya owner (atau SUDOERS jika sudo_override aktif) yang dapat mengubah pengaturan protect</b></blockquote>"
                )

    if mode in ("on", "true", "1"):
        doc = await _get_doc(chat_id)
        if doc.get("protect"):
            return await message.reply_text("<blockquote><b>Protect sudah diaktifkan</b></blockquote>")
        await _set_protect(chat_id, True)
        await _notify_chat_toggle(chat_id, f"<blockquote><b>🔒 Anti-Gcast PROTECT diaktifkan oleh {user_mention}</b></blockquote>")
        return await message.reply_text("<blockquote><b>Berhasil mengaktifkan protect</b></blockquote>")
    elif mode in ("off", "false", "0"):
        doc = await _get_doc(chat_id)
        if not doc.get("protect"):
            return await message.reply_text("<blockquote><b>Protect belum diaktifkan</b></blockquote>")
        await _set_protect(chat_id, False)
        await _notify_chat_toggle(chat_id, f"<blockquote><b>🔓 Anti-Gcast PROTECT dinonaktifkan oleh {user_mention}</b></blockquote>")
        return await message.reply_text("<blockquote><b>Berhasil menonaktifkan protect</b></blockquote>")
    else:
        return await message.reply_text("<blockquote><b>Format salah. Gunakan: /protect [on|off]</b></blockquote>")


# Per-chat strict mode: delete any message (except exemptions)
@app.on_message(filters.command(["protectmode", "antigcstmode"]) & filters.group)
@AdminActual
async def antigcst_mode(client, message: Message, _):
    """
    /protectmode all on|off
    /antigcstmode all on|off

    'all' = delete_all mode: when enabled, any non-exempt message will be deleted immediately.
    Exemptions: chat admins/owner, approved_users (whitelist), SUDOERS.
    Respects global only_owner_toggle & sudo_override same as /protect.
    Sends notification to group when toggled.
    """
    chat_id = message.chat.id
    if len(message.command) < 3:
        return await message.reply_text("<blockquote><b>Gunakan: /protectmode all on|off</b></blockquote>")

    sub = message.command[1].lower()
    val = message.command[2].lower()

    # enforce global only-owner if enabled
    try:
        cfg = await _get_global_config()
    except Exception:
        cfg = {"only_owner_toggle": False, "sudo_override": True}
    only_owner = cfg.get("only_owner_toggle", False)
    sudo_override = cfg.get("sudo_override", True)
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    if only_owner:
        owner_id = getattr(config, "OWNER_ID", None)
        if user_id != owner_id and not (sudo_override and user_id in SUDOERS):
            return await message.reply_text("<blockquote><b>Hanya owner (atau SUDOERS jika sudo_override aktif) yang dapat mengubah mode ini</b></blockquote>")

    if sub != "all":
        return await message.reply_text("<blockquote><b>Opsi tidak dikenali. Saat ini hanya 'all' didukung</b></blockquote>")

    if val not in ("on", "off", "true", "false", "1", "0"):
        return await message.reply_text("<blockquote><b>Nilai harus on atau off</b></blockquote>")

    bool_val = val in ("on", "true", "1")
    await _set_delete_all(chat_id, bool_val)
    # notify group
    if bool_val:
        await _notify_chat_toggle(chat_id, f"<blockquote><b>⛔️ delete_all (STRICT) mode DIHIDUPKAN oleh {user_mention}.\nSemua pesan non-exempt akan dihapus</b></blockquote>")
    else:
        await _notify_chat_toggle(chat_id, f"<blockquote><b>✅ delete_all (STRICT) mode DINONAKTIFKAN oleh {user_mention}.</b></blockquote>")
    return await message.reply_text(f"<blockquote><b>delete_all (strict) diset ke {bool_val} untuk chat ini</b></blockquote>")


# OWNER-only global settings command
@app.on_message(filters.command(["antigcstconfig", "antigcstsettings"]) & filters.user(getattr(config, "OWNER_ID", 5779185981)))
async def antigcst_config(client, message: Message):
    """
    /antigcstconfig onlyowner on|off
    /antigcstconfig sudooverride on|off
    /antigcstconfig show

    Only OWNER can run this command. It controls global behavior:
    - onlyowner: when on, only owner (or SUDOERS if sudooverride=True) can toggle /protect per-chat
    - sudooverride: when on, SUDOERS are allowed to toggle even if onlyowner is on
    """
    if len(message.command) == 1:
        return await message.reply_text("<blockquote><b>Gunakan: /antigcstconfig <onlyowner|sudooverride|show> [on|off]</b></blockquote>")

    cmd = message.command[1].lower()
    if cmd == "show":
        cfg = await _get_global_config()
        text = (
            f">Global antigcst settings:\n"
            f"- only_owner_toggle: {cfg.get('only_owner_toggle')}\n"
            f"- sudo_override: {cfg.get('sudo_override')}\n"
        )
        return await message.reply_text(text)

    if len(message.command) < 3:
        return await message.reply_text("<blockquote><b>Sertakan nilai on atau off</b></blockquote>")

    val = message.command[2].lower()
    if val not in ("on", "off", "true", "false", "1", "0"):
        return await message.reply_text("<blockquote><b>Nilai harus on atau off</b></blockquote>")
    bool_val = val in ("on", "true", "1")

    if cmd == "onlyowner":
        await _set_global_config("only_owner_toggle", bool_val)
        return await message.reply_text(f">only_owner_toggle diset ke {bool_val}")
    elif cmd == "sudooverride":
        await _set_global_config("sudo_override", bool_val)
        return await message.reply_text(f"<blockquote><b>sudo_override diset ke {bool_val}</b></blockquote>")
    else:
        return await message.reply_text("<blockquote><b>Opsi tidak dikenali. Gunakan onlyowner atau sudooverride</b></blockquote>")


# Whitelist (approved) management
@app.on_message(filters.command(["free", "approve", "addwhite"]) & filters.group)
@AdminActual
async def add_approve(client, message: Message, _):
    reply = message.reply_to_message
    try:
        target = reply.from_user.id if reply else int(message.command[1])
    except (AttributeError, IndexError, ValueError):
        # try username
        try:
            target = message.text.split(None, 1)[1]
        except Exception:
            return await message.reply_text("<blockquote><b>Balas pesan pengguna atau berikan id/username</b></blockquote>")

    try:
        user = await client.get_users(target)
    except (errors.PeerIdInvalid, errors.UsernameInvalid, errors.UsernameNotOccupied, ValueError):
        return await message.reply_text("<blockquote><b>Tidak dapat menemukan pengguna tersebut</b></blockquote>")

    ids = user.id
    if ids in SUDOERS:
        return await message.reply_text("<blockquote><b>Pengguna adalah SUDOERS bot!</b></blockquote>")

    approved = await _get_list(message.chat.id, "approved_users")
    if ids in approved:
        return await message.reply_text("<blockquote><b>Pengguna sudah disetujui</b></blockquote>")
    await _add_to_list(message.chat.id, "approved_users", ids)
    return await message.reply_text(f"<blockquote><b>Pengguna {user.mention} telah disetujui, tidak akan terkena antigcst</b></blockquote>")


@app.on_message(filters.command(["unfree", "unapprove", "delwhite"]) & filters.group)
@AdminActual
async def un_approve(client, message: Message, _):
    reply = message.reply_to_message
    try:
        target = reply.from_user.id if reply else int(message.command[1])
    except (AttributeError, IndexError, ValueError):
        try:
            target = message.text.split(None, 1)[1]
        except Exception:
            return await message.reply_text("<blockquote><b>Balas pesan pengguna atau berikan id/username</b></blockquote>")

    try:
        user = await client.get_users(target)
    except (errors.PeerIdInvalid, errors.UsernameInvalid, errors.UsernameNotOccupied, ValueError):
        return await message.reply_text("<blockquote><b>Tidak dapat menemukan pengguna tersebut</b></blockquote>")

    ids = user.id
    approved = await _get_list(message.chat.id, "approved_users")
    if ids not in approved:
        return await message.reply_text("<blockquote><b>Pengguna memang belum disetujui</b></blockquote>")
    await _remove_from_list(message.chat.id, "approved_users", ids)
    return await message.reply_text(f"<blockquote><b>Pengguna {user.mention} telah dihapus dari daftar approved</b></blockquote>")


@app.on_message(filters.command(["listwhite", "approved"]) & filters.group)
@AdminActual
async def list_approved(_, message: Message, __):
    approved = await _get_list(message.chat.id, "approved_users")
    if not approved:
        return await message.reply_text("<blockquote><b>Belum ada pengguna yang disetujui</b></blockquote>")
    msg = "<b>Pengguna Approved:</b>\n\n"
    for i, uid in enumerate(approved, 1):
        msg += f"{i}. <code>{uid}</code>\n"
    return await message.reply_text(msg)


@app.on_message(filters.command(["clearwhite", "clearfree", "clearapproved"]) & filters.group)
@AdminActual
async def clear_approved(_, message: Message, __):
    await COL.update_one(_chat_doc_key(message.chat.id), {"$set": {"approved_users": []}}, upsert=True)
    return await message.reply_text("<blockquote><b>Berhasil menghapus semua pengguna approved</b></blockquote>")


# Blacklist (silent) management
@app.on_message(filters.command(["addblack"]) & filters.group)
@AdminActual
async def add_black(client, message: Message, _):
    reply = message.reply_to_message
    try:
        target = reply.from_user.id if reply else int(message.command[1])
    except (AttributeError, IndexError, ValueError):
        try:
            target = message.text.split(None, 1)[1]
        except Exception:
            return await message.reply_text("<blockquote><b>Balas pesan pengguna atau berikan id/username</b></blockquote>")
    try:
        user = await client.get_users(target)
    except (errors.PeerIdInvalid, errors.UsernameInvalid, errors.UsernameNotOccupied, ValueError):
        return await message.reply_text("<blockquote><b>Tidak dapat menemukan pengguna tersebut</b></blockquote>")

    ids = user.id
    if ids in SUDOERS:
        return await message.reply_text("<blockquote><b>Pengguna adalah SUDOERS bot!</b></blockquote>")
    black = await _get_list(message.chat.id, "silent_users")
    if ids in black:
        return await message.reply_text("<blockquote><b>Pengguna sudah diblacklist</b></blockquote>")
    await _add_to_list(message.chat.id, "silent_users", ids)
    # ephemeral feedback
    msg = await message.reply_text(f"<blockquote><b>Pengguna: {ids} ditambahkan ke blacklist</b></blockquote>")
    try:
        await client.delete_messages(message.chat.id, msg.id)
    except Exception:
        pass
    return


@app.on_message(filters.command(["delblack", "unblack"]) & filters.group)
@AdminActual
async def del_black(client, message: Message, _):
    reply = message.reply_to_message
    try:
        target = reply.from_user.id if reply else int(message.command[1])
    except (AttributeError, IndexError, ValueError):
        try:
            target = message.text.split(None, 1)[1]
        except Exception:
            return await message.reply_text("<blockquote><b>Balas pesan pengguna atau berikan id/username</b></blockquote>")
    try:
        user = await client.get_users(target)
    except (errors.PeerIdInvalid, errors.UsernameInvalid, errors.UsernameNotOccupied, ValueError):
        return await message.reply_text("<blockquote><b>Tidak dapat menemukan pengguna tersebut</b></blockquote>")

    ids = user.id
    black = await _get_list(message.chat.id, "silent_users")
    if ids not in black:
        return await message.reply_text("<blockquote><b>User not in blacklist</b></blockquote>")
    await _remove_from_list(message.chat.id, "silent_users", ids)
    msg = await message.reply_text(f"<blockquote><b>Pengguna: {ids} dihapus dari blacklist</b></blockquote>")
    try:
        await client.delete_messages(message.chat.id, msg.id)
    except Exception:
        pass
    return


@app.on_message(filters.command(["listblack"]) & filters.group)
@AdminActual
async def list_black(_, message: Message, __):
    black = await _get_list(message.chat.id, "silent_users")
    if not black:
        return await message.reply_text("<blockquote><b>Belum ada pengguna yang diblacklist</b></blockquote>")
    msg = "<b>Pengguna Blacklist:</b>\n\n"
    for i, uid in enumerate(black, 1):
        msg += f"{i}. <code>{uid}</code>\n"
    return await message.reply_text(msg)


@app.on_message(filters.command(["clearblack"]) & filters.group)
@AdminActual
async def clear_black(_, message: Message, __):
    await COL.update_one(_chat_doc_key(message.chat.id), {"$set": {"silent_users": []}}, upsert=True)
    return await message.reply_text("<blockquote><b>Berhasil menghapus list black pengguna</b></blockquote>")


# Text blacklist
@app.on_message(filters.command(["bl"]) & filters.group)
@AdminActual
async def add_word_blacklist(client, message: Message, _):
    reply = message.reply_to_message
    if reply:
        text = reply.text or reply.caption
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("<blockquote><b>Balas ke pesan atau berikan pesan untuk diblacklist</b></blockquote>")
    if not text:
        return await message.reply_text("<blockquote><b>Pesan tidak memiliki teks untuk diblacklist</b></blockquote>")
    await _add_to_list(message.chat.id, "delete_words", text)
    msg = await message.reply_text(f"<blockquote><b>Kata dimasukkan ke blacklist:\n{text}</b></blockquote>")
    try:
        await client.delete_messages(message.chat.id, msg.id)
    except Exception:
        pass
    return


@app.on_message(filters.command(["unbl"]) & filters.group)
@AdminActual
async def del_word_blacklist(_, message: Message, __):
    reply = message.reply_to_message
    if reply:
        text = reply.text or reply.caption
    elif len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    else:
        return await message.reply_text("<blockquote><b>Balas ke pesan atau berikan pesan untuk dihapus dari blacklist</b></blockquote>")
    if not text:
        return await message.reply_text("<blockquote><b>Pesan tidak memiliki teks untuk dihapus dari blacklist</b></blockquote>")
    current = await _get_list(message.chat.id, "delete_words")
    if text not in current:
        return await message.reply_text("<blockquote><b>Kata tidak ditemukan di blacklist</b></blockquote>")
    await _remove_from_list(message.chat.id, "delete_words", text)
    return await message.reply_text(f"<blockquote><b>Kata dihapus dari blacklist:\n{text}</b></blockquote>")


@app.on_message(filters.command(["listbl"]) & filters.group)
@AdminActual
async def list_word_blacklist(_, message: Message, __):
    words = await _get_list(message.chat.id, "delete_words")
    if not words:
        return await message.reply_text("<blockquote><b>Belum ada pesan yg diblacklist</b></blockquote>")
    msg = "<b>Daftar Blacklist:</b>\n\n"
    for i, w in enumerate(words, 1):
        msg += f"{i}. {w}\n"
    return await message.reply_text(msg)


# Utility: check if user is chat admin (owner or admin)
async def is_chat_admin(client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        # if cannot fetch, default to False (not admin)
        return False


# Core protection: delete messages from blacklisted users or containing blacklisted words,
# and if delete_all is enabled, delete any non-exempt message immediately.
@app.on_message(filters.group & ~filters.bot, group=2)
async def antigcst_handler(client, message: Message):
    try:
        doc = await COL.find_one(_chat_doc_key(message.chat.id))
        if not doc or not doc.get("protect"):
            return
        if message.sender_chat:
            return
        uid = message.from_user.id if message.from_user else None
        if not uid:
            return

        if uid in doc.get("approved_users", []):
            return
        if await is_chat_admin(client, message.chat.id, uid):
            return
        if uid in SUDOERS:
            return

        warn_text = f"<blockquote><b>⚠️ WARN , {message.from_user.mention} Pesan anda telah dihapus karena ANDA JELEK</b></blockquote>"

        async def send_and_delete_warning():
            sent = await client.send_message(
                message.chat.id,
                warn_text,
                reply_to_message_id=message.id
            )
            await asyncio.sleep(5)
            try:
                await client.delete_messages(message.chat.id, sent.id)
            except Exception:
                pass

        if doc.get("delete_all", False):
            try:
                await message.delete()
                await send_and_delete_warning()
            except Exception:
                LOGGER.warning("Failed to delete message in strict mode in chat %s", message.chat.id)
            return

        if uid in doc.get("silent_users", []):
            try:
                await message.delete()
                await send_and_delete_warning()
            except Exception:
                LOGGER.warning("Failed to delete message from blacklisted user in chat %s", message.chat.id)
            return

        text = message.text or message.caption or ""
        for word in doc.get("delete_words", []):
            if word and word.lower() in text.lower():
                try:
                    await message.delete()
                    await send_and_delete_warning()
                except Exception:
                    LOGGER.warning("Failed to delete message containing blacklisted word in chat %s", message.chat.id)
                return
    except Exception as e:
        LOGGER.error("Error in antigcst_handler: %s", e)

__MODULE__ = "Anti-Gcast"
__HELP__ = """
🚫 Anti-Gcast / Anti-Spam protection

• /protect or /antigcast [on|off] – Enable or disable protection.
• /protectmode all on|off or /antigcstmode all on|off – Per-chat strict mode: if 'all' is ON, any non-exempt message will be deleted immediately.
• /antigcstconfig onlyowner|sudooverride|show – OWNER only: manage global toggles.
• /free, /unfree, /listwhite, /clearwhite – Manage whitelist (approved users).
• /addblack, /delblack, /listblack, /clearblack – Manage blacklist (silent users).
• /bl, /unbl, /listbl – Manage text blacklist (messages containing listed phrases will be deleted).

Notes:
- Exemptions from delete_all strict mode: chat admins (owner/admin), approved users (whitelist), and SUDOERS.
- Global only_owner_toggle setting still controls who may toggle protect/mode (OWNER-only when enabled; SUDOERS may be allowed if sudo_override=True).
- Default global config: only_owner_toggle=False, sudo_override=True.
- Collections used: "antigcst" (per-chat), "antigcst_config" (global).
"""
