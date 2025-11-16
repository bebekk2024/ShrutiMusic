# Utility helpers exported for the ShrutiMusic package.
# Provides AdminRightsCheck (async) and seconds_to_min (sync).

from typing import Optional
try:
    # pyrogram imports are only required at runtime when AdminRightsCheck is used
    from pyrogram import Client
    from pyrogram.types import ChatMember
except Exception:
    Client = None  # type: ignore

async def AdminRightsCheck(chat_id: int, user_id: int, client: Optional[Client]) -> bool:
    """
    Check whether a user is an admin/creator in a chat.
    Returns False if the client is not available or on error.
    Usage: await AdminRightsCheck(chat_id, user_id, pyrogram_client)
    """
    if client is None or Client is None:
        return False
    try:
        member = await client.get_chat_member(chat_id, user_id)
        # member.status typically one of: 'creator', 'administrator', 'member', ...
        return getattr(member, "status", "").lower() in ("administrator", "creator")
    except Exception:
        # Don't raise here; plugin code expects a boolean result
        return False

def seconds_to_min(seconds: int) -> str:
    """
    Convert seconds (int) to human-readable minutes:seconds string.
    Example: 125 -> "2:05"
    """
    try:
        s = int(seconds)
    except Exception:
        s = 0
    m = s // 60
    rem = s % 60
    return f"{m}:{rem:02d}"

__all__ = ["AdminRightsCheck", "seconds_to_min"]
