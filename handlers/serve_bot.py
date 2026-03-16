# FileServeBot — Feature 13
# Dedicated bot for serving files to users.
# All links (main bot + clone bots) redirect here via Cloudflare Worker.
# If this bot gets banned: change SERVE_BOT_TOKEN + SERVE_BOT_USERNAME in Koyeb → redeploy → all links work again.

import asyncio
import logging
from binascii import Error
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs import Config
from handlers.database import db
from handlers.helpers import b64_to_str, format_time_seconds
from handlers.languages import get_text

logging.basicConfig(level=logging.INFO)

# Global serve bot instance — accessible from bot.py
serve_bot_instance: Client = None


def get_serve_bot() -> Client:
    return serve_bot_instance


async def start_serve_bot(main_bot: Client):
    """
    Start the FileServeBot alongside the main bot.
    Called from bot.py main() after Bot.start().
    main_bot is passed so we can auto-promote serve bot in DB_CHANNEL.
    """
    global serve_bot_instance

    if not Config.SERVE_BOT_TOKEN:
        logging.warning("SERVE_BOT_TOKEN not set — FileServeBot not started. Set it in Koyeb env vars.")
        return

    serve_bot = Client(
        name="serve_bot",
        bot_token=Config.SERVE_BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        in_memory=True
    )

    @serve_bot.on_message(filters.command("start") & filters.private)
    async def serve_start(bot, cmd):
        """Handle file serving — main entry point for all file links."""
        raw_text = cmd.text.strip()
        start_param = raw_text.split(None, 1)[1] if len(raw_text.split()) > 1 else ""

        # No parameter — show welcome message
        if not start_param:
            await cmd.reply_text(
                "👋 **Hello!**\n\n"
                "I'm a dedicated file serving bot.\n\n"
                "📁 Click any file link to receive your file instantly!\n\n"
                f"🤖 Main Bot: @{Config.BOT_USERNAME}",
                quote=True
            )
            return

        try:
            # Decode file ID from mrkiller_ prefix
            if start_param.startswith("mrkiller_"):
                encoded_part = start_param.split("mrkiller_", 1)[1]
            else:
                encoded_part = start_param

            try:
                file_id = int(b64_to_str(encoded_part))
            except (Error, UnicodeDecodeError, ValueError):
                try:
                    file_id = int(encoded_part)
                except ValueError:
                    await cmd.reply_text("❌ Invalid link!", quote=True)
                    return

            # Get the message from DB_CHANNEL
            get_msg = await bot.get_messages(
                chat_id=Config.DB_CHANNEL,
                message_ids=file_id
            )

            if not get_msg:
                await cmd.reply_text("❌ File not found!", quote=True)
                return

            # Handle batch: text message with space-separated file IDs
            message_ids = []
            if get_msg.text:
                message_ids = [mid.strip() for mid in get_msg.text.split() if mid.strip()]
            elif get_msg.media:
                message_ids = [str(file_id)]
            else:
                await cmd.reply_text("❌ File not found!", quote=True)
                return

            lang = await db.get_language(cmd.from_user.id)

            for mid in message_ids:
                try:
                    mid_int = int(mid)

                    # Build stream/download buttons
                    buttons = []
                    if Config.STREAM_ENABLED and Config.STREAM_FQDN:
                        try:
                            from handlers.stream_handler import get_stream_link, get_download_link
                            buttons.append([
                                InlineKeyboardButton("▶️ Stream", url=get_stream_link(mid_int)),
                                InlineKeyboardButton("📥 Download", url=get_download_link(mid_int))
                            ])
                        except Exception:
                            pass

                    markup = InlineKeyboardMarkup(buttons) if buttons else None

                    try:
                        await bot.copy_message(
                            chat_id=cmd.from_user.id,
                            from_chat_id=Config.DB_CHANNEL,
                            message_id=mid_int,
                            reply_markup=markup,
                            protect_content=Config.PROTECT_CONTENT
                        )
                    except TypeError:
                        await bot.copy_message(
                            chat_id=cmd.from_user.id,
                            from_chat_id=Config.DB_CHANNEL,
                            message_id=mid_int,
                            reply_markup=markup
                        )

                except Exception as e:
                    logging.error(f"ServeBot file send error for {mid}: {e}")
                    continue

            # Send auto-delete warning if enabled
            if Config.AUTO_DELETE_TIME > 0:
                time_str = format_time_seconds(Config.AUTO_DELETE_TIME)
                warn_text = get_text(lang, "auto_delete_warn").format(time=time_str)
                await cmd.reply_text(
                    warn_text,
                    disable_web_page_preview=True,
                    quote=True
                )

        except Exception as e:
            logging.error(f"ServeBot start handler error: {e}")
            await cmd.reply_text(f"❌ Error: `{e}`", quote=True)

    # Start the serve bot
    await serve_bot.start()
    serve_bot_instance = serve_bot
    me = await serve_bot.get_me()
    logging.info(f"FileServeBot @{me.username} started successfully!")
    logging.info(f"Make sure @{me.username} is admin in your DB_CHANNEL to serve files.")
