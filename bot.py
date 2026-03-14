# (c) @harshil8981 — Enhanced V2 with all features

import os
import asyncio
import traceback
import logging
from binascii import Error
from pyrogram import Client, enums, filters
from pyrogram.errors import UserNotParticipant, FloodWait, QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from configs import Config
from handlers.database import db
from handlers.add_user_to_db import add_user_to_database
from handlers.send_file import send_media_and_reply
from handlers.helpers import b64_to_str, str_to_b64
from handlers.check_user_status import handle_user_status
from handlers.force_sub_handler import handle_force_sub, get_invite_link
from handlers.broadcast_handlers import main_broadcast_handler
from handlers.save_media import save_media_in_channel, save_batch_media_in_channel
from handlers.languages import get_text, get_all_lang_codes, get_lang_name, LANGUAGES
from handlers.token_handler import check_token, verify_user_token, get_token_msg
from handlers.admin_handler import (
    is_authorized,
    add_admin_handler,
    remove_admin_handler,
    list_admins_handler
)
from handlers.clone_handler import clone_handler, remove_clone_handler, restart_all_clones

logging.basicConfig(level=logging.INFO)

MediaList = {}

Bot = Client(
    name=Config.BOT_USERNAME,
    in_memory=True,
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)


# ==================== USER STATUS HANDLER ====================
@Bot.on_message(filters.private)
async def _(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)


# ==================== START COMMAND ====================
@Bot.on_message(filters.command("start") & filters.private)
async def start(bot: Client, cmd: Message):

    if cmd.from_user.id in Config.BANNED_USERS:
        await cmd.reply_text("Sorry, You are banned.")
        return

    # Feature 5: Multi Force Sub
    force_channels = Config.get_force_sub_channels()
    if force_channels:
        back = await handle_force_sub(bot, cmd)
        if back == 400:
            return

    usr_cmd = cmd.text.split("_", 1)[-1]

    # Feature 7: Token Verification - Handle verify callback
    if usr_cmd.startswith("verify"):
        parts = usr_cmd.split("_")
        if len(parts) >= 3:
            token = parts[1]
            try:
                user_id = int(parts[2])
            except:
                user_id = cmd.from_user.id
            if user_id == cmd.from_user.id:
                await verify_user_token(cmd.from_user.id, token)
                lang = await db.get_language(cmd.from_user.id)
                from handlers.helpers import format_time_seconds
                time_str = format_time_seconds(Config.TOKEN_TIMEOUT)
                await cmd.reply_text(
                    get_text(lang, "token_verified").format(time=time_str),
                    quote=True
                )
            return

    if usr_cmd == "/start":
        await add_user_to_database(bot, cmd)
        lang = await db.get_language(cmd.from_user.id)

        buttons = [
            [
                InlineKeyboardButton(get_text(lang, "our_channel"), url="https://t.me/Moviesss4ers"),
                InlineKeyboardButton(get_text(lang, "our_group"), url="https://t.me/moviei43")
            ],
            [
                InlineKeyboardButton(get_text(lang, "about_bot_btn"), callback_data="aboutbot"),
                InlineKeyboardButton(get_text(lang, "about_dev_btn"), callback_data="aboutdevs"),
                InlineKeyboardButton(get_text(lang, "close_btn"), callback_data="closeMessage")
            ],
            [
                InlineKeyboardButton("🌐 Language", callback_data="choose_lang")
            ]
        ]

        start_text = get_text(lang, "start_msg").format(
            name=cmd.from_user.first_name,
            id=cmd.from_user.id
        )

        # Feature 3: Custom Start Message with Image
        if Config.START_PIC:
            await cmd.reply_photo(
                photo=Config.START_PIC,
                caption=start_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await cmd.reply_text(
                start_text,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    else:
        try:
            # Feature 7: Token Verification Check
            if Config.TOKEN_VERIFICATION:
                is_verified = await check_token(cmd.from_user.id)
                if not is_verified:
                    lang = await db.get_language(cmd.from_user.id)
                    text, short_link, token = await get_token_msg(
                        cmd.from_user.id, Config.BOT_USERNAME
                    )
                    await cmd.reply_text(
                        text,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                get_text(lang, "verify_button"),
                                url=short_link
                            )]
                        ]),
                        disable_web_page_preview=True,
                        quote=True
                    )
                    return

            try:
                file_id = int(b64_to_str(usr_cmd).split("_")[-1])
            except (Error, UnicodeDecodeError):
                file_id = int(usr_cmd.split("_")[-1])

            GetMessage = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)
            message_ids = []
            if GetMessage.text:
                message_ids = GetMessage.text.split(" ")
            else:
                message_ids.append(int(GetMessage.id))
            for i in range(len(message_ids)):
                await send_media_and_reply(bot, user_id=cmd.from_user.id, file_id=int(message_ids[i]))
        except Exception as err:
            lang = await db.get_language(cmd.from_user.id)
            await cmd.reply_text(get_text(lang, "error_msg").format(err=err))


