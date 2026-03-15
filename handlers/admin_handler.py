# Admin Panel — Feature 9

import logging
from configs import Config
from handlers.database import db
from handlers.languages import get_text
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logging.basicConfig(level=logging.INFO)

# Tracks owner waiting to send text input for a setting
# Format: {user_id: 'action_name'}
pending_settings = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def tick(val) -> str:
    return "✅" if val else "❌"


async def build_settings_menu() -> tuple:
    """Build the main settings menu text and keyboard."""
    auto_del = await db.get_setting('auto_delete_time', Config.AUTO_DELETE_TIME)
    auto_del = int(auto_del) if auto_del is not None else 0
    caption = await db.get_setting('custom_caption', Config.CUSTOM_CAPTION)
    protect = await db.get_setting('protect_content', Config.PROTECT_CONTENT)
    stream = await db.get_setting('stream_enabled', Config.STREAM_ENABLED)
    shortener = await db.get_setting('url_shortener', Config.URL_SHORTENER)
    token = await db.get_setting('token_verification', Config.TOKEN_VERIFICATION)
    force_sub = await db.get_setting('updates_channel', Config.UPDATES_CHANNEL)

    text = (
        "⚙️ **Bot Settings**\n\n"
        f"◆ Auto Delete: `{auto_del}s` {tick(auto_del > 0)}\n"
        f"◆ Custom Caption: {tick(bool(caption))}\n"
        f"◆ Force Sub: {tick(bool(force_sub))}\n"
        f"◆ Protect Content: {tick(protect)}\n"
        f"◆ File Stream: {tick(stream)}\n"
        f"◆ URL Shortener: {tick(shortener)}\n"
        f"◆ Token Verify: {tick(token)}\n\n"
        "Tap a button to toggle or configure."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"⏱ Auto Delete {tick(auto_del > 0)}", callback_data="stg_autodel_menu"),
            InlineKeyboardButton(f"✍️ Caption {tick(bool(caption))}", callback_data="stg_caption_menu"),
        ],
        [
            InlineKeyboardButton(f"📢 Force Sub {tick(bool(force_sub))}", callback_data="stg_forcesub_menu"),
            InlineKeyboardButton(f"🔒 Protect {tick(protect)}", callback_data="stg_tog_protect"),
        ],
        [
            InlineKeyboardButton(f"📡 Stream {tick(stream)}", callback_data="stg_tog_stream"),
            InlineKeyboardButton(f"🔗 Shortener {tick(shortener)}", callback_data="stg_shortener_menu"),
        ],
        [
            InlineKeyboardButton(f"🎫 Token {tick(token)}", callback_data="stg_tog_token"),
            InlineKeyboardButton("📊 Full Status", callback_data="stg_status"),
        ],
        [InlineKeyboardButton("🤖 My Clone Bot", callback_data="stg_clone_info")],
        [InlineKeyboardButton("❌ Close", callback_data="closeMessage")],
    ])

    return text, keyboard


# ── /settings command ──────────────────────────────────────────────────────────

async def settings_handler(bot: Client, m: Message):
    """Handle /settings command — owner only."""
    if int(m.from_user.id) != Config.BOT_OWNER:
        await m.reply_text("❌ You are not authorized.", quote=True)
        return
    text, keyboard = await build_settings_menu()
    await m.reply_text(text, reply_markup=keyboard, quote=True)


# ── Callback handler ────────────────────────────────────────────────────────────

