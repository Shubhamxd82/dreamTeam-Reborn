# FileServeBot — Feature 13
# Dedicated bot for serving files to users.
# All main bot links redirect here via Cloudflare Worker.
# Clone bot links redirect to clone bot directly via Worker.
# If this bot gets banned: change SERVE_BOT_TOKEN + SERVE_BOT_USERNAME in Koyeb → redeploy → all main bot links work again.

import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from configs import Config
from handlers.database import db
from handlers.helpers import decode_link, format_time_seconds
from handlers.languages import get_text

logging.basicConfig(level=logging.INFO)

# Global serve bot instance
serve_bot_instance: Client = None


def get_serve_bot() -> Client:
    return serve_bot_instance


async def _delete_after_delay(warn_msg, file_messages: list, delay: int, lang: str):
    """Auto-delete served files after delay."""
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
        logging.error(f"ServeBot delete error: {e}")


async def start_serve_bot(main_bot: Client):
    """
    Start the FileServeBot alongside the main bot.
    Called from bot.py main() after Bot.start().
    ServeBot serves files for main bot links only.
    Clone bot links are served by the clone bots themselves.
    """
    global serve_bot_instance

    if not Config.SERVE_BOT_TOKEN:
        logging.warning("SERVE_BOT_TOKEN not set — FileServeBot not started.")
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
        """Handle file serving for main bot links."""
        raw_text = cmd.text.strip()
        start_param = raw_text.split(None, 1)[1] if len(raw_text.split()) > 1 else ""

        # No parameter — show welcome message
        if not start_param:
            await cmd.reply_text(
                "👋 **Hello!**\n\n"
                "I'm Just a file serving bot.\n\n"
                "📁 Use Our **Main Bot** to Get Access of files Here.\n\n"
                f"🤖 Main Bot: [WONDER MAN](https://t.me/{Config.BOT_USERNAME})",
                quote=True,
                disable_web_page_preview=True
            )
            return

        try:
            # Decode the new secure link format
            channel_id, message_id, user_id = decode_link(start_param)

            # user_id should be None for main bot links
            # Clone bot links are routed to clone bot by Worker, not here
            # But we handle both just in case

            # Get the message from the correct channel
            get_msg = await bot.get_messages(
                chat_id=channel_id,
                message_ids=message_id
            )

            if not get_msg:
                await cmd.reply_text("❌ File not found!", quote=True)
                return

            # Handle batch: text message with space-separated file IDs
            message_ids = []
            if get_msg.text:
                message_ids = [mid.strip() for mid in get_msg.text.split() if mid.strip()]
            elif get_msg.media:
                message_ids = [str(message_id)]
            else:
                await cmd.reply_text("❌ File not found!", quote=True)
                return

            lang = await db.get_language(cmd.from_user.id)
            sent_messages = []

            for mid in message_ids:
                try:
                    mid_int = int(mid)

                    # Main bot files get stream/download buttons
                    # Clone bot files (user_id present) get no stream/download
                    buttons = []
                    if not user_id and Config.STREAM_ENABLED and Config.STREAM_FQDN:
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
                        sent = await bot.copy_message(
                            chat_id=cmd.from_user.id,
                            from_chat_id=channel_id,
                            message_id=mid_int,
                            reply_markup=markup,
                            protect_content=Config.PROTECT_CONTENT
                        )
                    except TypeError:
                        # Older Pyrogram — protect_content not supported
                        sent = await bot.copy_message(
                            chat_id=cmd.from_user.id,
                            from_chat_id=channel_id,
                            message_id=mid_int,
                            reply_markup=markup
                        )

                    if sent:
                        sent_messages.append(sent)

                except Exception as e:
                    error_str = str(e)
                    logging.error(f"ServeBot file send error for {mid}: {e}")
                    if "CHAT_FORWARD_PRIVATE" in error_str or "forward_private" in error_str.lower():
                        await cmd.reply_text(
                            "⚠️ **File cannot be sent!**\n\n"
                            "The source channel has **Restrict Saving Content** enabled.\n"
                            "Please ask the admin to disable it in channel settings.",
                            quote=True
                        )
                        return
                    continue

            # Auto-delete warning and scheduling
            if Config.AUTO_DELETE_TIME > 0 and sent_messages:
                time_str = format_time_seconds(Config.AUTO_DELETE_TIME)
                warn_text = get_text(lang, "auto_delete_warn").format(time=time_str)
                warn_msg = await cmd.reply_text(
                    warn_text,
                    disable_web_page_preview=True,
                    quote=True
                )
                asyncio.create_task(
                    _delete_after_delay(warn_msg, sent_messages, Config.AUTO_DELETE_TIME, lang)
                )

        except ValueError as e:
            logging.error(f"ServeBot invalid link: {e}")
            await cmd.reply_text("❌ Invalid link!", quote=True)
        except Exception as e:
            logging.error(f"ServeBot start handler error: {e}")
            await cmd.reply_text(f"❌ Error: `{e}`", quote=True)

    @serve_bot.on_message(filters.private & ~filters.command("start"))
    async def serve_fallback(bot, cmd):
        """Catch all other commands and messages — redirect to main bot."""
        await cmd.reply_text(
            "👋 **Hello!**\n\n"
            "I'm Just a file serving bot.\n\n"
            "📁 Use Our **Main Bot** to Get Access of files Here.\n\n"
            f"🤖 Main Bot: [WONDER MAN](https://t.me/{Config.BOT_USERNAME})",
            quote=True,
            disable_web_page_preview=True
        )

    # Start the serve bot
    await serve_bot.start()
    serve_bot_instance = serve_bot
    me = await serve_bot.get_me()
    logging.info(f"FileServeBot @{me.username} started successfully!")
    logging.info(f"Make sure @{me.username} is admin in your DB_CHANNEL to serve files.")
