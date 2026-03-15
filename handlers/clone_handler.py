# Clone Bot Feature — Feature 11

import asyncio
import logging
from binascii import Error
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from configs import Config
from handlers.database import db
from handlers.languages import get_text, get_all_lang_codes, get_lang_name
from handlers.helpers import str_to_b64, b64_to_str

logging.basicConfig(level=logging.INFO)

# Active clone bot instances: {user_id: Client}
clone_bots = {}

# Tracks users waiting to send text/photo input for /mybot settings
# Format: {user_id: 'action_name'}
pending_mybot = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def tick(val) -> str:
    return "✅" if val else "❌"


async def build_mybot_menu(user_id: int) -> tuple:
    """Build the /mybot settings menu."""
    clone = await db.get_clone(user_id)
    if not clone:
        return None, None

    username = clone.get('bot_username', 'Unknown')
    settings = clone.get('settings', {})

    start_pic = settings.get('start_pic')
    start_msg = settings.get('start_msg')
    caption = settings.get('custom_caption')
    backup_ch = settings.get('backup_channel')
    lang = settings.get('language', Config.DEFAULT_LANGUAGE)
    lang_name = get_lang_name(lang)

    text = (
        f"🤖 **Clone Bot Settings** (@{username})\n\n"
        f"◆ Start Photo: {tick(bool(start_pic))}\n"
        f"◆ Start Message: {tick(bool(start_msg))}\n"
        f"◆ Custom Caption: {tick(bool(caption))}\n"
        f"◆ Backup Channel: {tick(bool(backup_ch))}\n"
        f"◆ Language: `{lang_name}`\n\n"
        "Tap a button to configure."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🖼 Start Photo {tick(bool(start_pic))}", callback_data="mybot_startpic_menu"),
            InlineKeyboardButton(f"📝 Start Message {tick(bool(start_msg))}", callback_data="mybot_startmsg_menu"),
        ],
        [
            InlineKeyboardButton(f"✍️ Caption {tick(bool(caption))}", callback_data="mybot_caption_menu"),
            InlineKeyboardButton(f"📢 Backup Channel {tick(bool(backup_ch))}", callback_data="mybot_backup_menu"),
        ],
        [
            InlineKeyboardButton(f"🌐 Language ({lang_name})", callback_data="mybot_lang_menu"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="mybot_close")],
    ])

    return text, keyboard


# ── /mybot command ─────────────────────────────────────────────────────────────

async def mybot_handler(bot: Client, m: Message):
    """Handle /mybot command — shows clone bot settings menu."""
    clone = await db.get_clone(m.from_user.id)
    if not clone:
        await m.reply_text(
            "❌ You don't have an active clone bot!\n\n"
            "Use /clone to create one first.",
            quote=True
        )
        return

    text, keyboard = await build_mybot_menu(m.from_user.id)
    await m.reply_text(text, reply_markup=keyboard, quote=True)


# ── /mybot callback handler ────────────────────────────────────────────────────

