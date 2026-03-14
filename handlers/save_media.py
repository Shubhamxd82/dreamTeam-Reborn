# (c) @harshil8981 — Enhanced V2

import asyncio
from configs import Config
from pyrogram import Client
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import FloodWait
from handlers.helpers import str_to_b64, get_shortlink
from handlers.database import db
from handlers.languages import get_text


# ==================== WORKER URL CONFIG ====================
# Change this to your own Cloudflare Worker URL
# If empty, falls back to direct t.me links
WORKER_URL = Config.WORKER_URL if hasattr(Config, 'WORKER_URL') else ""


def get_share_link(file_er_id: str) -> str:
    """Generate share link - uses Worker URL if set, otherwise direct t.me link."""
    encoded = str_to_b64(file_er_id)
    if WORKER_URL:
        return f"{WORKER_URL}/mrkiller_{encoded}"
    else:
        return f"https://t.me/{Config.BOT_USERNAME}?start=mrkiller_{encoded}"


async def forward_to_channel(bot: Client, message: Message, editable: Message):
    try:
        __SENT = await message.forward(Config.DB_CHANNEL)
        return __SENT
    except FloodWait as sl:
        if sl.value > 45:
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(editable.chat.id)}` !!",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]
                    ]
                )
            )
        return await forward_to_channel(bot, message, editable)


async def save_batch_media_in_channel(bot: Client, editable: Message, message_ids: list):
    try:
        lang = await db.get_language(editable.chat.id)
        message_ids_str = ""

        for message in (await bot.get_messages(chat_id=editable.chat.id, message_ids=message_ids)):
            sent_message = await forward_to_channel(bot, message, editable)
            if sent_message is None:
                continue
            message_ids_str += f"{str(sent_message.id)} "
            await asyncio.sleep(2)

        SaveMessage = await bot.send_message(
            chat_id=Config.DB_CHANNEL,
            text=message_ids_str,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Delete Batch", callback_data="closeMessage")
            ]])
        )

        # Generate share link using worker URL (original behavior)
        raw_link = get_share_link(str(SaveMessage.id))

        # Feature 6: URL Shortener (applied on top of worker URL)
        share_link = await get_shortlink(raw_link)

        await editable.edit(
            get_text(lang, "batch_stored").format(link=share_link),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(get_text(lang, "open_link"), url=share_link)]]
            ),
            disable_web_page_preview=True
        )

        await bot.send_message(
            chat_id=int(Config.LOG_CHANNEL),
            text=f"#BATCH_SAVE:\n\n[{editable.reply_to_message.from_user.first_name}](tg://user?id={editable.reply_to_message.from_user.id}) Got Batch Link!",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Link", url=share_link)]])
        )
    except Exception as err:
        await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
        await bot.send_message(
            chat_id=int(Config.LOG_CHANNEL),
            text=f"#ERROR_TRACEBACK:\nGot Error from `{str(editable.chat.id)}` !!\n\n**Traceback:** `{err}`",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]]
            )
        )


async def save_media_in_channel(bot: Client, editable: Message, message: Message):
    try:
        lang = await db.get_language(editable.chat.id)
        forwarded_msg = await message.forward(Config.DB_CHANNEL)
        file_er_id = str(forwarded_msg.id)

        await forwarded_msg.reply_text(
            f"#PRIVATE_FILE:\n\n[{message.from_user.first_name}](tg://user?id={message.from_user.id}) Got File Link!",
            disable_web_page_preview=True
        )

        # Generate share link using worker URL (original behavior)
        raw_link = get_share_link(file_er_id)

        # Feature 6: URL Shortener
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
            print(f"Sleep of {sl.value}s caused by FloodWait ...")
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(editable.chat.id)}` !!",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]]
                )
            )
        await save_media_in_channel(bot, editable, message)
    except Exception as err:
        await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
        await bot.send_message(
            chat_id=int(Config.LOG_CHANNEL),
            text=f"#ERROR_TRACEBACK:\nGot Error from `{str(editable.chat.id)}` !!\n\n**Traceback:** `{err}`",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]]
            )
        )
