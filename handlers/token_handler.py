# Token/Verify System — Feature 7

import time
import secrets
import logging
from configs import Config
from handlers.database import db
from handlers.helpers import get_token_shortlink, format_time_seconds
from handlers.languages import get_text

logging.basicConfig(level=logging.INFO)


async def check_token(user_id: int) -> bool:
    """Check if user has a valid (non-expired) token."""
    if not Config.TOKEN_VERIFICATION:
        return True

    # Admins bypass token
    if await db.is_admin(user_id):
        return True

    token_data = await db.get_token_data(user_id)
    if not token_data or not token_data.get("is_verified", False):
        return False

    token_time = token_data.get("token_time", 0)
    if token_time == 0:
        return False

    if (time.time() - token_time) > Config.TOKEN_TIMEOUT:
        await db.reset_token(user_id)
        return False

    return True


async def generate_token_link(bot_username: str, user_id: int) -> tuple:
    """Generate a verification link for the user. Returns (short_url, token)."""
    token = secrets.token_hex(5)  # 10 char hex token
    verify_url = f"https://t.me/{bot_username}?start=verify-{token}-{user_id}"
    short_url = await get_token_shortlink(verify_url)
    return short_url, token


async def verify_user_token(user_id: int, token: str) -> bool:
    """Verify and activate user's token."""
    try:
        await db.update_token(user_id, token, int(time.time()))
        return True
    except Exception as e:
        logging.error(f"Token verification error for user {user_id}: {e}")
        return False


async def get_token_msg(user_id: int, bot_username: str) -> tuple:
    """Get the verification message, short link, and token for a user.
    Returns: (text, short_link, token)
    """
    lang = await db.get_language(user_id)
    time_str = format_time_seconds(Config.TOKEN_TIMEOUT)
    short_link, token = await generate_token_link(bot_username, user_id)
    text = get_text(lang, "token_verify").format(time=time_str)
    return text, short_link, token
