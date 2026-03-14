# (c) @harshil8981 — Enhanced V2: Multi Force Sub

import asyncio
from typing import Union, List
from configs import Config
from handlers.database import db
from handlers.languages import get_text
from pyrogram import Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


async def get_invite_link(bot: Client, chat_id: Union[str, int]):
    try:
        invite_link = await bot.create_chat_invite_link(chat_id=chat_id)
        return invite_link
    except FloodWait as e:
        print(f"Sleep of {e.value}s caused by FloodWait ...")
        await asyncio.sleep(e.value)
        return await get_invite_link(bot, chat_id)


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
            user = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
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
            print(f"Force sub error for channel {channel_id}: {e}")
            continue

    if not not_joined_channels:
        return 200

    # Build buttons for all channels user hasn't joined
    buttons = []
    for i, channel_id in enumerate(not_joined_channels, 1):
        try:
            invite_link = await get_invite_link(bot, chat_id=channel_id)
            try:
                chat_info = await bot.get_chat(channel_id)
                channel_name = chat_info.title
            except:
                channel_name = f"Channel {i}"
            buttons.append([
                InlineKeyboardButton(
                    f"🤖 {get_text(lang, 'join_button')} — {channel_name}",
                    url=invite_link.invite_link
                )
            ])
        except Exception as err:
            print(f"Unable to get invite link for {channel_id}: {err}")
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