# ==================== FILE HANDLER ====================
@Bot.on_message((filters.document | filters.video | filters.audio) & ~filters.chat(Config.DB_CHANNEL))
async def main(bot: Client, message: Message):

    if message.chat.type == enums.ChatType.PRIVATE:

        await add_user_to_database(bot, message)

        # Feature 5: Multi Force Sub
        force_channels = Config.get_force_sub_channels()
        if force_channels:
            back = await handle_force_sub(bot, message)
            if back == 400:
                return

        if message.from_user.id in Config.BANNED_USERS:
            await message.reply_text("Sorry, You are banned!", disable_web_page_preview=True)
            return

        if Config.OTHER_USERS_CAN_SAVE_FILE is False:
            # Check if user is admin
            if not await is_authorized(message.from_user.id):
                return

        lang = await db.get_language(message.from_user.id)
        await message.reply_text(
            text=get_text(lang, "choose_option"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(lang, "save_batch"), callback_data="addToBatchTrue")],
                [InlineKeyboardButton(get_text(lang, "get_link"), callback_data="addToBatchFalse")]
            ]),
            quote=True,
            disable_web_page_preview=True
        )
    elif message.chat.type == enums.ChatType.CHANNEL:
        if (message.chat.id == int(Config.LOG_CHANNEL)) or message.forward_from_chat or message.forward_from:
            return
        # Check UPDATES_CHANNEL only if it's set
        if Config.UPDATES_CHANNEL and message.chat.id == int(Config.UPDATES_CHANNEL):
            return
        if int(message.chat.id) in Config.BANNED_CHAT_IDS:
            await bot.leave_chat(message.chat.id)
            return

        # Feature 4: Disable Channel Button
        if Config.DISABLE_CHANNEL_BUTTON:
            try:
                await message.forward(Config.DB_CHANNEL)
            except Exception as err:
                logging.error(f"Channel forward error: {err}")
            return

        try:
            forwarded_msg = await message.forward(Config.DB_CHANNEL)
            file_er_id = str(forwarded_msg.id)
            share_link = f"https://t.me/{Config.BOT_USERNAME}?start=mrkiller_{str_to_b64(file_er_id)}"
            CH_edit = await bot.edit_message_reply_markup(
                message.chat.id, message.id,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Get Sharable Link", url=share_link)]
                ])
            )
            if message.chat.username:
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/{message.chat.username}/{CH_edit.id}) Channel's Broadcasted File's Button Added!"
                )
            else:
                private_ch = str(message.chat.id)[4:]
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/c/{private_ch}/{CH_edit.id}) Channel's Broadcasted File's Button Added!"
                )
        except FloodWait as sl:
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(message.chat.id)}` !!",
                disable_web_page_preview=True
            )
        except Exception as err:
            await bot.leave_chat(message.chat.id)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#ERROR_TRACEBACK:\nGot Error from `{str(message.chat.id)}` !!\n\n**Traceback:** `{err}`",
                disable_web_page_preview=True
            )


# ==================== ADMIN COMMANDS (Feature 9) ====================
@Bot.on_message(filters.private & filters.command("addadmin"))
async def addadmin_cmd(bot: Client, m: Message):
    await add_admin_handler(bot, m)


@Bot.on_message(filters.private & filters.command("removeadmin"))
async def removeadmin_cmd(bot: Client, m: Message):
    await remove_admin_handler(bot, m)


@Bot.on_message(filters.private & filters.command("admins"))
async def admins_cmd(bot: Client, m: Message):
    await list_admins_handler(bot, m)


# ==================== BROADCAST (Enhanced for multi-admin) ====================
@Bot.on_message(filters.private & filters.command("broadcast") & filters.reply)
async def broadcast_handler_open(bot: Client, m: Message):
    if not await is_authorized(m.from_user.id):
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return
    await main_broadcast_handler(m, db)


# ==================== STATUS (Enhanced for multi-admin) ====================
@Bot.on_message(filters.private & filters.command("status"))
async def sts(bot: Client, m: Message):
    if not await is_authorized(m.from_user.id):
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return
    total_users = await db.total_users_count()
    await m.reply_text(
        text=f"**Total Users in DB:** `{total_users}`",
        quote=True
    )


# ==================== BAN/UNBAN (Enhanced for multi-admin) ====================
@Bot.on_message(filters.private & filters.command("ban_user"))
async def ban(c: Client, m: Message):
    if not await is_authorized(m.from_user.id):
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return

    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to ban any user from the bot.\n\n"
            f"Usage:\n\n"
            f"`/ban_user user_id ban_duration ban_reason`\n\n"
            f"Eg: `/ban_user 1234567 28 You misused me.`\n"
            f"This will ban user with id `1234567` for `28` days for the reason `You misused me`.",
            quote=True
        )
        return

    try:
        user_id = int(m.command[1])
        ban_duration = int(m.command[2])
        ban_reason = ' '.join(m.command[3:])
        ban_log_text = f"Banning user {user_id} for {ban_duration} days for the reason {ban_reason}."
        try:
            await c.send_message(
                user_id,
                f"You are banned to use this bot for **{ban_duration}** day(s) for the reason __{ban_reason}__ \n\n"
                f"**Message from the admin**"
            )
            ban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            ban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"

        await db.ban_user(user_id, ban_duration, ban_reason)
        print(ban_log_text)
        await m.reply_text(ban_log_text, quote=True)
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occurred! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Bot.on_message(filters.private & filters.command("unban_user"))
async def unban(c: Client, m: Message):
    if not await is_authorized(m.from_user.id):
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return

    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to unban any user.\n\n"
            f"Usage:\n\n`/unban_user user_id`\n\n"
            f"Eg: `/unban_user 1234567`\n"
            f"This will unban user with id `1234567`.",
            quote=True
        )
        return

    try:
        user_id = int(m.command[1])
        unban_log_text = f"Unbanning user {user_id}"
        try:
            await c.send_message(user_id, f"Your ban was lifted!")
            unban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            unban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
        await db.remove_ban(user_id)
        print(unban_log_text)
        await m.reply_text(unban_log_text, quote=True)
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occurred! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Bot.on_message(filters.private & filters.command("banned_users"))
async def _banned_users(_, m: Message):
    if not await is_authorized(m.from_user.id):
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return

    all_banned_users = await db.get_all_banned_users()
    banned_usr_count = 0
    text = ''

    async for banned_user in all_banned_users:
        user_id = banned_user['id']
        ban_duration = banned_user['ban_status']['ban_duration']
        banned_on = banned_user['ban_status']['banned_on']
        ban_reason = banned_user['ban_status']['ban_reason']
        banned_usr_count += 1
        text += f"> **user_id**: `{user_id}`, **Ban Duration**: `{ban_duration}`, " \
                f"**Banned on**: `{banned_on}`, **Reason**: `{ban_reason}`\n\n"
    reply_text = f"Total banned user(s): `{banned_usr_count}`\n\n{text}"
    if len(reply_text) > 4096:
        with open('banned-users.txt', 'w') as f:
            f.write(reply_text)
        await m.reply_document('banned-users.txt', True)
        os.remove('banned-users.txt')
        return
    await m.reply_text(reply_text, True)


# ==================== CLONE BOT (Feature 11) ====================
@Bot.on_message(filters.private & filters.command("clone"))
async def clone_cmd(bot: Client, m: Message):
    await clone_handler(bot, m)


@Bot.on_message(filters.private & filters.command("removeclone"))
async def removeclone_cmd(bot: Client, m: Message):
    await remove_clone_handler(bot, m)


# ==================== LANGUAGE (Feature 12) ====================
@Bot.on_message(filters.private & filters.command("language"))
async def language_cmd(bot: Client, m: Message):
    buttons = []
    row = []
    for lang_code in get_all_lang_codes():
        row.append(InlineKeyboardButton(
            get_lang_name(lang_code),
            callback_data=f"setlang_{lang_code}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    lang = await db.get_language(m.from_user.id)
    await m.reply_text(
        get_text(lang, "choose_lang"),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True
    )


# ==================== CLEAR BATCH ====================
@Bot.on_message(filters.private & filters.command("clear_batch"))
async def clear_user_batch(bot: Client, m: Message):
    MediaList[f"{str(m.from_user.id)}"] = []
    await m.reply_text("Cleared your batch files successfully!")


# ==================== SETTINGS COMMAND (Owner only) ====================
@Bot.on_message(filters.private & filters.command("settings") & filters.user(Config.BOT_OWNER))
async def settings_cmd(bot: Client, m: Message):
    settings_text = f"""
⚙️ **Bot Settings:**

🔹 **Auto-Delete:** `{Config.AUTO_DELETE_TIME}s` {'✅' if Config.AUTO_DELETE_TIME > 0 else '❌'}
🔹 **Custom Caption:** {'✅' if Config.CUSTOM_CAPTION else '❌'}
🔹 **Start Photo:** {'✅' if Config.START_PIC else '❌'}
🔹 **Channel Button:** {'❌ Disabled' if Config.DISABLE_CHANNEL_BUTTON else '✅ Enabled'}
🔹 **Force Sub Channels:** `{len(Config.get_force_sub_channels())}`
🔹 **URL Shortener:** {'✅' if Config.URL_SHORTENER else '❌'}
🔹 **Token Verify:** {'✅' if Config.TOKEN_VERIFICATION else '❌'}
🔹 **Protect Content:** {'✅' if Config.PROTECT_CONTENT else '❌'}
🔹 **Stream Server:** {'✅' if Config.STREAM_ENABLED else '❌'}
🔹 **Clone Feature:** {'✅' if Config.CLONE_ENABLED else '❌'}
🔹 **Default Language:** `{Config.DEFAULT_LANGUAGE}`
🔹 **Total Admins:** `{len(Config.ADMINS)}`
"""
    await m.reply_text(settings_text, quote=True)


# ==================== CALLBACK QUERY HANDLER ====================
@Bot.on_callback_query()
async def button(bot: Client, cmd: CallbackQuery):

    cb_data = cmd.data

    # Language selection (Feature 12)
    if cb_data.startswith("setlang_"):
        lang_code = cb_data.split("_", 1)[1]
        await db.set_language(cmd.from_user.id, lang_code)
        lang_name = get_lang_name(lang_code)
        await cmd.message.edit(
            get_text(lang_code, "language_changed").format(lang=lang_name)
        )
        return

    # Choose language button
    if cb_data == "choose_lang":
        buttons = []
        row = []
        for lang_code in get_all_lang_codes():
            row.append(InlineKeyboardButton(
                get_lang_name(lang_code),
                callback_data=f"setlang_{lang_code}"
            ))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="gotohome")])

        lang = await db.get_language(cmd.from_user.id)
        await cmd.message.edit(
            get_text(lang, "choose_lang"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if "aboutbot" in cb_data:
        lang = await db.get_language(cmd.from_user.id)
        await cmd.message.edit(
            Config.ABOUT_BOT_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(get_text(lang, "go_home"), callback_data="gotohome"),
                    InlineKeyboardButton(get_text(lang, "about_dev_btn"), callback_data="aboutdevs")
                ]
            ])
        )

    elif "aboutdevs" in cb_data:
        lang = await db.get_language(cmd.from_user.id)
        await cmd.message.edit(
            Config.ABOUT_DEV_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(get_text(lang, "go_home"), callback_data="gotohome"),
                    InlineKeyboardButton(get_text(lang, "about_bot_btn"), callback_data="aboutbot")
                ]
            ])
        )

    elif "gotohome" in cb_data:
        lang = await db.get_language(cmd.from_user.id)
        start_text = get_text(lang, "start_msg").format(
            name=cmd.message.chat.first_name,
            id=cmd.message.chat.id
        )

        buttons = [
            [
                InlineKeyboardButton(get_text(lang, "our_channel"), url="https://t.me/Moviesss4ers"),
                InlineKeyboardButton(get_text(lang, "our_group"), url="https://t.me/moviei43")
            ],
            [
                InlineKeyboardButton(get_text(lang, "about_bot_btn"), callback_data="aboutbot"),
                InlineKeyboardButton(get_text(lang, "about_dev_btn"), callback_data="aboutdevs"),
                InlineKeyboardButton(get_text(lang, "close_btn"), callback_data="closeMessage")
            ],
            [
                InlineKeyboardButton("🌐 Language", callback_data="choose_lang")
            ]
        ]

        # If originally sent as photo, can't switch to text edit
        try:
            await cmd.message.edit(
                start_text,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except:
            await cmd.message.edit_caption(
                caption=start_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif "refreshForceSub" in cb_data:
        force_channels = Config.get_force_sub_channels()
        if not force_channels:
            await cmd.answer("No force sub channels configured!", show_alert=True)
            return

        # Check all channels
        all_joined = True
        for channel_id in force_channels:
            try:
                user = await bot.get_chat_member(channel_id, cmd.message.chat.id)
                if user.status == "kicked":
                    await cmd.message.edit(
                        text="Sorry, You are Banned!",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                all_joined = False
                break
            except Exception:
                continue

        if not all_joined:
            lang = await db.get_language(cmd.from_user.id)
            await cmd.answer(
                "You haven't joined all channels yet! Please join first.",
                show_alert=True
            )
            return

        lang = await db.get_language(cmd.from_user.id)
        start_text = get_text(lang, "start_msg").format(
            name=cmd.message.chat.first_name,
            id=cmd.message.chat.id
        )
        await cmd.message.edit(
            text=start_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(get_text(lang, "our_channel"), url="https://t.me/Moviesss4ers"),
                    InlineKeyboardButton(get_text(lang, "our_group"), url="https://t.me/moviei43")
                ],
                [
                    InlineKeyboardButton(get_text(lang, "about_bot_btn"), callback_data="aboutbot"),
                    InlineKeyboardButton(get_text(lang, "about_dev_btn"), callback_data="aboutdevs")
                ],
                [
                    InlineKeyboardButton("🌐 Language", callback_data="choose_lang")
                ]
            ])
        )

    elif cb_data.startswith("ban_user_"):
        user_id = cb_data.split("_", 2)[-1]
        if not await is_authorized(cmd.from_user.id):
            await cmd.answer("You are not allowed to do that!", show_alert=True)
            return
        try:
            force_channels = Config.get_force_sub_channels()
            if force_channels:
                await bot.ban_chat_member(chat_id=int(force_channels[0]), user_id=int(user_id))
            await cmd.answer("User Banned!", show_alert=True)
        except Exception as e:
            await cmd.answer(f"Can't Ban Him!\n\nError: {e}", show_alert=True)

    elif "addToBatchTrue" in cb_data:
        if MediaList.get(f"{str(cmd.from_user.id)}", None) is None:
            MediaList[f"{str(cmd.from_user.id)}"] = []
        file_id = cmd.message.reply_to_message.id
        MediaList[f"{str(cmd.from_user.id)}"].append(file_id)

        lang = await db.get_language(cmd.from_user.id)
        await cmd.message.edit(
            get_text(lang, "batch_added"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(lang, "get_batch_link"), callback_data="getBatchLink")],
                [InlineKeyboardButton(get_text(lang, "close_msg"), callback_data="closeMessage")]
            ])
        )

    elif "addToBatchFalse" in cb_data:
        await save_media_in_channel(bot, editable=cmd.message, message=cmd.message.reply_to_message)

    elif "getBatchLink" in cb_data:
        message_ids = MediaList.get(f"{str(cmd.from_user.id)}", None)
        if message_ids is None:
            await cmd.answer("Batch List Empty!", show_alert=True)
            return
        await cmd.message.edit("Please wait, generating batch link ...")
        await save_batch_media_in_channel(bot=bot, editable=cmd.message, message_ids=message_ids)
        MediaList[f"{str(cmd.from_user.id)}"] = []

    elif "closeMessage" in cb_data:
        await cmd.message.delete(True)

    try:
        await cmd.answer()
    except QueryIdInvalid:
        pass


# ==================== STARTUP ====================
async def main():
    """Main startup function."""
    await Bot.start()
    logging.info(f"Bot @{Config.BOT_USERNAME} started!")

    # Feature 10: Start stream server
    if Config.STREAM_ENABLED:
        from handlers.stream_handler import start_stream_server, set_bot_client
        set_bot_client(Bot)
        await start_stream_server()
        logging.info(f"Stream server started at {Config.get_stream_base_url()}")

    # Feature 11: Restart clone bots
    if Config.CLONE_ENABLED:
        await restart_all_clones()

    logging.info("All features initialized!")

    # Keep the bot running
    await asyncio.Event().wait()


if __name__ == "__main__":
    # Use asyncio.run for clean startup
    Bot.run(main())
