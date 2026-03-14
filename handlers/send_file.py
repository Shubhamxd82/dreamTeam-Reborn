# (c) @harshil8981 — Enhanced V2

import asyncio
import logging
from configs import Config
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, MessageDeleteForbidden
from handlers.helpers import str_to_b64, humanbytes, format_time_seconds, get_shortlink
from handlers.database import db
from handlers.languages import get_text

logging.basicConfig(level=logging.INFO)


def get_file_info(message: Message) -> tuple:
    """Extract file info from a message."""
    media = message.document or message.video or message.audio
    if media:
        filename = getattr(media, 'file_name', 'Unknown')
        filesize = getattr(media, 'file_size', 0)
        return filename, filesize
    return "Unknown", 0


def format_custom_caption(message: Message, user_mention: str = "", username: str = "") -> str:
    """Format custom caption with variables."""
    if not Config.CUSTOM_CAPTION:
        return message.caption or ""

    filename, filesize = get_file_info(message)
    original_caption = message.caption or ""

    try:
        caption = Config.CUSTOM_CAPTION.format(
            filename=filename,
            filesize=humanbytes(filesize),
            caption=original_caption,
            mention=user_mention,
            username=username
        )
        return caption
    except Exception as e:
        logging.error(f"Caption format error: {e}")
        return original_caption


async def reply_forward(message: Message, file_id: int, lang: str = "en"):
    """Send auto-delete warning reply."""
    try:
        if Config.AUTO_DELETE_TIME > 0:
            time_str = format_time_seconds(Config.AUTO_DELETE_TIME)
            warn_text = get_text(lang, "auto_delete_warn").format(time=time_str)
        else:
            warn_text = "📁 Here is your file!"

        # Add stream/download buttons if enabled
        buttons = []
        if Config.STREAM_ENABLED and Config.STREAM_FQDN:
            from handlers.stream_handler import get_stream_link, get_download_link
            stream_link = get_stream_link(file_id)
            dl_link = get_download_link(file_id)
            buttons.append([
                InlineKeyboardButton("▶️ Stream", url=stream_link),
                InlineKeyboardButton("📥 Download", url=dl_link)
            ])

        reply = await message.reply_text(
            warn_text,
            disable_web_page_preview=True,
            quote=True,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )
        return reply
    except FloodWait as e:
        logging.warning(f"FloodWait: {e}")
        await asyncio.sleep(e.value)
        return await reply_forward(message, file_id, lang)
    except Exception as e:
        logging.error(f"Reply forward error: {e}")
        return None


async def media_forward(bot: Client, user_id: int, file_id: int):
    """Forward media to user with custom caption and protect content support."""
    try:
        # Get original message for custom caption
        original_msg = await bot.get_messages(
            chat_id=Config.DB_CHANNEL,
            message_ids=file_id
        )

        if Config.CUSTOM_CAPTION and original_msg.media:
            custom_cap = format_custom_caption(original_msg)
            return await bot.copy_message(
                chat_id=user_id,
                from_chat_id=Config.DB_CHANNEL,
                message_id=file_id,
                caption=custom_cap,
                protect_content=Config.PROTECT_CONTENT  # Feature 8
            )
        elif Config.FORWARD_AS_COPY:
            return await bot.copy_message(
                chat_id=user_id,
                from_chat_id=Config.DB_CHANNEL,
                message_id=file_id,
                protect_content=Config.PROTECT_CONTENT  # Feature 8
            )
        else:
            return await bot.forward_messages(
                chat_id=user_id,
                from_chat_id=Config.DB_CHANNEL,
                message_ids=file_id,
                protect_content=Config.PROTECT_CONTENT  # Feature 8
            )
    except FloodWait as e:
        logging.warning(f"FloodWait: {e}")
        await asyncio.sleep(e.value)
        return await media_forward(bot, user_id, file_id)
    except Exception as e:
        logging.error(f"Media forward error: {e}")
        return None


async def send_media_and_reply(bot: Client, user_id: int, file_id: int):
    """Send file to user with auto-delete, custom caption, stream links."""
    try:
        lang = await db.get_language(user_id)

        sent_message = await media_forward(bot, user_id, file_id)
        if sent_message is None:
            return

        reply_message = await reply_forward(sent_message, file_id, lang)

        # Feature 1: Auto-Delete
        if Config.AUTO_DELETE_TIME > 0:
            asyncio.create_task(
                delete_after_delay(
                    reply_message,
                    sent_message,
                    Config.AUTO_DELETE_TIME,
                    lang
                )
            )
    except Exception as e:
        logging.error(f"Send media error: {e}")


async def delete_after_delay(message, file_message, delay: int, lang: str = "en"):
    """Auto-delete file after specified delay."""
    try:
        await asyncio.sleep(delay)

        # Delete the file message
        try:
            await file_message.delete()
        except Exception:
            pass

        # Edit the warning message
        if message:
            try:
                delete_text = get_text(lang, "file_deleted")
                await message.edit_text(delete_text)
            except (MessageDeleteForbidden, Exception) as e:
                logging.warning(f"Could not edit delete message: {e}")
    except Exception as e:
        logging.error(f"Delete after delay error: {e}")
