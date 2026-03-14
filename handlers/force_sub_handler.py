# (c) @Shubhlinks — Enhanced V2: Multi Force Sub

import asyncio
import logging
from typing import Union, List
from configs import Config
from handlers.database import db
from handlers.languages import get_text
from pyrogram import Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

logging.basicConfig(level=logging.INFO)


async def get_invite_link(bot: Client, chat_id: Union[str, int]):
    """Get invite link for a channel. Bot must be admin."""
    try:
        invite_link = await bot.create_chat_invite_link(chat_id=int(chat_id))
        return invite_link
    except FloodWait as e:
        logging.warning(f"FloodWait {e.value}s in get_invite_link")
        await asyncio.sleep(e.value)
        return await get_invite_link(bot, chat_id)
    except Exception as e:
        logging.error(f"Error getting invite link for {chat_id}: {e}")
        return None


async def handle_force_sub(bot: Client, cmd: Message):
    """Handle force subscription check for multiple channels."""
    force_channels = Config.get_force_sub_channels()

    if not force_channels:
        return 200

    user_id = cmd.from_user.id
    lang = await db.get_language(user_id)

    not_joined_channels = []

    for channel_id in force_channels:
        try:
            user = await bot.get_chat_member(chat_id=int(channel_id), user_id=user_id)
            if user.status == "kicked":
                await bot.send_message(
                    chat_id=user_id,
                    text=get_text(lang, "banned_msg"),
                    disable_web_page_preview=True
                )
                return 400
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            logging.error(f"Force sub check error for channel {channel_id}: {e}")
            continue

    if not not_joined_channels:
        return 200

    buttons = []
    for i, channel_id in enumerate(not_joined_channels, 1):
        try:
            invite_link = await get_invite_link(bot, chat_id=channel_id)
            if invite_link is None:
                continue
            try:
                chat_info = await bot.get_chat(int(channel_id))
                channel_name = chat_info.title
            except Exception:
                channel_name = f"Channel {i}"
            buttons.append([
                InlineKeyboardButton(
                    f"🤖 {get_text(lang, 'join_button')} — {channel_name}",
                    url=invite_link.invite_link
                )
            ])
        except Exception as err:
            logging.error(f"Unable to get invite link for {channel_id}: {err}")
            continue

    if not buttons:
        return 200

    buttons.append([
        InlineKeyboardButton(get_text(lang, "refresh_button"), callback_data="refreshForceSub")
    ])

    await bot.send_message(
        chat_id=user_id,
        text=get_text(lang, "force_sub"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return 400
