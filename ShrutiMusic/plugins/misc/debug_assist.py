# Run this from your project root where the ShrutiMusic package is importable.
import asyncio

async def main():
    try:
        from ShrutiMusic import userbot, get_userbot
        from ShrutiMusic.utils import database as dbmod
        print("userbot.one:", getattr(userbot, "one", None))
        try:
            print("get_userbot():", get_userbot())
        except Exception as e:
            print("get_userbot() raised:", e)
        print("assistantdict keys:", list(dbmod.assistantdict.keys())[:20])
        import importlib
        mod = importlib.import_module("ShrutiMusic.core.userbot")
        print("assistants:", getattr(mod, "assistants", None))
    except Exception as e:
        print("Debug failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
