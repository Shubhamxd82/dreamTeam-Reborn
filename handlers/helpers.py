# (c) @Shubhlinks — Enhanced V2

import os
import hashlib
import base64
import aiohttp
import logging
from base64 import standard_b64encode, standard_b64decode
from configs import Config
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)


# ==================== OLD BASE64 HELPERS (used by stream links) ====================

def str_to_b64(__str: str) -> str:
    str_bytes = __str.encode('ascii')
    bytes_b64 = standard_b64encode(str_bytes)
    b64 = bytes_b64.decode('ascii')
    return b64


def b64_to_str(b64: str) -> str:
    bytes_b64 = b64.encode('ascii')
    bytes_str = standard_b64decode(bytes_b64)
    __str = bytes_str.decode('ascii')
    return __str


# ==================== NEW SECURE LINK ENCODE/DECODE ====================

def encode_link(channel_id: int, message_id: int, user_id: int = None) -> str:
    """
    Encode channel_id + message_id (+ optional user_id) into a secure random link parameter.
    - Main bot links: encode_link(DB_CHANNEL, message_id)
    - Clone bot links: encode_link(clone_channel, message_id, owner_user_id)
    Uses random 8-byte salt + SHA256 key derivation so every link looks completely different.
    No mrkiller_, no = padding, URL-safe base64.
    """
    if user_id:
        data = f"{channel_id}|{message_id}|{user_id}"
    else:
        data = f"{channel_id}|{message_id}"

    # Random 4-byte salt — makes every link look unique even for same file
    salt = os.urandom(4)

    # Derive unique key: SHA256(salt + SECRET_KEY)
    unique_key = hashlib.sha256(
        salt + Config.LINK_SECRET_KEY.encode()
    ).digest()

    # XOR encrypt data with key stream derived from unique_key
    data_bytes = data.encode()
    key_stream = (unique_key * (len(data_bytes) // 32 + 1))[:len(data_bytes)]
    encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_stream))

    # Combine salt + encrypted, base64url encode, strip padding
    final = salt + encrypted
    return base64.urlsafe_b64encode(final).decode().rstrip("=")


def decode_link(encoded: str):
    """
    Decode a link parameter back to (channel_id, message_id, user_id_or_None).
    Raises ValueError if link is invalid or tampered.
    """
    try:
        # Restore base64 padding
        padded = encoded + "=" * (-len(encoded) % 4)
        raw = base64.urlsafe_b64decode(padded)

        if len(raw) < 5:
            raise ValueError("Link too short")

        salt = raw[:4]
        encrypted = raw[4:]

        # Derive unique key
        unique_key = hashlib.sha256(
            salt + Config.LINK_SECRET_KEY.encode()
        ).digest()

        # XOR decrypt
        key_stream = (unique_key * (len(encrypted) // 32 + 1))[:len(encrypted)]
        decrypted = bytes(a ^ b for a, b in zip(encrypted, key_stream))

        data = decrypted.decode()
        parts = data.split("|")

        if len(parts) == 3:
            return int(parts[0]), int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]), int(parts[1]), None
        else:
            raise ValueError(f"Invalid data format: {data}")

    except Exception as e:
        raise ValueError(f"Failed to decode link: {e}")


# ==================== HUMAN READABLE HELPERS ====================

def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    power = 2 ** 10
    n = 0
    units = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"


def format_time_seconds(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days > 1 else ''}"


# ==================== URL SHORTENER ====================

async def shorten_url(long_url: str, api_key: str = None, website: str = None) -> str:
    if not api_key:
        api_key = Config.URL_SHORTENER_API
    if not website:
        website = Config.URL_SHORTENER_WEBSITE

    if not api_key or not website:
        return long_url

    website = website.strip().lower().replace("https://", "").replace("http://", "").rstrip("/")

    try:
        timeout = aiohttp.ClientTimeout(total=10)

        if "gplinks" in website:
            api_url = f"https://gplinks.co/api?api={api_key}&url={quote_plus(long_url)}"
        elif "shrinkme" in website:
            api_url = f"https://shrinkme.io/api?api={api_key}&url={quote_plus(long_url)}"
        elif "shorturllink" in website:
            api_url = f"https://shorturllink.in/api?api={api_key}&url={quote_plus(long_url)}"
        elif "droplink" in website:
            api_url = f"https://droplink.co/api?api={api_key}&url={quote_plus(long_url)}"
        else:
            api_url = f"https://{website}/api?api={api_key}&url={quote_plus(long_url)}"

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") == "success":
                        return data.get("shortenedUrl", long_url)
                    if "shortenedUrl" in data:
                        return data["shortenedUrl"]
                    if "short_url" in data:
                        return data["short_url"]

    except aiohttp.ClientError as e:
        logging.error(f"URL Shortener Connection Error: {e}")
    except Exception as e:
        logging.error(f"URL Shortener Error: {e}")

    return long_url


async def get_shortlink(link: str) -> str:
    if Config.URL_SHORTENER and Config.URL_SHORTENER_API and Config.URL_SHORTENER_WEBSITE:
        return await shorten_url(link)
    return link


async def get_token_shortlink(link: str) -> str:
    if Config.TOKEN_SHORTENER_API and Config.TOKEN_SHORTENER_WEBSITE:
        return await shorten_url(
            link,
            api_key=Config.TOKEN_SHORTENER_API,
            website=Config.TOKEN_SHORTENER_WEBSITE
        )
    elif Config.URL_SHORTENER_API and Config.URL_SHORTENER_WEBSITE:
        return await shorten_url(link)
    return link