async def settings_callback(bot: Client, cmd: CallbackQuery):
    """Handle all stg_ prefixed callbacks."""
    cb = cmd.data
    user_id = cmd.from_user.id

    if int(user_id) != Config.BOT_OWNER:
        await cmd.answer("❌ Not authorized!", show_alert=True)
        return

    # ── Main menu ──
    if cb == "stg_main":
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Toggle: Protect Content ──
    elif cb == "stg_tog_protect":
        current = await db.get_setting('protect_content', Config.PROTECT_CONTENT)
        new_val = not bool(current)
        await db.set_setting('protect_content', new_val)
        Config.PROTECT_CONTENT = new_val
        await cmd.answer(f"Protect Content: {tick(new_val)}", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Toggle: File Stream ──
    elif cb == "stg_tog_stream":
        current = await db.get_setting('stream_enabled', Config.STREAM_ENABLED)
        new_val = not bool(current)
        await db.set_setting('stream_enabled', new_val)
        Config.STREAM_ENABLED = new_val
        await cmd.answer(f"File Stream: {tick(new_val)}", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Toggle: Token Verify ──
    elif cb == "stg_tog_token":
        current = await db.get_setting('token_verification', Config.TOKEN_VERIFICATION)
        new_val = not bool(current)
        await db.set_setting('token_verification', new_val)
        Config.TOKEN_VERIFICATION = new_val
        await cmd.answer(f"Token Verify: {tick(new_val)}", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Toggle: URL Shortener ──
    elif cb == "stg_tog_shortener":
        current = await db.get_setting('url_shortener', Config.URL_SHORTENER)
        new_val = not bool(current)
        await db.set_setting('url_shortener', new_val)
        Config.URL_SHORTENER = new_val
        await cmd.answer(f"URL Shortener: {tick(new_val)}", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Auto Delete menu ──
    elif cb == "stg_autodel_menu":
        auto_del = await db.get_setting('auto_delete_time', Config.AUTO_DELETE_TIME)
        auto_del = int(auto_del) if auto_del else 0
        await cmd.message.edit(
            f"⏱ **Auto Delete Settings**\n\nCurrent: `{auto_del}s` {tick(auto_del > 0)}\n\nChoose duration:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("60s", callback_data="stg_autodel_set_60"),
                    InlineKeyboardButton("120s", callback_data="stg_autodel_set_120"),
                    InlineKeyboardButton("300s", callback_data="stg_autodel_set_300"),
                ],
                [
                    InlineKeyboardButton("600s", callback_data="stg_autodel_set_600"),
                    InlineKeyboardButton("1800s", callback_data="stg_autodel_set_1800"),
                    InlineKeyboardButton("3600s", callback_data="stg_autodel_set_3600"),
                ],
                [InlineKeyboardButton("✏️ Custom Value", callback_data="stg_autodel_custom")],
                [InlineKeyboardButton("🚫 Disable", callback_data="stg_autodel_set_0")],
                [InlineKeyboardButton("« Back", callback_data="stg_main")],
            ])
        )

    elif cb.startswith("stg_autodel_set_"):
        val = int(cb.split("_")[-1])
        await db.set_setting('auto_delete_time', val)
        Config.AUTO_DELETE_TIME = val
        label = f"`{val}s`" if val > 0 else "Disabled"
        await cmd.answer(f"Auto Delete set to {label}", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    elif cb == "stg_autodel_custom":
        pending_settings[user_id] = 'autodel'
        await cmd.message.edit(
            "⏱ **Set Custom Auto Delete Time**\n\n"
            "Send number of seconds.\nExample: `180` = 3 minutes\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="stg_autodel_menu")]
            ])
        )

    # ── Custom Caption menu ──
    elif cb == "stg_caption_menu":
        caption = await db.get_setting('custom_caption', Config.CUSTOM_CAPTION)
        cap_display = f"`{caption[:80]}...`" if caption and len(caption) > 80 else (f"`{caption}`" if caption else "Not set")
        await cmd.message.edit(
            f"✍️ **Custom Caption**\n\nCurrent: {cap_display}\n\n"
            "Variables: `{{filename}}` `{{filesize}}` `{{caption}}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Caption", callback_data="stg_caption_set")],
                [InlineKeyboardButton("🗑 Clear Caption", callback_data="stg_caption_clear")],
                [InlineKeyboardButton("« Back", callback_data="stg_main")],
            ])
        )

    elif cb == "stg_caption_set":
        pending_settings[user_id] = 'caption'
        await cmd.message.edit(
            "✍️ **Set Custom Caption**\n\n"
            "Send your caption text.\n"
            "Variables: `{{filename}}` `{{filesize}}` `{{caption}}`\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="stg_caption_menu")]
            ])
        )

    elif cb == "stg_caption_clear":
        await db.set_setting('custom_caption', None)
        Config.CUSTOM_CAPTION = None
        await cmd.answer("✅ Caption cleared!", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── Force Sub menu ──
    elif cb == "stg_forcesub_menu":
        force_sub = await db.get_setting('updates_channel', Config.UPDATES_CHANNEL)
        await cmd.message.edit(
            f"📢 **Force Subscribe**\n\nCurrent: `{force_sub or 'Not set'}`\n\n"
            "Set a channel username or ID.\nExample: `@MyChannel` or `-1001234567890`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set Channel", callback_data="stg_forcesub_set")],
                [InlineKeyboardButton("🗑 Remove Channel", callback_data="stg_forcesub_clear")],
                [InlineKeyboardButton("« Back", callback_data="stg_main")],
            ])
        )

    elif cb == "stg_forcesub_set":
        pending_settings[user_id] = 'forcesub'
        await cmd.message.edit(
            "📢 **Set Force Subscribe Channel**\n\n"
            "Send channel username or ID.\n"
            "Example: `@MyChannel` or `-1001234567890`\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="stg_forcesub_menu")]
            ])
        )

    elif cb == "stg_forcesub_clear":
        await db.set_setting('updates_channel', None)
        Config.UPDATES_CHANNEL = None
        await cmd.answer("✅ Force sub removed!", show_alert=False)
        text, keyboard = await build_settings_menu()
        await cmd.message.edit(text, reply_markup=keyboard)

    # ── URL Shortener menu ──
    elif cb == "stg_shortener_menu":
        shortener = await db.get_setting('url_shortener', Config.URL_SHORTENER)
        api = await db.get_setting('url_shortener_api', Config.URL_SHORTENER_API)
        website = await db.get_setting('url_shortener_website', Config.URL_SHORTENER_WEBSITE)
        await cmd.message.edit(
            f"🔗 **URL Shortener**\n\n"
            f"Status: {tick(shortener)}\n"
            f"Website: `{website or 'Not set'}`\n"
            f"API Key: `{'Set ✅' if api else 'Not set ❌'}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'🔴 Disable' if shortener else '🟢 Enable'}", callback_data="stg_tog_shortener")],
                [InlineKeyboardButton("✏️ Set Website", callback_data="stg_shortener_website")],
                [InlineKeyboardButton("🔑 Set API Key", callback_data="stg_shortener_api")],
                [InlineKeyboardButton("« Back", callback_data="stg_main")],
            ])
        )

    elif cb == "stg_shortener_website":
        pending_settings[user_id] = 'shortener_website'
        await cmd.message.edit(
            "🔗 **Set Shortener Website**\n\n"
            "Send the website domain.\nExample: `shortxlinks.com`\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="stg_shortener_menu")]
            ])
        )

    elif cb == "stg_shortener_api":
        pending_settings[user_id] = 'shortener_api'
        await cmd.message.edit(
            "🔑 **Set Shortener API Key**\n\n"
            "Send your API key.\n\n"
            "Send /cancel to cancel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back", callback_data="stg_shortener_menu")]
            ])
        )

    # ── Clone Bot Info ──
    elif cb == "stg_clone_info":
        await cmd.message.edit(
            "🤖 **My Clone Bot**\n\n"
            "**How to clone your bot?**\n"
            "Send the /clone command, forward your bot token from BotFather, "
            "and I will create your bot. It only takes a few moments!\n\n"
            "**How to customize your clone?**\n"
            "You can manage your clone bot using the /mybot command.\n\n"
            "With /mybot, you can:\n"
            "• Set a custom **Start Photo**\n"
            "• Set a custom **Start Message**\n"
            "• Set a custom **File Caption**\n"
            "• Add a **Backup Channel** button\n"
            "• Change the **Default Language**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Manage Clone (/mybot)", callback_data="stg_clone_info")],
                [InlineKeyboardButton("« Back", callback_data="stg_main")],
            ])
        )

    # ── Full Status ──
    elif cb == "stg_status":
        auto_del = await db.get_setting('auto_delete_time', Config.AUTO_DELETE_TIME)
        caption = await db.get_setting('custom_caption', Config.CUSTOM_CAPTION)
        protect = await db.get_setting('protect_content', Config.PROTECT_CONTENT)
        stream = await db.get_setting('stream_enabled', Config.STREAM_ENABLED)
        shortener = await db.get_setting('url_shortener', Config.URL_SHORTENER)
        token = await db.get_setting('token_verification', Config.TOKEN_VERIFICATION)
        force_sub = await db.get_setting('updates_channel', Config.UPDATES_CHANNEL)
        api = await db.get_setting('url_shortener_api', Config.URL_SHORTENER_API)
        website = await db.get_setting('url_shortener_website', Config.URL_SHORTENER_WEBSITE)
        auto_del = int(auto_del) if auto_del else 0

        await cmd.message.edit(
            "📊 **Full Bot Status**\n\n"
            f"◆ **Auto Delete:** `{auto_del}s` {tick(auto_del > 0)}\n"
            f"◆ **Custom Caption:** {tick(bool(caption))}\n"
            f"◆ **Force Sub:** `{force_sub or 'Not set'}` {tick(bool(force_sub))}\n"
            f"◆ **Protect Content:** {tick(protect)}\n"
            f"◆ **File Stream:** {tick(stream)}\n"
            f"◆ **URL Shortener:** {tick(shortener)}\n"
            f"   ↳ Website: `{website or 'Not set'}`\n"
            f"   ↳ API Key: `{'Set ✅' if api else 'Not set ❌'}`\n"
            f"◆ **Token Verify:** {tick(token)}\n"
            f"◆ **Bot Username:** @{Config.BOT_USERNAME}\n"
            f"◆ **Stream FQDN:** `{Config.STREAM_FQDN or 'Not set'}`\n"
            f"◆ **Worker URL:** `{Config.WORKER_URL or 'Not set'}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back to Settings", callback_data="stg_main")]
            ])
        )

    try:
        await cmd.answer()
    except Exception:
        pass


