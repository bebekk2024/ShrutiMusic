from pyrogram.errors import UserNotParticipant, UserBannedInChannel

async def is_joined_channel(client, user_id, support_channel):
    try:
        print(f"Checking {user_id} in {support_channel}")
        member = await client.get_chat_member(support_channel, user_id)
        print(f"Status: {member.status}")
        if member.status in ("member", "administrator", "creator"):
            return True
        else:
            return False
    except UserNotParticipant:
        print("UserNotParticipant")
        return False
    except UserBannedInChannel:
        print("UserBannedInChannel")
        return False
    except Exception as e:
        print(f"Other Error: {e}")
        return False
