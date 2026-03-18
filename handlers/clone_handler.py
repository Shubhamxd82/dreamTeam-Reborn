# Clone Bot Feature — Feature 11

import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from configs import Config
from handlers.database import db
from handlers.languages import get_text, get_all_lang_codes, get_lang_name
from handlers.helpers import encode_link, decode_link, format_time_seconds, humanbytes

logging.basicConfig(level=logging.INFO)

# Active clone bot instances: {user_id: Client}
clone_bots = {}

# Batch media lists per clone user: {user_id: [message_ids]}
clone_media_lists = {}

# Tracks users waiting to send text/photo input for /mybot settings
pending_mybot = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def tick(val) -> str:
    return "✅" if val else "❌"


async def _clone_delete_after_delay(warn_msg, file_messages: list, delay: int, lang: str):
    """Auto-delete clone bot served files after delay."""
    try:
        await asyncio.sleep(delay)
        for msg in file_messages:
            try:
                await msg.delete()
            except Exception:
                pass
        if warn_msg:
            try:
                delete_text = get_text(lang, "file_deleted")
                await warn_msg.edit_text(delete_text)
            except Exception:
                pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Clone delete error: {e}")


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
        [InlineKeyboardButton(f"🌐 Language ({lang_name})", callback_data="mybot_lang_menu")],
        [InlineKeyboardButton("❌ Close", callback_data="mybot_close")],
    ])
    return text, keyboard


# ── /mybot command ─────────────────────────────────────────────────────────────

async def mybot_handler(bot: Client, m: Message):
    clone = await db.get_clone(m.from_user.id)
    if not clone:
        await m.reply_text(
            "❌ You don't have an active clone bot!\n\nUse /clone to create one first.",
            quote=True
        )
        return
    text, keyboard = await build_mybot_menu(m.from_user.id)
    await m.reply_text(text, reply_markup=keyboard, quote=True)


# ── /mybot callback handler ────────────────────────────────────────────────────

