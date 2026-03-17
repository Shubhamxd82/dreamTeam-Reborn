# (c) @harshil8981 — Enhanced V2

import asyncio
import logging
from configs import Config
from pyrogram import Client
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import FloodWait
from handlers.helpers import encode_link, get_shortlink
from handlers.database import db
from handlers.languages import get_text

logging.basicConfig(level=logging.INFO)


def get_share_link(file_er_id: str) -> str:
    """
    Generate share link using new secure encrypted format.
    Encodes DB_CHANNEL + message_id into a random-looking link.
    Worker receives this, detects no user_id → routes to ServeBot.
    """
    encoded = encode_link(Config.DB_CHANNEL, int(file_er_id))
    if Config.WORKER_URL:
        return f"{Config.WORKER_URL}?link={encoded}"
    else:
        serve_username = Config.SERVE_BOT_USERNAME or Config.BOT_USERNAME
        return f"https://t.me/{serve_username}?start={encoded}"


async def get_user_lang(user_id: int) -> str:
    """Safely get user language, fallback to default."""
    try:
        return await db.get_language(user_id)
    except Exception:
        return Config.DEFAULT_LANGUAGE


async def forward_to_channel(bot: Client, message: Message, editable: Message):
    try:
        __SENT = await message.forward(Config.DB_CHANNEL)
        return __SENT
    except FloodWait as sl:
        if sl.value > 45:
            await asyncio.sleep(sl.value)
            if Config.LOG_CHANNEL:
                await bot.send_message(
                    chat_id=int(Config.LOG_CHANNEL),
                    text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(editable.chat.id)}` !!",
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]]
                    )
                )
        return await forward_to_channel(bot, message, editable)
    except Exception as e:
        logging.error(f"Forward to channel error: {e}")
        return None


async def save_batch_media_in_channel(bot: Client, editable: Message, message_ids: list):
    try:
        lang = await get_user_lang(editable.chat.id)
        message_ids_str = ""

        for message in (await bot.get_messages(chat_id=editable.chat.id, message_ids=message_ids)):
            sent_message = await forward_to_channel(bot, message, editable)
            if sent_message is None:
                continue
            message_ids_str += f"{str(sent_message.id)} "
            await asyncio.sleep(2)

        if not message_ids_str.strip():
            await editable.edit("❌ No files were saved. Please try again.")
            return

        SaveMessage = await bot.send_message(
            chat_id=Config.DB_CHANNEL,
            text=message_ids_str.strip(),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Delete Batch", callback_data="closeMessage")
            ]])
        )

        raw_link = get_share_link(str(SaveMessage.id))
        share_link = await get_shortlink(raw_link)

        await editable.edit(
            get_text(lang, "batch_stored").format(link=share_link),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(get_text(lang, "open_link"), url=share_link)]]
            ),
            disable_web_page_preview=True
        )

        if Config.LOG_CHANNEL:
            try:
                user = editable.reply_to_message.from_user
                await bot.send_message(
                    chat_id=int(Config.LOG_CHANNEL),
                    text=f"#BATCH_SAVE:\n\n[{user.first_name}](tg://user?id={user.id}) Got Batch Link!",
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Link", url=share_link)]])
                )
            except Exception:
                pass

    except Exception as err:
        logging.error(f"Save batch error: {err}")
        try:
            await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
        except Exception:
            pass
        if Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    chat_id=int(Config.LOG_CHANNEL),
                    text=f"#ERROR_TRACEBACK:\nGot Error from `{str(editable.chat.id)}` !!\n\n**Traceback:** `{err}`",
                    disable_web_page_preview=True
                )
            except Exception:
                pass


async def save_media_in_channel(bot: Client, editable: Message, message: Message):
    try:
        lang = await get_user_lang(editable.chat.id)
        forwarded_msg = await message.forward(Config.DB_CHANNEL)
        file_er_id = str(forwarded_msg.id)

        await forwarded_msg.reply_text(
            f"#PRIVATE_FILE:\n\n[{message.from_user.first_name}](tg://user?id={message.from_user.id}) Got File Link!",
            disable_web_page_preview=True
        )

        raw_link = get_share_link(file_er_id)
        share_link = await get_shortlink(raw_link)

        await editable.edit(
            get_text(lang, "file_stored").format(link=share_link),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(get_text(lang, "open_link"), url=share_link)]]
            ),
            disable_web_page_preview=True
        )
    except FloodWait as sl:
        if sl.value > 45:
            logging.warning(f"FloodWait {sl.value}s in save_media")
            await asyncio.sleep(sl.value)
            if Config.LOG_CHANNEL:
                try:
                    await bot.send_message(
                        chat_id=int(Config.LOG_CHANNEL),
                        text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(editable.chat.id)}` !!",
                        disable_web_page_preview=True
                    )
                except Exception:
                    pass
        await save_media_in_channel(bot, editable, message)
    except Exception as err:
        logging.error(f"Save media error: {err}")
        try:
            await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
        except Exception:
            pass
        if Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    chat_id=int(Config.LOG_CHANNEL),
                    text=f"#ERROR_TRACEBACK:\nGot Error from `{str(editable.chat.id)}` !!\n\n**Traceback:** `{err}`",
                    disable_web_page_preview=True
                )
            except Exception:
                pass
