# Admin Panel — Feature 9

import logging
from configs import Config
from handlers.database import db
from handlers.languages import get_text
from pyrogram import Client
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)


async def is_authorized(user_id: int) -> bool:
    """Check if user is authorized (owner or admin)."""
    return await db.is_admin(int(user_id))


async def add_admin_handler(bot: Client, m: Message):
    """Handle /addadmin command."""
    if int(m.from_user.id) != Config.BOT_OWNER:
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return

    if len(m.command) < 2:
        await m.reply_text(
            "**Usage:** `/addadmin user_id`\n\n"
            "Example: `/addadmin 1234567`",
            quote=True
        )
        return

    try:
        user_id = int(m.command[1])
        await db.add_admin(user_id, m.from_user.id)
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(
            get_text(lang, "admin_added").format(user_id=user_id),
            quote=True
        )
        logging.info(f"Admin added: {user_id} by {m.from_user.id}")
    except ValueError:
        await m.reply_text("❌ Invalid user ID! Must be a number.", quote=True)
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`", quote=True)


async def remove_admin_handler(bot: Client, m: Message):
    """Handle /removeadmin command."""
    if int(m.from_user.id) != Config.BOT_OWNER:
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return

    if len(m.command) < 2:
        await m.reply_text(
            "**Usage:** `/removeadmin user_id`\n\n"
            "Example: `/removeadmin 1234567`",
            quote=True
        )
        return

    try:
        user_id = int(m.command[1])
        if user_id == Config.BOT_OWNER:
            await m.reply_text("❌ Cannot remove the bot owner!", quote=True)
            return
        await db.remove_admin(user_id)
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(
            get_text(lang, "admin_removed").format(user_id=user_id),
            quote=True
        )
        logging.info(f"Admin removed: {user_id} by {m.from_user.id}")
    except ValueError:
        await m.reply_text("❌ Invalid user ID! Must be a number.", quote=True)
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`", quote=True)


async def list_admins_handler(bot: Client, m: Message):
    """Handle /admins command."""
    if not await is_authorized(m.from_user.id):
        lang = await db.get_language(m.from_user.id)
        await m.reply_text(get_text(lang, "not_admin"), quote=True)
        return

    all_admins = await db.get_all_admins()
    lang = await db.get_language(m.from_user.id)

    admin_text = ""
    for i, admin_id in enumerate(all_admins, 1):
        role = "👑 Owner" if int(admin_id) == Config.BOT_OWNER else "🛡️ Admin"
        admin_text += f"{i}. `{admin_id}` — {role}\n"

    if not admin_text:
        admin_text = "No admins configured."

    await m.reply_text(
        get_text(lang, "admin_list").format(admins=admin_text),
        quote=True
    )
