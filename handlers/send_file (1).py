# (c) @Shubhlinks — Enhanced V2

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
    media = None
    if message.document:
        media = message.document
    elif message.video:
        media = message.video
    elif message.audio:
        media = message.audio

    if media:
        filename = getattr(media, 'file_name', None) or "Unknown"
        filesize = getattr(media, 'file_size', 0) or 0
        return filename, filesize
    return "Unknown", 0


def format_custom_caption(message: Message, user_mention: str = "", username: str = "") -> str:
    """Format custom caption with variables."""
    if not Config.CUSTOM_CAPTION:
        return getattr(message, 'caption', '') or ""

    filename, filesize = get_file_info(message)
    original_caption = getattr(message, 'caption', '') or ""

    try:
        caption = Config.CUSTOM_CAPTION.format(
            filename=filename,
            filesize=humanbytes(filesize),
            caption=original_caption,
            mention=user_mention,
            username=username
        )
        return caption
    except (KeyError, IndexError, ValueError) as e:
        logging.error(f"Caption format error: {e}")
        return original_caption


def _get_stream_buttons(file_id: int):
    """Build stream/download inline keyboard. Returns list of button rows or []."""
    if not (Config.STREAM_ENABLED and Config.STREAM_FQDN):
        return []
    try:
        from handlers.stream_handler import get_stream_link, get_download_link
        stream_link = get_stream_link(file_id)
        dl_link = get_download_link(file_id)
        return [[
            InlineKeyboardButton("▶️ Stream", url=stream_link),
            InlineKeyboardButton("📥 Download", url=dl_link)
        ]]
    except ImportError:
        logging.warning("stream_handler not available")
        return []


async def reply_forward(message: Message, file_id: int, lang: str = "en"):
    """Send auto-delete warning reply — no stream buttons here."""
    try:
        if Config.AUTO_DELETE_TIME > 0:
            time_str = format_time_seconds(Config.AUTO_DELETE_TIME)
            warn_text = get_text(lang, "auto_delete_warn").format(time=time_str)
        else:
            warn_text = "📁 Here is your file!"

        reply = await message.reply_text(
            warn_text,
            disable_web_page_preview=True,
            quote=True,
        )
        return reply
    except FloodWait as e:
        logging.warning(f"FloodWait in reply_forward: {e.value}s")
        await asyncio.sleep(e.value)
        return await reply_forward(message, file_id, lang)
    except Exception as e:
        logging.error(f"Reply forward error: {e}")
        return None


async def media_forward(bot: Client, user_id: int, file_id: int):
    """Forward media to user with stream/download buttons under the file."""
    try:
        buttons = _get_stream_buttons(file_id)
        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

        if Config.CUSTOM_CAPTION:
            original_msg = await bot.get_messages(
                chat_id=Config.DB_CHANNEL,
                message_ids=file_id
            )
            if original_msg and original_msg.media:
                custom_cap = format_custom_caption(original_msg)
                try:
                    return await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=Config.DB_CHANNEL,
                        message_id=file_id,
                        caption=custom_cap,
                        reply_markup=reply_markup,
                        protect_content=Config.PROTECT_CONTENT
                    )
                except TypeError:
                    return await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=Config.DB_CHANNEL,
                        message_id=file_id,
                        caption=custom_cap,
                        reply_markup=reply_markup,
                        protect_content=Config.PROTECT_CONTENT
                    )

        if Config.FORWARD_AS_COPY:
            try:
                return await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=Config.DB_CHANNEL,
                    message_id=file_id,
                    reply_markup=reply_markup,
                    protect_content=Config.PROTECT_CONTENT
                )
            except TypeError:
                return await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=Config.DB_CHANNEL,
                    message_id=file_id,
                    reply_markup=reply_markup,
                    protect_content=Config.PROTECT_CONTENT
                )
        else:
            # forward_messages doesn't support reply_markup,
            # so forward first then edit the reply_markup
            try:
                sent = await bot.forward_messages(
                    chat_id=user_id,
                    from_chat_id=Config.DB_CHANNEL,
                    message_ids=file_id,
                    protect_content=Config.PROTECT_CONTENT
                )
            except TypeError:
                sent = await bot.forward_messages(
                    chat_id=user_id,
                    from_chat_id=Config.DB_CHANNEL,
                    message_ids=file_id,
                    protect_content=Config.PROTECT_CONTENT
                )
            # Add buttons by editing reply markup after forward
            if sent and reply_markup:
                try:
                    await bot.edit_message_reply_markup(
                        chat_id=user_id,
                        message_id=sent.id,
                        reply_markup=reply_markup
                    )
                except Exception:
                    pass
            return sent

    except FloodWait as e:
        logging.warning(f"FloodWait in media_forward: {e.value}s")
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

        if Config.AUTO_DELETE_TIME > 0 and reply_message:
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

        try:
            await file_message.delete()
        except Exception as e:
            logging.warning(f"Could not delete file message: {e}")

        if message:
            try:
                delete_text = get_text(lang, "file_deleted")
                await message.edit_text(delete_text)
            except MessageDeleteForbidden:
                logging.warning("Message edit forbidden after delete")
            except Exception as e:
                logging.warning(f"Could not edit delete message: {e}")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Delete after delay error: {e}")
