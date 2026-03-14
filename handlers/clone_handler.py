# Clone Bot Feature — Feature 11

import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from configs import Config
from handlers.database import db
from handlers.languages import get_text
from handlers.helpers import str_to_b64

logging.basicConfig(level=logging.INFO)

# Store active clone bot instances
clone_bots = {}


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

        # Register handlers BEFORE starting
        @clone.on_message(filters.command("start") & filters.private)
        async def clone_start(bot, cmd):
            await cmd.reply_text(
                f"Hello! I'm a clone of @{Config.BOT_USERNAME}.\n\n"
                f"Send me any file and I'll give you a permanent link!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Original Bot", url=f"https://t.me/{Config.BOT_USERNAME}")]
                ])
            )

        @clone.on_message((filters.document | filters.video | filters.audio) & filters.private)
        async def clone_save(bot, message):
            try:
                forwarded = await message.forward(db_channel)
                file_id = str(forwarded.id)
                me = await bot.get_me()
                share_link = f"https://t.me/{me.username}?start=mrkiller_{str_to_b64(file_id)}"
                await message.reply_text(
                    f"**File Stored ✅**\n\nLink: {share_link}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Open Link", url=share_link)]
                    ]),
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
        # Cleanup on failure
        try:
            if 'clone' in locals() and clone.is_connected:
                await clone.stop()
        except Exception:
            pass
        return False, str(e)


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


async def clone_handler(bot: Client, m: Message):
    """Handle /clone command."""
    if not Config.CLONE_ENABLED:
        await m.reply_text("❌ Clone feature is disabled.", quote=True)
        return

    lang = await db.get_language(m.from_user.id)

    if len(m.command) < 3:
        await m.reply_text(get_text(lang, "clone_usage"), quote=True)
        return

    bot_token = m.command[1]

    # Basic token validation
    if ":" not in bot_token:
        await m.reply_text("❌ Invalid bot token format! Token should be like: `123456:ABC-DEF`", quote=True)
        return

    try:
        db_channel = int(m.command[2])
    except ValueError:
        await m.reply_text("❌ Invalid DB Channel ID! Must be a number like: `-1001234567890`", quote=True)
        return

    # Check if user already has a clone
    existing = await db.get_clone(m.from_user.id)
    if existing:
        await m.reply_text(
            "❌ You already have an active clone!\n\n"
            "Use /removeclone to remove it first.",
            quote=True
        )
        return

    processing = await m.reply_text("⏳ Starting your clone bot...", quote=True)

    success, result = await start_clone_bot(m.from_user.id, bot_token, db_channel)

    if success:
        await db.add_clone(m.from_user.id, bot_token, result, db_channel)
        await processing.edit(
            get_text(lang, "clone_success").format(username=result)
        )
    else:
        await processing.edit(f"❌ Failed to create clone!\n\n**Error:** `{result}`")


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


async def restart_all_clones():
    """Restart all saved clone bots on startup."""
    if not Config.CLONE_ENABLED:
        return

    try:
        all_clones = await db.get_all_clones()
        count = 0
        clone_list = []

        # Convert cursor to list first to avoid cursor issues
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
