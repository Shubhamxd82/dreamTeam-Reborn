# (c) @harshil8981 — Enhanced by Feature Upgrade V2

import os


class Config(object):
    # ==================== CORE CONFIG ====================
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    BOT_USERNAME = os.environ.get("BOT_USERNAME")
    DB_CHANNEL = int(os.environ.get("DB_CHANNEL", "-100"))
    BOT_OWNER = int(os.environ.get("BOT_OWNER", "1445283714"))
    DATABASE_URL = os.environ.get("DATABASE_URL")
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL", None)

    BANNED_USERS = set(int(x) for x in os.environ.get("BANNED_USERS", "").split()) if os.environ.get("BANNED_USERS") else set()
    BANNED_CHAT_IDS = list(set(int(x) for x in os.environ.get("BANNED_CHAT_IDS", "").split())) if os.environ.get("BANNED_CHAT_IDS") else []

    FORWARD_AS_COPY = bool(os.environ.get("FORWARD_AS_COPY", True))
    BROADCAST_AS_COPY = bool(os.environ.get("BROADCAST_AS_COPY", False))
    OTHER_USERS_CAN_SAVE_FILE = bool(os.environ.get("OTHER_USERS_CAN_SAVE_FILE", True))

    # ==================== FEATURE 1: AUTO-DELETE ====================
    # Time in seconds after which files will be auto-deleted (0 = disabled)
    AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "600"))  # Default: 10 minutes
    AUTO_DELETE_MSG = os.environ.get(
        "AUTO_DELETE_MSG",
        "⚠️ <b>This file will be auto-deleted in <u>{time}</u>.</b>\n\n📌 Please save/forward it before deletion!"
    )
    AUTO_DELETE_FINAL_MSG = os.environ.get(
        "AUTO_DELETE_FINAL_MSG",
        "✅ File was auto-deleted to prevent copyright issues.\n\n🔁 Click the link again to re-download."
    )

    # ==================== FEATURE 2: CUSTOM CAPTION ====================
    # Use variables: {filename}, {filesize}, {caption}, {mention}, {username}
    # Set to empty string "" or None to keep original caption
    CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
    # Example: "📁 {filename}\n💾 Size: {filesize}\n\n📢 @YourChannel"

    # ==================== FEATURE 3: CUSTOM START MESSAGE WITH IMAGE ====================
    START_PIC = os.environ.get("START_PIC", "")  # URL of start image/photo
    # If empty, no photo is sent with start message

    # ==================== FEATURE 4: DISABLE CHANNEL BUTTON ====================
    # If True, channel file edits will NOT include a share button
    DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"

    # ==================== FEATURE 5: MULTIPLE FORCE SUB ====================
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "")
    FORCE_SUB_CHANNEL_2 = os.environ.get("FORCE_SUB_CHANNEL_2", "")
    FORCE_SUB_CHANNEL_3 = os.environ.get("FORCE_SUB_CHANNEL_3", "")
    FORCE_SUB_CHANNEL_4 = os.environ.get("FORCE_SUB_CHANNEL_4", "")

    @classmethod
    def get_force_sub_channels(cls):
        """Returns a list of all configured force sub channel IDs."""
        channels = []
        for ch_str in [cls.UPDATES_CHANNEL, cls.FORCE_SUB_CHANNEL_2,
                       cls.FORCE_SUB_CHANNEL_3, cls.FORCE_SUB_CHANNEL_4]:
            if ch_str and ch_str.strip():
                try:
                    channels.append(int(ch_str) if ch_str.startswith("-") else ch_str)
                except ValueError:
                    channels.append(ch_str)
        return channels

    # ==================== FEATURE 6: URL SHORTENER ====================
    URL_SHORTENER = os.environ.get("URL_SHORTENER", "False").lower() == "true"
    URL_SHORTENER_API = os.environ.get("URL_SHORTENER_API", "")  # API key
    URL_SHORTENER_WEBSITE = os.environ.get("URL_SHORTENER_WEBSITE", "")
    # Supported: gplinks.co, shrinkme.io, shorturllink.in, etc.
    # Example: URL_SHORTENER_WEBSITE=gplinks.co  URL_SHORTENER_API=your_api_key

    # ==================== FEATURE 7: TOKEN/VERIFY SYSTEM ====================
    TOKEN_VERIFICATION = os.environ.get("TOKEN_VERIFICATION", "False").lower() == "true"
    TOKEN_TIMEOUT = int(os.environ.get("TOKEN_TIMEOUT", "7200"))  # Token validity in seconds (default 2hr)
    TOKEN_SHORTENER_API = os.environ.get("TOKEN_SHORTENER_API", "")  # Can be same as URL_SHORTENER_API
    TOKEN_SHORTENER_WEBSITE = os.environ.get("TOKEN_SHORTENER_WEBSITE", "")
    # Users must verify via short link before accessing files

    # ==================== FEATURE 8: PROTECT CONTENT ====================
    PROTECT_CONTENT = os.environ.get("PROTECT_CONTENT", "False").lower() == "true"
    # If True, files sent to users cannot be forwarded/saved

    # ==================== FEATURE 9: ADMIN PANEL (MULTI-ADMIN) ====================
    # Space-separated list of admin user IDs (in addition to BOT_OWNER)
    ADMINS = list(set(
        [BOT_OWNER] +
        [int(x) for x in os.environ.get("ADMINS", "").split() if x.isdigit()]
    ))

    # ==================== FEATURE 10: STREAM/DOWNLOAD LINK ====================
    STREAM_ENABLED = os.environ.get("STREAM_ENABLED", "False").lower() == "true"
    STREAM_PORT = int(os.environ.get("STREAM_PORT", "8080"))
    STREAM_FQDN = os.environ.get("STREAM_FQDN", "")  # Your domain, e.g. yourapp.koyeb.app
    STREAM_USE_HTTPS = os.environ.get("STREAM_USE_HTTPS", "True").lower() == "true"

    @classmethod
    def get_stream_base_url(cls):
        protocol = "https" if cls.STREAM_USE_HTTPS else "http"
        if cls.STREAM_FQDN:
            return f"{protocol}://{cls.STREAM_FQDN}"
        return f"http://0.0.0.0:{cls.STREAM_PORT}"

    # ==================== FEATURE 11: CLONE BOT ====================
    CLONE_ENABLED = os.environ.get("CLONE_ENABLED", "False").lower() == "true"
    # Allows users to create clones using /clone command

    # ==================== FEATURE 12: MULTI-LANGUAGE ====================
    DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "en")  # en, hi, es, fr, ar, pt, id, tr

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

    ABOUT_DEV_TEXT = f"""
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
