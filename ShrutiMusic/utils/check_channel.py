from pyrogram.errors import UserNotParticipant, UserBannedInChannel

async def is_joined_channel(client, user_id, channel_username):
    try:
        member = await client.get_chat_member(channel_username, user_id)
        if member.status in ("member", "administrator", "creator"):
            return True
        else:
            return False
    except UserNotParticipant:
        return False
    except UserBannedInChannel:
        return False
    except Exception:
        return False