async def mybot_callback(bot: Client, cmd: CallbackQuery):
    cb = cmd.data
    user_id = cmd.from_user.id

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

    elif cb == "mybot_startpic_menu":
        start_pic = await db.get_clone_setting(user_id, 'start_pic')
        await cmd.message.edit(
            f"🖼 **Start Photo**\n\nCurrent: {tick(bool(start_pic))}\n\nSend a photo to set.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Set Photo", callback_data="mybot_startpic_set")],
                [InlineKeyboardButton("🗑 Remove Photo", callback_data="mybot_startpic_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_startpic_set":
        pending_mybot[user_id] = 'start_pic'
        await cmd.message.edit(
            "🖼 **Set Start Photo**\n\nSend me a **photo**.\n\nSend /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="mybot_startpic_menu")]])
        )

    elif cb == "mybot_startpic_clear":
        await db.update_clone_settings(user_id, {'start_pic': None})
        await cmd.answer("✅ Start photo removed!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

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
            "📝 **Set Start Message**\n\nSend the message text.\n\nSend /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="mybot_startmsg_menu")]])
        )

    elif cb == "mybot_startmsg_clear":
        await db.update_clone_settings(user_id, {'start_msg': None})
        await cmd.answer("✅ Start message removed!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    elif cb == "mybot_caption_menu":
        caption = await db.get_clone_setting(user_id, 'custom_caption')
        preview = f"`{caption[:80]}...`" if caption and len(caption) > 80 else (f"`{caption}`" if caption else "Not set")
        await cmd.message.edit(
            f"✍️ **Custom Caption**\n\nCurrent: {preview}\n\nVariables: `{{filename}}` `{{filesize}}` `{{caption}}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Caption", callback_data="mybot_caption_set")],
                [InlineKeyboardButton("🗑 Clear Caption", callback_data="mybot_caption_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_caption_set":
        pending_mybot[user_id] = 'custom_caption'
        await cmd.message.edit(
            "✍️ **Set Custom Caption**\n\nSend your caption.\nVariables: `{{filename}}` `{{filesize}}` `{{caption}}`\n\nSend /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="mybot_caption_menu")]])
        )

    elif cb == "mybot_caption_clear":
        await db.update_clone_settings(user_id, {'custom_caption': None})
        await cmd.answer("✅ Caption cleared!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    elif cb == "mybot_backup_menu":
        backup_ch = await db.get_clone_setting(user_id, 'backup_channel')
        await cmd.message.edit(
            f"📢 **Backup Channel Button**\n\nCurrent: `{backup_ch or 'Not set'}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Channel", callback_data="mybot_backup_set")],
                [InlineKeyboardButton("🗑 Remove Channel", callback_data="mybot_backup_clear")],
                [InlineKeyboardButton("« Back", callback_data="mybot_main")],
            ])
        )

    elif cb == "mybot_backup_set":
        pending_mybot[user_id] = 'backup_channel'
        await cmd.message.edit(
            "📢 **Set Backup Channel**\n\nSend the channel URL.\nExample: `https://t.me/MyChannel`\n\nSend /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="mybot_backup_menu")]])
        )

    elif cb == "mybot_backup_clear":
        await db.update_clone_settings(user_id, {'backup_channel': None})
        await cmd.answer("✅ Backup channel removed!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    elif cb == "mybot_lang_menu":
        current_lang = await db.get_clone_setting(user_id, 'language', Config.DEFAULT_LANGUAGE)
        buttons = []
        row = []
        for lang_code in get_all_lang_codes():
            marker = "✅ " if lang_code == current_lang else ""
            row.append(InlineKeyboardButton(f"{marker}{get_lang_name(lang_code)}", callback_data=f"mybot_lang_set_{lang_code}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("« Back", callback_data="mybot_main")])
        await cmd.message.edit("🌐 **Select Language for Clone Bot**", reply_markup=InlineKeyboardMarkup(buttons))

    elif cb.startswith("mybot_lang_set_"):
        lang_code = cb.replace("mybot_lang_set_", "")
        await db.update_clone_settings(user_id, {'language': lang_code})
        await cmd.answer(f"✅ Language set to {get_lang_name(lang_code)}!", show_alert=False)
        text, keyboard = await build_mybot_menu(user_id)
        await cmd.message.edit(text, reply_markup=keyboard)

    try:
        await cmd.answer()
    except Exception:
        pass


# ── Text/Photo input handler ───────────────────────────────────────────────────

async def handle_mybot_input(bot: Client, m: Message) -> bool:
    user_id = m.from_user.id
    if user_id not in pending_mybot:
        return False

    if m.text and m.text.strip() == "/cancel":
        pending_mybot.pop(user_id, None)
        text, keyboard = await build_mybot_menu(user_id)
        if text:
            await m.reply_text(text, reply_markup=keyboard, quote=True)
        return True

    action = pending_mybot.pop(user_id, None)

    if action == 'start_pic':
        if m.photo:
            await db.update_clone_settings(user_id, {'start_pic': m.photo.file_id})
            await m.reply_text("✅ Start photo saved!", quote=True)
        else:
            await m.reply_text("❌ Please send a **photo**, not text.", quote=True)
            pending_mybot[user_id] = 'start_pic'
            return True
    elif action == 'start_msg':
        val = m.text.strip() if m.text else None
        if val:
            await db.update_clone_settings(user_id, {'start_msg': val})
            await m.reply_text("✅ Start message saved!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send text.", quote=True)
    elif action == 'custom_caption':
        val = m.text.strip() if m.text else None
        if val:
            await db.update_clone_settings(user_id, {'custom_caption': val})
            await m.reply_text("✅ Custom caption saved!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send text.", quote=True)
    elif action == 'backup_channel':
        val = m.text.strip() if m.text else None
        if val:
            await db.update_clone_settings(user_id, {'backup_channel': val})
            await m.reply_text(f"✅ Backup channel set to `{val}`!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send channel URL.", quote=True)

    text, keyboard = await build_mybot_menu(user_id)
    if text:
        await m.reply_text(text, reply_markup=keyboard, quote=True)
    return True


# ── Start a clone bot instance ─────────────────────────────────────────────────

async def start_clone_bot(owner_user_id: int, bot_token: str, db_channel: int) -> tuple:
    """Start a clone bot instance. Returns (success, username_or_error)."""
    try:
        clone = Client(
            name=f"clone_{owner_user_id}",
            bot_token=bot_token,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            in_memory=True
        )

        async def _save_single_file(bot, message: Message, settings: dict) -> str:
            """
            Forward file to clone's OWN channel and return share link.
            Clone bot IS admin of db_channel — direct forward works ✅
            """
            forwarded = await message.forward(db_channel)
            file_id_str = str(forwarded.id)

            # Generate new secure link encoding clone's channel + message_id + owner_user_id
            # Worker receives link → redirects to ServeBot
            # ServeBot decodes channel_id → fetches from clone's channel ✅
            encoded = encode_link(db_channel, int(file_id_str), owner_user_id)
            if Config.WORKER_URL:
                share_link = f"{Config.WORKER_URL}?link={encoded}"
            else:
                me = await bot.get_me()
                share_link = f"https://t.me/{me.username}?start={encoded}"

            return share_link, file_id_str

        @clone.on_message(filters.command("start") & filters.private)
        async def clone_start(bot, cmd):
            """Handle /start — serve file or show welcome message."""
            clone_data = await db.get_clone(owner_user_id)
            settings = clone_data.get('settings', {}) if clone_data else {}
            start_pic = settings.get('start_pic')
            start_msg = settings.get('start_msg')
            backup_ch = settings.get('backup_channel')
            custom_caption = settings.get('custom_caption')
            lang = settings.get('language', Config.DEFAULT_LANGUAGE)

            # Track user in clone's own user list
            await db.clone_add_user(owner_user_id, cmd.from_user.id)

            # Check if user is banned from this clone bot
            ban_status = await db.clone_get_ban_status(owner_user_id, cmd.from_user.id)
            if ban_status.get('is_banned'):
                await cmd.reply_text("❌ Sorry, you are banned from using this bot.", quote=True)
                return

            raw_text = cmd.text.strip()
            start_param = raw_text.split(None, 1)[1] if len(raw_text.split()) > 1 else ""

            if start_param:
                try:
                    # Decode new secure link format
                    channel_id, message_id, _ = decode_link(start_param)

                    get_msg = await bot.get_messages(chat_id=channel_id, message_ids=message_id)
                    if not get_msg:
                        await cmd.reply_text("❌ File not found!", quote=True)
                        return

                    # Handle batch: text message = multiple IDs
                    message_ids = []
                    if get_msg.text:
                        message_ids = [mid.strip() for mid in get_msg.text.split() if mid.strip()]
                    elif get_msg.media:
                        message_ids = [str(message_id)]
                    else:
                        await cmd.reply_text("❌ File not found!", quote=True)
                        return

                    sent_messages = []

                    for mid in message_ids:
                        try:
                            mid_int = int(mid)
                            file_msg = await bot.get_messages(chat_id=channel_id, message_ids=mid_int)
                            if not file_msg or not file_msg.media:
                                continue

                            # Build caption
                            if custom_caption:
                                media = file_msg.document or file_msg.video or file_msg.audio
                                filename = getattr(media, 'file_name', 'file') if media else 'file'
                                filesize = getattr(media, 'file_size', 0) if media else 0
                                try:
                                    caption_text = custom_caption.format(
                                        filename=filename,
                                        filesize=humanbytes(filesize),
                                        caption=getattr(file_msg, 'caption', '') or ''
                                    )
                                except Exception:
                                    caption_text = custom_caption
                            else:
                                caption_text = None

                            # NO stream/download for clone bots
                            file_buttons = []
                            if backup_ch:
                                file_buttons.append([InlineKeyboardButton("📢 Backup Channel", url=backup_ch)])
                            markup = InlineKeyboardMarkup(file_buttons) if file_buttons else None

                            try:
                                sent = await bot.copy_message(
                                    chat_id=cmd.from_user.id,
                                    from_chat_id=channel_id,
                                    message_id=mid_int,
                                    caption=caption_text,
                                    reply_markup=markup,
                                    protect_content=Config.PROTECT_CONTENT
                                )
                            except TypeError:
                                sent = await bot.copy_message(
                                    chat_id=cmd.from_user.id,
                                    from_chat_id=channel_id,
                                    message_id=mid_int,
                                    caption=caption_text,
                                    reply_markup=markup
                                )
                            if sent:
                                sent_messages.append(sent)

                        except Exception as e:
                            logging.error(f"Clone batch send error for {mid}: {e}")
                            continue

                    # Auto-delete warning
                    if Config.AUTO_DELETE_TIME > 0 and sent_messages:
                        time_str = format_time_seconds(Config.AUTO_DELETE_TIME)
                        warn_text = get_text(lang, "auto_delete_warn").format(time=time_str)
                        warn_msg = await cmd.reply_text(warn_text, disable_web_page_preview=True, quote=True)
                        asyncio.create_task(
                            _clone_delete_after_delay(warn_msg, sent_messages, Config.AUTO_DELETE_TIME, lang)
                        )
                    return

                except ValueError as e:
                    logging.error(f"Clone start decode error: {e}")
                    await cmd.reply_text("❌ Invalid link!", quote=True)
                    return
                except Exception as e:
                    logging.error(f"Clone file send error: {e}")
                    await cmd.reply_text(f"❌ Error: `{e}`", quote=True)
                    return

            # No param — show welcome message
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
                    await cmd.reply_photo(photo=start_pic, caption=message_text, reply_markup=markup)
                    return
                except Exception:
                    pass
            await cmd.reply_text(message_text, reply_markup=markup)


        @clone.on_message((filters.document | filters.video | filters.audio) & filters.private)
        async def clone_file_handler(bot, message):
            """Show Save Single / Save Batch options when user sends a file."""
            try:
                clone_data = await db.get_clone(owner_user_id)
                settings = clone_data.get('settings', {}) if clone_data else {}
                lang = settings.get('language', Config.DEFAULT_LANGUAGE)

                await message.reply_text(
                    get_text(lang, "choose_option"),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(lang, "save_batch"), callback_data="clone_addBatchTrue")],
                        [InlineKeyboardButton(get_text(lang, "get_link"), callback_data="clone_addBatchFalse")]
                    ]),
                    quote=True,
                    disable_web_page_preview=True
                )
            except Exception as e:
                logging.error(f"Clone file handler error: {e}")
                await message.reply_text(f"❌ Error: `{e}`", quote=True)


        @clone.on_callback_query()
        async def clone_callback_handler(bot, cmd):
            """Handle all callbacks for clone bot."""
            cb = cmd.data
            cb_user_id = cmd.from_user.id

            if cb == "clone_addBatchTrue":
                # Add to batch list
                if clone_media_lists.get(cb_user_id) is None:
                    clone_media_lists[cb_user_id] = []
                if cmd.message.reply_to_message:
                    clone_media_lists[cb_user_id].append(cmd.message.reply_to_message.id)

                clone_data = await db.get_clone(owner_user_id)
                settings = clone_data.get('settings', {}) if clone_data else {}
                lang = settings.get('language', Config.DEFAULT_LANGUAGE)

                await cmd.message.edit(
                    get_text(lang, "batch_added"),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(lang, "get_batch_link"), callback_data="clone_getBatchLink")],
                        [InlineKeyboardButton(get_text(lang, "close_msg"), callback_data="clone_closeMsg")]
                    ])
                )

            elif cb == "clone_addBatchFalse":
                # Save as single file
                file_msg = cmd.message.reply_to_message
                if not file_msg:
                    await cmd.answer("❌ File not found!", show_alert=True)
                    return

                try:
                    clone_data = await db.get_clone(owner_user_id)
                    settings = clone_data.get('settings', {}) if clone_data else {}
                    custom_caption = settings.get('custom_caption')
                    backup_ch = settings.get('backup_channel')

                    share_link, file_id_str = await _save_single_file(bot, file_msg, settings)

                    # Build caption
                    if custom_caption:
                        media = file_msg.document or file_msg.video or file_msg.audio
                        filename = getattr(media, 'file_name', 'file') or 'file'
                        filesize = getattr(media, 'file_size', 0) or 0
                        try:
                            caption_text = custom_caption.format(
                                filename=filename,
                                filesize=humanbytes(filesize),
                                caption=getattr(file_msg, 'caption', '') or ''
                            )
                        except Exception:
                            caption_text = custom_caption
                    else:
                        caption_text = f"**File Stored ✅**\n\nLink: {share_link}"

                    buttons = [[InlineKeyboardButton("🔗 Open Link", url=share_link)]]
                    if backup_ch:
                        buttons.append([InlineKeyboardButton("📢 Backup Channel", url=backup_ch)])

                    await cmd.message.edit(
                        caption_text,
                        reply_markup=InlineKeyboardMarkup(buttons),
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    await cmd.message.edit(f"❌ Error: `{e}`")

            elif cb == "clone_getBatchLink":
                msg_ids = clone_media_lists.get(cb_user_id)
                if not msg_ids:
                    await cmd.answer("Batch list is empty!", show_alert=True)
                    return

                clone_data = await db.get_clone(owner_user_id)
                settings = clone_data.get('settings', {}) if clone_data else {}
                backup_ch = settings.get('backup_channel')
                lang = settings.get('language', Config.DEFAULT_LANGUAGE)

                await cmd.message.edit("⏳ Please wait, generating batch link...")

                try:
                    message_ids_str = ""
                    messages = await bot.get_messages(chat_id=cmd.message.chat.id, message_ids=msg_ids)
                    for msg in messages:
                        try:
                            sent = await msg.forward(db_channel)
                            message_ids_str += f"{str(sent.id)} "
                            await asyncio.sleep(1)
                        except Exception as e:
                            logging.error(f"Clone batch forward error: {e}")
                            continue

                    if not message_ids_str.strip():
                        await cmd.message.edit("❌ No files saved. Please try again.")
                        return

                    # Save batch index message
                    batch_msg = await bot.send_message(
                        chat_id=db_channel,
                        text=message_ids_str.strip(),
                        disable_web_page_preview=True
                    )

                    encoded = encode_link(db_channel, batch_msg.id, owner_user_id)
                    if Config.WORKER_URL:
                        share_link = f"{Config.WORKER_URL}?link={encoded}"
                    else:
                        me = await bot.get_me()
                        share_link = f"https://t.me/{me.username}?start={encoded}"

                    clone_media_lists[cb_user_id] = []

                    buttons = [[InlineKeyboardButton("🔗 Open Link", url=share_link)]]
                    if backup_ch:
                        buttons.append([InlineKeyboardButton("📢 Backup Channel", url=backup_ch)])

                    await cmd.message.edit(
                        get_text(lang, "batch_stored").format(link=share_link),
                        reply_markup=InlineKeyboardMarkup(buttons),
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    await cmd.message.edit(f"❌ Error: `{e}`")

            elif cb == "clone_closeMsg":
                clone_media_lists.pop(cb_user_id, None)
                try:
                    await cmd.message.delete()
                except Exception:
                    pass

            try:
                await cmd.answer()
            except Exception:
                pass


        @clone.on_message(filters.command("status") & filters.private)
        async def clone_status(bot, cmd):
            """Show total users — owner only."""
            if cmd.from_user.id != owner_user_id:
                await cmd.reply_text("❌ You are not authorized!", quote=True)
                return
            total = await db.clone_total_users_count(owner_user_id)
            await cmd.reply_text(
                f"📊 **Clone Bot Status**\n\n"
                f"👥 **Total Users:** `{total}`",
                quote=True
            )


        @clone.on_message(filters.command("broadcast") & filters.private & filters.reply)
        async def clone_broadcast(bot, cmd):
            """Broadcast a message to all users — owner only."""
            if cmd.from_user.id != owner_user_id:
                await cmd.reply_text("❌ You are not authorized!", quote=True)
                return

            broadcast_msg = cmd.reply_to_message
            if not broadcast_msg:
                await cmd.reply_text("❌ Reply to a message to broadcast it.", quote=True)
                return

            status_msg = await cmd.reply_text("📡 Broadcasting...", quote=True)
            success = 0
            failed = 0

            all_users = await db.clone_get_all_users(owner_user_id)
            async for user in all_users:
                try:
                    await broadcast_msg.copy(chat_id=user['user_id'])
                    success += 1
                except Exception:
                    failed += 1
                await asyncio.sleep(0.05)

            await status_msg.edit(
                f"✅ **Broadcast Complete!**\n\n"
                f"✅ Success: `{success}`\n"
                f"❌ Failed: `{failed}`"
            )


        @clone.on_message(filters.command("ban_user") & filters.private)
        async def clone_ban(bot, cmd):
            """Ban a user — owner only."""
            if cmd.from_user.id != owner_user_id:
                await cmd.reply_text("❌ You are not authorized!", quote=True)
                return

            if len(cmd.command) < 2:
                await cmd.reply_text(
                    "**Usage:** `/ban_user USER_ID DAYS REASON`\n\n"
                    "**Example:** `/ban_user 123456789 7 Spam`",
                    quote=True
                )
                return

            try:
                ban_user_id = int(cmd.command[1])
                ban_duration = int(cmd.command[2]) if len(cmd.command) > 2 else 0
                ban_reason = ' '.join(cmd.command[3:]) if len(cmd.command) > 3 else "No reason given"

                await db.clone_ban_user(owner_user_id, ban_user_id, ban_duration, ban_reason)

                try:
                    await bot.send_message(
                        ban_user_id,
                        f"⛔ You have been banned from this bot.\n"
                        f"**Duration:** {ban_duration} day(s)\n"
                        f"**Reason:** {ban_reason}"
                    )
                except Exception:
                    pass

                await cmd.reply_text(
                    f"✅ User `{ban_user_id}` banned for `{ban_duration}` days.\n"
                    f"**Reason:** {ban_reason}",
                    quote=True
                )
            except (ValueError, IndexError):
                await cmd.reply_text("❌ Invalid format! Use: `/ban_user USER_ID DAYS REASON`", quote=True)
            except Exception as e:
                await cmd.reply_text(f"❌ Error: `{e}`", quote=True)


        @clone.on_message(filters.command("unban_user") & filters.private)
        async def clone_unban(bot, cmd):
            """Unban a user — owner only."""
            if cmd.from_user.id != owner_user_id:
                await cmd.reply_text("❌ You are not authorized!", quote=True)
                return

            if len(cmd.command) < 2:
                await cmd.reply_text(
                    "**Usage:** `/unban_user USER_ID`\n\n"
                    "**Example:** `/unban_user 123456789`",
                    quote=True
                )
                return

            try:
                unban_user_id = int(cmd.command[1])
                await db.clone_unban_user(owner_user_id, unban_user_id)

                try:
                    await bot.send_message(unban_user_id, "✅ You have been unbanned from this bot.")
                except Exception:
                    pass

                await cmd.reply_text(f"✅ User `{unban_user_id}` has been unbanned.", quote=True)
            except ValueError:
                await cmd.reply_text("❌ Invalid user ID!", quote=True)
            except Exception as e:
                await cmd.reply_text(f"❌ Error: `{e}`", quote=True)


        @clone.on_message(filters.command("banned_users") & filters.private)
        async def clone_banned_list(bot, cmd):
            """List all banned users — owner only."""
            if cmd.from_user.id != owner_user_id:
                await cmd.reply_text("❌ You are not authorized!", quote=True)
                return

            banned_users = await db.clone_get_all_banned_users(owner_user_id)
            count = 0
            text = ""

            async for user in banned_users:
                uid = user['user_id']
                ban_info = user.get('ban_status', {})
                duration = ban_info.get('ban_duration', 0)
                reason = ban_info.get('ban_reason', 'No reason')
                banned_on = ban_info.get('banned_on', 'Unknown')
                text += f"> `{uid}` | {duration}d | {banned_on} | {reason}\n\n"
                count += 1

            if count == 0:
                await cmd.reply_text("✅ No banned users.", quote=True)
                return

            reply = f"**Total Banned:** `{count}`\n\n{text}"
            if len(reply) > 4096:
                with open(f'banned_{owner_user_id}.txt', 'w') as f:
                    f.write(reply)
                await cmd.reply_document(f'banned_{owner_user_id}.txt', quote=True)
                import os
                os.remove(f'banned_{owner_user_id}.txt')
            else:
                await cmd.reply_text(reply, quote=True)


        await clone.start()
        me = await clone.get_me()
        clone_bots[owner_user_id] = clone
        logging.info(f"Clone bot @{me.username} started for user {owner_user_id}")
        return True, me.username

    except Exception as e:
        logging.error(f"Clone bot error for user {owner_user_id}: {e}")
        try:
            if 'clone' in locals() and clone.is_connected:
                await clone.stop()
        except Exception:
            pass
        return False, str(e)


# ── Stop a clone bot ───────────────────────────────────────────────────────────

async def stop_clone_bot(user_id: int) -> bool:
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

    if len(m.command) < 3:
        await m.reply_text(
            "**Usage:** `/clone BOT_TOKEN DB_CHANNEL`\n\n"
            "**Example:** `/clone 123456789:ABC-DEF -1001234567890`\n\n"
            "**Setup steps:**\n"
            "1. Create bot via @BotFather → get token\n"
            "2. Create a private Telegram channel\n"
            "3. Add your bot as admin to that channel\n"
            "4. Add @MckcserveBOT as admin to that channel\n"
            "5. Get your channel ID (starts with -100)\n"
            "6. Run this command with both values",
            quote=True
        )
        return

    bot_token = m.command[1]
    if ":" not in bot_token:
        await m.reply_text("❌ Invalid bot token format! Should be like: `123456:ABC-DEF`", quote=True)
        return

    try:
        db_channel = int(m.command[2])
    except ValueError:
        await m.reply_text("❌ Invalid channel ID! Must be a number like: `-1001234567890`", quote=True)
        return

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
