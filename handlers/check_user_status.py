# (c) @Shubhlinks — Enhanced V2

import datetime
import logging
from configs import Config
from handlers.database import Database

logging.basicConfig(level=logging.INFO)

db = Database(Config.DATABASE_URL, Config.BOT_USERNAME)


async def handle_user_status(bot, cmd):
    chat_id = cmd.from_user.id
    if not await db.is_user_exist(chat_id):
        await db.add_user(chat_id)
        if Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    int(Config.LOG_CHANNEL),
                    f"#NEW_USER: \n\nNew User [{cmd.from_user.first_name}](tg://user?id={cmd.from_user.id}) started @{Config.BOT_USERNAME} !!"
                )
            except Exception as e:
                logging.error(f"Log channel send error: {e}")

    ban_status = await db.get_ban_status(chat_id)
    if ban_status and ban_status.get("is_banned", False):
        if (
                datetime.date.today() - datetime.date.fromisoformat(ban_status["banned_on"])
        ).days > ban_status["ban_duration"]:
            await db.remove_ban(chat_id)
        else:
            try:
                from handlers.languages import get_text
                lang = await db.get_language(chat_id)
                await cmd.reply_text(get_text(lang, "banned_msg"), quote=True)
            except Exception:
                await cmd.reply_text("You are Banned!", quote=True)
            return
    await cmd.continue_propagation()
