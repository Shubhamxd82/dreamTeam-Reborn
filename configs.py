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

    _banned_raw = os.environ.get("BANNED_USERS", "").strip()
    BANNED_USERS = set(int(x) for x in _banned_raw.split() if x.isdigit()) if _banned_raw else set()

    _banned_chats_raw = os.environ.get("BANNED_CHAT_IDS", "").strip()
    BANNED_CHAT_IDS = list(set(int(x) for x in _banned_chats_raw.split() if x.lstrip('-').isdigit())) if _banned_chats_raw else []

    FORWARD_AS_COPY = os.environ.get("FORWARD_AS_COPY", "True").lower() in ("true", "1", "yes")
    BROADCAST_AS_COPY = os.environ.get("BROADCAST_AS_COPY", "False").lower() in ("true", "1", "yes")
    OTHER_USERS_CAN_SAVE_FILE = os.environ.get("OTHER_USERS_CAN_SAVE_FILE", "True").lower() in ("true", "1", "yes")

    # ==================== FEATURE 1: AUTO-DELETE ====================
    AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "600"))
    AUTO_DELETE_MSG = os.environ.get(
        "AUTO_DELETE_MSG",
        "⚠️ <b>Due To Copyright This file will deleted after <u>{time}</u>.</b>\n\n📌 Please save/forward it before download!"
    )
    AUTO_DELETE_FINAL_MSG = os.environ.get(
        "AUTO_DELETE_FINAL_MSG",
        "✅ File was auto-deleted to prevent copyright.\n\n©️ <b>Powered by @Moviesss4ers 🏆.</b>"
    )

    # ==================== FEATURE 2: CUSTOM CAPTION ====================
    CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
    if CUSTOM_CAPTION is not None and CUSTOM_CAPTION.strip() == "":
        CUSTOM_CAPTION = None

    # ==================== FEATURE 3: START PIC ====================
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

    # ==================== LINK SECRET KEY ====================
    # Used to encrypt/decrypt file links — makes every link look completely random
    # Must be same in Koyeb env vars AND worker.js
    LINK_SECRET_KEY = os.environ.get("LINK_SECRET_KEY", "Mv4eRs26").strip()

    # ==================== TEXT TEMPLATES ====================
    ABOUT_BOT_TEXT = f"""
Hello, I'm Ryan Gosling - I Drive.
AS i Said, Send me any File & It will be uploaded in My Database & You will Get the File Link Which **Never Expires**. 

╭────[ **🔅Literally Me🔅**]────⍟
│
├🔸🤖 **My Name:** [𝐖𝐨𝐧𝐝𝐞𝐫 𝐌𝐚𝐧](https://t.me/{BOT_USERNAME})
│
├🔸📝 **Language:** [𝐏𝐲𝐭𝐡𝐨𝐧𝟑](https://www.python.org)
│
├🔹📚 **Library:** [𝐏𝐲𝐫𝐨𝐠𝐫𝐚𝐦](https://docs.pyrogram.org)
│
├🔹📡 **Hosted On:** [𝐕𝐏𝐒](http://vultr.com/)
│
├🔸👨‍💻 **Owner:** [𝐒𝐡𝐮𝐛𝐡𝐚𝐦](https://t.me/Nexus_Shubhu) 
│
├🔹📡 **Secured By:** [𝐂𝐥𝐨𝐮𝐝𝐟𝐥𝐚𝐫𝐞](https://workers.cloudflare.com/)
│
├🔹©️ **Powered By:** [𝐌𝐨𝐯𝐢𝐞𝐬𝐬𝐬𝟒𝐞𝐫𝐬](https://t.me/Moviesss4ers)
│
╰──────[ 😎 ]───────────⍟
"""
    ABOUT_DEV_TEXT = f"""
🧑🏻‍💻 **𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿:** [【﻿Dengerous】](https://t.me/Dengerous53) 

𝐃𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫 𝐢𝐬 𝐒𝐮𝐩𝐞𝐫 𝐍𝐨𝐨𝐛. 𝐉𝐮𝐬𝐭 𝐋𝐞𝐚𝐫𝐧𝐢𝐧𝐠 𝐟𝐫𝐨𝐦 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥 𝐃𝐨𝐜𝐬. 𝐀𝐧𝐝 𝐒𝐞𝐞𝐤𝐢𝐧𝐠 𝐇𝐞𝐥𝐩 𝐅𝐫𝐨𝐦 𝐏𝐫𝐨 𝐂𝐨𝐝𝐞𝐫𝐬\n**@Nexus_Shubhu**

𝐀𝐥𝐬𝐨 𝐫𝐞𝐦𝐞𝐦𝐛𝐞𝐫 𝐭𝐡𝐚𝐭 𝐝𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫 𝐰𝐢𝐥𝐥 𝐃𝐞𝐥𝐞𝐭𝐞 𝐀𝐝𝐮𝐥𝐭 𝐂𝐨𝐧𝐭𝐞𝐧𝐭𝐬 𝐟𝐫𝐨𝐦 𝐃𝐚𝐭𝐚𝐛𝐚𝐬𝐞. 𝐒𝐨 𝐛𝐞𝐭𝐭𝐞𝐫 𝐝𝐨𝐧'𝐭 𝐒𝐭𝐨𝐫𝐞 𝐓𝐡𝐨𝐬𝐞 𝐊𝐢𝐧𝐝 𝐨𝐟 𝐓𝐡𝐢𝐧𝐠𝐬.

"""
    HOME_TEXT = """
Hello, [{}](tg://user?id={})\n\nThis is a Literally Permanent **FileStore Bot**.

How to Use Bot & it's Benefits??

📢 Send me any File & It will be uploaded in My Database & You will Get the File Link Which Never Expires.

⚠️ **Benefits**: If you have a TeleGram Movie Channel or Any Copyright Channel, Then Its Useful for Daily Usage, You can Send Me Your File & I will Send Permanent Link to You & Channel will be Safe from **CopyRight Infringement** Issue.

🗣️ **For Example**: If Bot Get Banned & Deleted, Your All Links will Redirect to New Bot & All Files Are Still Accessable, Dont Worry You Don't have to Make any Changes Anywhere Because We Do 😎

❌ **PORNOGRAPHY CONTENTS** are strictly prohibited & get Permanent Ban.
"""

    FORCE_SUB_TEXT = """
**Please Join My Update Channel(s) to use this Bot!**

Due to overload, only channel subscribers can use this Bot!
"""