# ── Text input handler ─────────────────────────────────────────────────────────

async def handle_settings_input(bot: Client, m: Message) -> bool:
    """
    Called from bot.py group=0 handler.
    If owner sent text for a pending setting, handle it.
    Returns True if message was consumed, False otherwise.
    """
    user_id = m.from_user.id

    # Only intercept if there's a pending setting for this user
    if user_id not in pending_settings:
        return False

    # /cancel aborts input
    if m.text and m.text.strip() == "/cancel":
        pending_settings.pop(user_id, None)
        text, keyboard = await build_settings_menu()
        await m.reply_text(text, reply_markup=keyboard, quote=True)
        return True

    action = pending_settings.pop(user_id, None)

    if action == 'autodel':
        try:
            val = int(m.text.strip())
            if val < 0:
                raise ValueError
            await db.set_setting('auto_delete_time', val)
            Config.AUTO_DELETE_TIME = val
            label = f"`{val}s`" if val > 0 else "disabled"
            await m.reply_text(f"✅ Auto Delete set to {label}.", quote=True)
        except (ValueError, AttributeError):
            await m.reply_text("❌ Invalid. Send a positive number like `120`.", quote=True)

    elif action == 'caption':
        caption = m.text.strip() if m.text else None
        if caption:
            await db.set_setting('custom_caption', caption)
            Config.CUSTOM_CAPTION = caption
            await m.reply_text("✅ Custom caption saved!", quote=True)
        else:
            await m.reply_text("❌ Invalid. Send text.", quote=True)

    elif action == 'forcesub':
        channel = m.text.strip() if m.text else None
        if channel:
            await db.set_setting('updates_channel', channel)
            Config.UPDATES_CHANNEL = channel
            await m.reply_text(f"✅ Force sub channel set to `{channel}`!", quote=True)
        else:
            await m.reply_text("❌ Invalid.", quote=True)

    elif action == 'shortener_website':
        website = m.text.strip() if m.text else None
        if website:
            await db.set_setting('url_shortener_website', website)
            Config.URL_SHORTENER_WEBSITE = website
            await m.reply_text(f"✅ Shortener website set to `{website}`!", quote=True)
        else:
            await m.reply_text("❌ Invalid.", quote=True)

    elif action == 'shortener_api':
        api = m.text.strip() if m.text else None
        if api:
            await db.set_setting('url_shortener_api', api)
            Config.URL_SHORTENER_API = api
            await m.reply_text("✅ Shortener API key saved!", quote=True)
        else:
            await m.reply_text("❌ Invalid.", quote=True)

    # Show menu again after handling
    text, keyboard = await build_settings_menu()
    await m.reply_text(text, reply_markup=keyboard, quote=True)
    return True


# ── Existing admin handlers (unchanged from original) ──────────────────────────

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
            "**Usage:** `/addadmin user_id`\n\nExample: `/addadmin 1234567`",
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
            "**Usage:** `/removeadmin user_id`\n\nExample: `/removeadmin 1234567`",
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
