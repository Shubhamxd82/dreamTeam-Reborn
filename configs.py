# (c) @Shubhlinks — Enhanced by Feature Upgrade V2

import os


class Config(object):
    # ==================== CORE CONFIG ====================
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
    DB_CHANNEL = int(os.environ.get("DB_CHANNEL", "0"))
    BOT_OWNER = int(os.environ.get("BOT_OWNER", "0"))
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL", None)

    # FIX: Safe parsing for BANNED_USERS — won't crash on empty string
    _banned_raw = os.environ.get("BANNED_USERS", "").strip()
    BANNED_USERS = set(int(x) for x in _banned_raw.split() if x.isdigit()) if _banned_raw else set()

    _banned_chats_raw = os.environ.get("BANNED_CHAT_IDS", "").strip()
    BANNED_CHAT_IDS = list(set(int(x) for x in _banned_chats_raw.split() if x.lstrip('-').isdigit())) if _banned_chats_raw else []

    # FIX: Proper boolean parsing — "False" string now correctly becomes False
    FORWARD_AS_COPY = os.environ.get("FORWARD_AS_COPY", "True").lower() in ("true", "1", "yes")
    BROADCAST_AS_COPY = os.environ.get("BROADCAST_AS_COPY", "False").lower() in ("true", "1", "yes")
    OTHER_USERS_CAN_SAVE_FILE = os.environ.get("OTHER_USERS_CAN_SAVE_FILE", "True").lower() in ("true", "1", "yes")

    # ==================== FEATURE 1: AUTO-DELETE ====================
    AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "600"))
    AUTO_DELETE_MSG = os.environ.get(
        "AUTO_DELETE_MSG",
        "⚠️ <b>This file will be auto-deleted in <u>{time}</u>.</b>\n\n📌 Please save/forward it before deletion!"
    )
    AUTO_DELETE_FINAL_MSG = os.environ.get(
        "AUTO_DELETE_FINAL_MSG",
        "✅ File was auto-deleted to prevent copyright issues.\n\n🔁 Click the link again to re-download."
    )

    # ==================== FEATURE 2: CUSTOM CAPTION ====================
    CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
    if CUSTOM_CAPTION is not None and CUSTOM_CAPTION.strip() == "":
        CUSTOM_CAPTION = None

    # ==================== FEATURE 3: CUSTOM START MESSAGE WITH IMAGE ====================
    START_PIC = os.environ.get("START_PIC", "").strip()

    # ==================== FEATURE 4: DISABLE CHANNEL BUTTON ====================
    DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False").lower() in ("true", "1", "yes")

    # ==================== FEATURE 5: MULTIPLE FORCE SUB ====================
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "").strip()
    FORCE_SUB_CHANNEL_2 = os.environ.get("FORCE_SUB_CHANNEL_2", "").strip()
    FORCE_SUB_CHANNEL_3 = os.environ.get("FORCE_SUB_CHANNEL_3", "").strip()
    FORCE_SUB_CHANNEL_4 = os.environ.get("FORCE_SUB_CHANNEL_4", "").strip()

    @classmethod
    def get_force_sub_channels(cls):
        """Returns a list of all configured force sub channel IDs."""
        channels = []
        for ch_str in [cls.UPDATES_CHANNEL, cls.FORCE_SUB_CHANNEL_2,
                       cls.FORCE_SUB_CHANNEL_3, cls.FORCE_SUB_CHANNEL_4]:
            if ch_str and ch_str.strip():
                try:
                    channels.append(int(ch_str))
                except ValueError:
                    channels.append(ch_str)
        return channels

    # ==================== FEATURE 6: URL SHORTENER ====================
    URL_SHORTENER = os.environ.get("URL_SHORTENER", "False").lower() in ("true", "1", "yes")
    URL_SHORTENER_API = os.environ.get("URL_SHORTENER_API", "").strip()
    URL_SHORTENER_WEBSITE = os.environ.get("URL_SHORTENER_WEBSITE", "").strip()

    # ==================== FEATURE 7: TOKEN/VERIFY SYSTEM ====================
    TOKEN_VERIFICATION = os.environ.get("TOKEN_VERIFICATION", "False").lower() in ("true", "1", "yes")
    TOKEN_TIMEOUT = int(os.environ.get("TOKEN_TIMEOUT", "7200"))
    TOKEN_SHORTENER_API = os.environ.get("TOKEN_SHORTENER_API", "").strip()
    TOKEN_SHORTENER_WEBSITE = os.environ.get("TOKEN_SHORTENER_WEBSITE", "").strip()

    # ==================== FEATURE 8: PROTECT CONTENT ====================
    PROTECT_CONTENT = os.environ.get("PROTECT_CONTENT", "False").lower() in ("true", "1", "yes")

    # ==================== FEATURE 9: ADMIN PANEL ====================
    _admins_raw = os.environ.get("ADMINS", "").strip()
    ADMINS = list(set(
        [int(os.environ.get("BOT_OWNER", "0"))] +
        [int(x) for x in _admins_raw.split() if x.isdigit()]
    ))

    # ==================== FEATURE 10: STREAM/DOWNLOAD LINK ====================
    STREAM_ENABLED = os.environ.get("STREAM_ENABLED", "False").lower() in ("true", "1", "yes")
    STREAM_PORT = int(os.environ.get("STREAM_PORT", "8080"))
    STREAM_FQDN = os.environ.get("STREAM_FQDN", "").strip()
    STREAM_USE_HTTPS = os.environ.get("STREAM_USE_HTTPS", "True").lower() in ("true", "1", "yes")

    @classmethod
    def get_stream_base_url(cls):
        protocol = "https" if cls.STREAM_USE_HTTPS else "http"
        if cls.STREAM_FQDN:
            return f"{protocol}://{cls.STREAM_FQDN}"
        return f"http://0.0.0.0:{cls.STREAM_PORT}"

    # ==================== FEATURE 11: CLONE BOT ====================
    CLONE_ENABLED = os.environ.get("CLONE_ENABLED", "False").lower() in ("true", "1", "yes")

    # ==================== FEATURE 12: MULTI-LANGUAGE ====================
    DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "en").strip().lower()

    # ==================== WORKER URL ====================
    WORKER_URL = os.environ.get("WORKER_URL", "").strip()

    # ==================== FILE SERVE BOT ====================
    # Dedicated bot for serving files — swap token if banned without breaking any links
    SERVE_BOT_TOKEN = os.environ.get("SERVE_BOT_TOKEN", "").strip()
    SERVE_BOT_USERNAME = os.environ.get("SERVE_BOT_USERNAME", "").strip()

    # ==================== TEXT TEMPLATES ====================
    ABOUT_BOT_TEXT = f"""
Hello, I'm a Permanent File Store Bot.

╭────[ **🔅Bot Info🔅** ]────⍟
│
├🔸🤖 **My Name:** [𝐅𝐢𝐥𝐞 𝐒𝐭𝐨𝐫𝐞](https://t.me/{BOT_USERNAME})
│
├🔸📝 **Language:** [𝐏𝐲𝐭𝐡𝐨𝐧𝟑](https://www.python.org)
│
├🔹📚 **Library:** [𝐏𝐲𝐫𝐨𝐠𝐫𝐚𝐦](https://docs.pyrogram.org)
│
╰──────[ 😎 ]───────────⍟
"""

    ABOUT_DEV_TEXT = """
🧑🏻‍💻 **𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿:** [【﻿Dengerous】](https://t.me/Dengerous53)

**@Nexus_Shubhu**
"""

    HOME_TEXT = """
Hello, [{}](tg://user?id={})\n\nThis is a Permanent **FileStore Bot**.

📢 Send me any File & I'll store it and give you a permanent link.

⚠️ If bot gets banned, your links still work with the new bot!

❌ **PORNOGRAPHY CONTENTS** are strictly prohibited.
"""

    FORCE_SUB_TEXT = """
**Please Join My Update Channel(s) to use this Bot!**

Due to overload, only channel subscribers can use this Bot!
"""