async def mybot_callback(bot: Client, cmd: CallbackQuery):
    """Handle all mybot_ prefixed callbacks."""
    cb = cmd.data
    user_id = cmd.from_user.id

    # Verify user has a clone
    clone = await db.get_clone(user_id)
    if not clone:
        await cmd.answer("❌ No active clone bot found!", show_alert=True)
        return

    if cb == "mybot_main":
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    elif cb == "mybot_close":
        try:
            await cmd.message.delete()
        except Exception:
            pass

    # ── Start Photo ──
    elif cb == "mybot_startpic_menu":
        start_pic = await db.get_clone_setting(user_id, 'start_pic')
        await cmd.message.edit(
            f"🖼 **Start Photo**\n\nCurrent: {tick(bool(start_pic))}\n\n"
            "Send a photo to set as start photo, or remove the existing one.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Set Photo", callback_data="mybot_startpic_set")],
                [InlineKeyboardButton("🗑 Remove Photo", callback_data="mybot_startpic_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_startpic_set":
        pending_mybot[user_id] = 'start_pic'
        await cmd.message.edit(
            "🖼 **Set Start Photo**\n\n"
            "Send me a **photo** to use as the start image.\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="mybot_startpic_menu")]
            ])
        )

    elif cb == "mybot_startpic_clear":
        await db.update_clone_settings(user_id, {'start_pic': None})
        await cmd.answer("✅ Start photo removed!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Start Message ──
    elif cb == "mybot_startmsg_menu":
        start_msg = await db.get_clone_setting(user_id, 'start_msg')
        preview = f"`{start_msg[:80]}...`" if start_msg and len(start_msg) > 80 else (f"`{start_msg}`" if start_msg else "Not set")
        await cmd.message.edit(
            f"📝 **Start Message**\n\nCurrent: {preview}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Message", callback_data="mybot_startmsg_set")],
                [InlineKeyboardButton("🗑 Remove Message", callback_data="mybot_startmsg_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_startmsg_set":
        pending_mybot[user_id] = 'start_msg'
        await cmd.message.edit(
            "📝 **Set Start Message**\n\n"
            "Send me the start message text.\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="mybot_startmsg_menu")]
            ])
        )

    elif cb == "mybot_startmsg_clear":
        await db.update_clone_settings(user_id, {'start_msg': None})
        await cmd.answer("✅ Start message removed!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Custom Caption ──
    elif cb == "mybot_caption_menu":
        caption = await db.get_clone_setting(user_id, 'custom_caption')
        preview = f"`{caption[:80]}...`" if caption and len(caption) > 80 else (f"`{caption}`" if caption else "Not set")
        await cmd.message.edit(
            f"✍️ **Custom Caption**\n\nCurrent: {preview}\n\n"
            "Variables: `{{filename}}` `{{filesize}}` `{{caption}}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Caption", callback_data="mybot_caption_set")],
                [InlineKeyboardButton("🗑 Clear Caption", callback_data="mybot_caption_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_caption_set":
        pending_mybot[user_id] = 'custom_caption'
        await cmd.message.edit(
            "✍️ **Set Custom Caption**\n\n"
            "Send your caption text.\n"
            "Variables: `{{filename}}` `{{filesize}}` `{{caption}}`\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="mybot_caption_menu")]
            ])
        )

    elif cb == "mybot_caption_clear":
        await db.update_clone_settings(user_id, {'custom_caption': None})
        await cmd.answer("✅ Caption cleared!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Backup Channel ──
    elif cb == "mybot_backup_menu":
        backup_ch = await db.get_clone_setting(user_id, 'backup_channel')
        await cmd.message.edit(
            f"📢 **Backup Channel Button**\n\nCurrent: `{backup_ch or 'Not set'}`\n\n"
            "When set, a backup channel button appears alongside stream/download buttons when files are sent.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Channel", callback_data="mybot_backup_set")],
                [InlineKeyboardButton("🗑 Remove Channel", callback_data="mybot_backup_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_backup_set":
        pending_mybot[user_id] = 'backup_channel'
        await cmd.message.edit(
            "📢 **Set Backup Channel**\n\n"
            "Send the channel URL.\nExample: `https://t.me/MyChannel`\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="mybot_backup_menu")]
            ])
        )

    elif cb == "mybot_backup_clear":
        await db.update_clone_settings(user_id, {'backup_channel': None})
        await cmd.answer("✅ Backup channel removed!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Language ──
    elif cb == "mybot_lang_menu":
        current_lang = await db.get_clone_setting(user_id, 'language', Config.DEFAULT_LANGUAGE)
        buttons = []
        row = []
        for lang_code in get_all_lang_codes():
            marker = "✅ " if lang_code == current_lang else ""
            row.append(InlineKeyboardButton(
                f"{marker}{get_lang_name(lang_code)}",
                callback_data=f"mybot_lang_set_{lang_code}"
            ))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("« Back", callback_data="mybot_main")])
        await cmd.message.edit(
            "🌐 **Select Language for Clone Bot**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif cb.startswith("mybot_lang_set_"):
        lang_code = cb.replace("mybot_lang_set_", "")
        await db.update_clone_settings(user_id, {'language': lang_code})
        lang_name = get_lang_name(lang_code)
        await cmd.answer(f"✅ Language set to {lang_name}!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    try:
        await cmd.answer()
    except Exception:
        pass


# ── Text/Photo input handler ───────────────────────────────────────────────────

async def handle_mybot_input(bot: Client, m: Message) -> bool:
    """
    Called from bot.py group=0 handler.
    Handles text/photo input for pending /mybot settings.
    Returns True if consumed, False otherwise.
    """
    user_id = m.from_user.id

    if user_id not in pending_mybot:
        return False

    # /cancel aborts
    if m.text and m.text.strip() == "/cancel":
        pending_mybot.pop(user_id, None)
        text, keyboard = await build_mybot_menu(user_id)
        if text:
            await m.reply_text(text, reply_markup=keyboard, quote=True)
        return True

    action = pending_mybot.pop(user_id, None)

    if action == 'start_pic':
        if m.photo:
            file_id = m.photo.file_id
            await db.update_clone_settings(user_id, {'start_pic': file_id})
            await m.reply_text("✅ Start photo saved!", quote=True)
        else:
            await m.reply_text("❌ Please send a **photo**, not text.", quote=True)
            pending_mybot[user_id] = 'start_pic'
            return True

    elif action == 'start_msg':
        text_val = m.text.strip() if m.text else None
        if text_val:
            await db.update_clone_settings(user_id, {'start_msg': text_val})
            await m.reply_text("✅ Start message saved!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send text.", quote=True)

    elif action == 'custom_caption':
        caption_val = m.text.strip() if m.text else None
        if caption_val:
            await db.update_clone_settings(user_id, {'custom_caption': caption_val})
            await m.reply_text("✅ Custom caption saved!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send text.", quote=True)

    elif action == 'backup_channel':
        channel_val = m.text.strip() if m.text else None
        if channel_val:
            await db.update_clone_settings(user_id, {'backup_channel': channel_val})
            await m.reply_text(f"✅ Backup channel set to `{channel_val}`!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send channel URL.", quote=True)

    # Show menu again
    text, keyboard = await build_mybot_menu(user_id)
    if text:
        await m.reply_text(text, reply_markup=keyboard, quote=True)
    return True


# ── Start a clone bot instance ─────────────────────────────────────────────────

async def start_clone_bot(user_id: int, bot_token: str, db_channel: int) -> tuple:
    """Start a clone bot instance. Returns (success, username_or_error)."""
    try:
        clone = Client(
            name=f"clone_{user_id}",
            bot_token=bot_token,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            in_memory=True
        )

        @clone.on_message(filters.command("start") & filters.private)
        async def clone_start(bot, cmd):
            # Read settings fresh from DB
            clone_data = await db.get_clone(user_id)
            settings = clone_data.get('settings', {}) if clone_data else {}

            start_pic = settings.get('start_pic')
            start_msg = settings.get('start_msg')
            backup_ch = settings.get('backup_channel')

            # ── Check for file parameter (mrkiller_XXXX) ──────────────────────
            raw_text = cmd.text.strip()
            start_param = raw_text.split(None, 1)[1] if len(raw_text.split()) > 1 else ""

            if start_param:
                # Decode the file ID and send the file
                try:
                    if start_param.startswith("mrkiller_"):
                        encoded_part = start_param.split("mrkiller_", 1)[1]
                    else:
                        encoded_part = start_param

                    try:
                        file_id = int(b64_to_str(encoded_part))
                    except (Error, UnicodeDecodeError, ValueError):
                        file_id = int(encoded_part)

                    # Get the file message from this clone's DB channel
                    get_msg = await bot.get_messages(
                        chat_id=db_channel,
                        message_ids=file_id
                    )

                    if not get_msg:
                        await cmd.reply_text("❌ File not found!", quote=True)
                        return

                    # Batch support: message may contain multiple IDs as text
                    message_ids = []
                    if get_msg.text:
                        message_ids = [mid.strip() for mid in get_msg.text.split() if mid.strip()]
                    elif get_msg.media:
                        message_ids = [str(file_id)]
                    else:
                        await cmd.reply_text("❌ File not found!", quote=True)
                        return

                    custom_caption = settings.get('custom_caption')
                    me = await bot.get_me()

                    for mid in message_ids:
                        try:
                            mid_int = int(mid)
                            file_msg = await bot.get_messages(
                                chat_id=db_channel,
                                message_ids=mid_int
                            )
                            if not file_msg or not file_msg.media:
                                continue

                            # Build caption
                            if custom_caption:
                                media = file_msg.document or file_msg.video or file_msg.audio
                                filename = getattr(media, 'file_name', 'file') if media else 'file'
                                filesize = getattr(media, 'file_size', 0) if media else 0
                                try:
                                    from handlers.helpers import humanbytes
                                    caption_text = custom_caption.format(
                                        filename=filename,
                                        filesize=humanbytes(filesize),
                                        caption=getattr(file_msg, 'caption', '') or ''
                                    )
                                except Exception:
                                    caption_text = custom_caption
                            else:
                                caption_text = None

                            # Build buttons: stream/download + backup channel
                            file_buttons = []
                            if Config.STREAM_ENABLED and Config.STREAM_FQDN:
                                try:
                                    from handlers.stream_handler import get_stream_link, get_download_link
                                    file_buttons.append([
                                        InlineKeyboardButton("▶️ Stream", url=get_stream_link(mid_int)),
                                        InlineKeyboardButton("📥 Download", url=get_download_link(mid_int))
                                    ])
                                except Exception:
                                    pass
                            if backup_ch:
                                file_buttons.append([InlineKeyboardButton("📢 Backup Channel", url=backup_ch)])

                            markup = InlineKeyboardMarkup(file_buttons) if file_buttons else None

                            await bot.copy_message(
                                chat_id=cmd.from_user.id,
                                from_chat_id=db_channel,
                                message_id=mid_int,
                                caption=caption_text,
                                reply_markup=markup
                            )
                        except Exception as e:
                            logging.error(f"Clone batch send error for {mid}: {e}")
                            continue
                    return

                except Exception as e:
                    logging.error(f"Clone file send error: {e}")
                    await cmd.reply_text(f"❌ Error retrieving file: `{e}`", quote=True)
                    return

            # ── No file param — show welcome message ──────────────────────────
            default_msg = (
                f"Hello! I'm a clone of @{Config.BOT_USERNAME}.\n\n"
                "Send me any file and I'll give you a permanent link!"
            )
            message_text = start_msg if start_msg else default_msg

            buttons = []
            if backup_ch:
                buttons.append([InlineKeyboardButton("📢 Backup Channel", url=backup_ch)])
            buttons.append([InlineKeyboardButton("Original Bot", url=f"https://t.me/{Config.BOT_USERNAME}")])

            markup = InlineKeyboardMarkup(buttons)

            if start_pic:
                try:
                    await cmd.reply_photo(
                        photo=start_pic,
                        caption=message_text,
                        reply_markup=markup
                    )
                    return
                except Exception:
                    pass

            await cmd.reply_text(message_text, reply_markup=markup)

        @clone.on_message((filters.document | filters.video | filters.audio) & filters.private)
        async def clone_save(bot, message):
            try:
                # Read settings fresh from DB
                clone_data = await db.get_clone(user_id)
                settings = clone_data.get('settings', {}) if clone_data else {}
                custom_caption = settings.get('custom_caption')
                backup_ch = settings.get('backup_channel')

                forwarded = await message.forward(db_channel)
                file_id_str = str(forwarded.id)
                me = await bot.get_me()
                share_link = f"https://t.me/{me.username}?start=mrkiller_{str_to_b64(file_id_str)}"

                # Build caption
                if custom_caption:
                    media = message.document or message.video or message.audio
                    filename = getattr(media, 'file_name', 'file') if media else 'file'
                    filesize = getattr(media, 'file_size', 0) if media else 0
                    try:
                        from handlers.helpers import humanbytes
                        caption_text = custom_caption.format(
                            filename=filename,
                            filesize=humanbytes(filesize),
                            caption=getattr(message, 'caption', '') or ''
                        )
                    except Exception:
                        caption_text = custom_caption
                else:
                    caption_text = f"**File Stored ✅**\n\nLink: {share_link}"

                # Build buttons: stream/download + open link + backup channel
                forwarded_id = int(file_id_str)
                buttons = []
                if Config.STREAM_ENABLED and Config.STREAM_FQDN:
                    try:
                        from handlers.stream_handler import get_stream_link, get_download_link
                        buttons.append([
                            InlineKeyboardButton("▶️ Stream", url=get_stream_link(forwarded_id)),
                            InlineKeyboardButton("📥 Download", url=get_download_link(forwarded_id))
                        ])
                    except Exception:
                        pass
                buttons.append([InlineKeyboardButton("🔗 Open Link", url=share_link)])
                if backup_ch:
                    buttons.append([InlineKeyboardButton("📢 Backup Channel", url=backup_ch)])

                await message.reply_text(
                    caption_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True,
                    quote=True
                )
            except Exception as e:
                await message.reply_text(f"Error: `{e}`", quote=True)

        await clone.start()
        me = await clone.get_me()

        clone_bots[user_id] = clone
        logging.info(f"Clone bot @{me.username} started for user {user_id}")
        return True, me.username

    except Exception as e:
        logging.error(f"Clone bot error for user {user_id}: {e}")
        try:
            if 'clone' in locals() and clone.is_connected:
                await clone.stop()
        except Exception:
            pass
        return False, str(e)


# ── Stop a clone bot ───────────────────────────────────────────────────────────

async def stop_clone_bot(user_id: int) -> bool:
    """Stop a clone bot instance."""
    try:
        clone = clone_bots.get(user_id)
        if clone:
            try:
                await clone.stop()
            except Exception as e:
                logging.warning(f"Error stopping clone: {e}")
            del clone_bots[user_id]
        return True
    except Exception as e:
        logging.error(f"Stop clone error: {e}")
        return False


# ── /clone command ─────────────────────────────────────────────────────────────

async def clone_handler(bot: Client, m: Message):
    """Handle /clone command."""
    if not Config.CLONE_ENABLED:
        await m.reply_text("❌ Clone feature is disabled.", quote=True)
        return

    lang = await db.get_language(m.from_user.id)

    if len(m.command) < 2:
        await m.reply_text(
            "**Usage:** `/clone BOT_TOKEN`\n\n"
            "**Example:** `/clone 123456789:ABC-DEFghijklmno`\n\n"
            "Get your bot token from @BotFather.\n"
            "Files will be stored in the main bot's database channel automatically.",
            quote=True
        )
        return

    bot_token = m.command[1]

    if ":" not in bot_token:
        await m.reply_text("❌ Invalid bot token format! Token should be like: `123456:ABC-DEF`", quote=True)
        return

    # Always use the main bot's DB channel
    db_channel = Config.DB_CHANNEL

    existing = await db.get_clone(m.from_user.id)
    if existing:
        await m.reply_text(
            "❌ You already have an active clone!\n\nUse /removeclone to remove it first.",
            quote=True
        )
        return

    processing = await m.reply_text("⏳ Starting your clone bot...", quote=True)

    success, result = await start_clone_bot(m.from_user.id, bot_token, db_channel)

    if success:
        await db.add_clone(m.from_user.id, bot_token, result, db_channel)
        await processing.edit(get_text(lang, "clone_success").format(username=result))
    else:
        await processing.edit(f"❌ Failed to create clone!\n\n**Error:** `{result}`")


# ── /removeclone command ───────────────────────────────────────────────────────

async def remove_clone_handler(bot: Client, m: Message):
    """Handle /removeclone command."""
    lang = await db.get_language(m.from_user.id)

    existing = await db.get_clone(m.from_user.id)
    if not existing:
        await m.reply_text("❌ You don't have any active clone!", quote=True)
        return

    await stop_clone_bot(m.from_user.id)
    await db.remove_clone(m.from_user.id)
    await m.reply_text(get_text(lang, "clone_removed"), quote=True)


# ── Restart all clones on startup ──────────────────────────────────────────────

async def restart_all_clones():
    """Restart all saved clone bots on startup."""
    if not Config.CLONE_ENABLED:
        return

    try:
        all_clones = await db.get_all_clones()
        count = 0
        clone_list = []

        async for clone_data in all_clones:
            clone_list.append(clone_data)

        for clone_data in clone_list:
            try:
                success, username = await start_clone_bot(
                    clone_data['user_id'],
                    clone_data['bot_token'],
                    clone_data['db_channel']
                )
                if success:
                    count += 1
                    logging.info(f"Restarted clone @{username}")
                else:
                    logging.warning(f"Failed to restart clone for user {clone_data['user_id']}: {username}")
            except Exception as e:
                logging.error(f"Failed to restart clone for {clone_data['user_id']}: {e}")

        logging.info(f"Restarted {count} clone bot(s) out of {len(clone_list)}")
    except Exception as e:
        logging.error(f"Error restarting clones: {e}")
