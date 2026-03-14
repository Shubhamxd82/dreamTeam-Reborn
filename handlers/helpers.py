# (c) @harshil8981 — Enhanced V2

import aiohttp
import logging
from base64 import standard_b64encode, standard_b64decode
from configs import Config
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)


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
        # FIX: Added timeout to prevent hanging
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
                    # Some APIs return different key names
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
