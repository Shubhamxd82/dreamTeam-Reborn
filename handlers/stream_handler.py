# Stream/Download Link Handler — Feature 10

import logging
import math
from aiohttp import web
from pyrogram import Client
from configs import Config
from handlers.helpers import str_to_b64, b64_to_str, humanbytes

logging.basicConfig(level=logging.INFO)

routes = web.RouteTableDef()
bot_client = None


def set_bot_client(client: Client):
    global bot_client
    bot_client = client


@routes.get("/")
async def root_handler(request):
    return web.json_response({
        "status": "alive",
        "bot": Config.BOT_USERNAME,
        "stream": Config.STREAM_ENABLED
    })


async def get_media_message(file_id: int):
    try:
        message = await bot_client.get_messages(
            chat_id=Config.DB_CHANNEL,
            message_ids=file_id
        )
        if message and message.media:
            return message
        return None
    except Exception as e:
        logging.error(f"Get media message error: {e}")
        return None


def get_media_info(message):
    media = message.document or message.video or message.audio
    if not media:
        return None, None, None, None

    file_name = getattr(media, 'file_name', None) or 'file'
    file_size = getattr(media, 'file_size', 0) or 0
    mime_type = getattr(media, 'mime_type', None) or 'application/octet-stream'
    file_id = media.file_id

    return file_name, file_size, mime_type, file_id


@routes.get("/watch/{encoded_id}")
async def stream_handler(request):
    """True streaming — sends chunks as they arrive from Telegram."""
    try:
        encoded_id = request.match_info["encoded_id"]
        try:
            msg_id = int(b64_to_str(encoded_id))
        except Exception:
            msg_id = int(encoded_id)

        message = await get_media_message(msg_id)
        if not message:
            return web.Response(text="File not found", status=404)

        file_name, file_size, mime_type, _ = get_media_info(message)
        if file_name is None:
            return web.Response(text="Not a downloadable file", status=400)

        range_header = request.headers.get('Range')

        if range_header:
            range_spec = range_header.replace('bytes=', '')
            parts = range_spec.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            status = 206
        else:
            start = 0
            end = file_size - 1
            status = 200

        content_length = end - start + 1

        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'inline; filename="{file_name}"',
            'Content-Length': str(content_length),
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {start}-{end}/{file_size}',
        }

        response = web.StreamResponse(status=status, headers=headers)
        await response.prepare(request)

        # Stream chunks directly from Telegram to browser
        async for chunk in bot_client.stream_media(message, offset=start, limit=content_length):
            await response.write(chunk)

        await response.write_eof()
        return response

    except Exception as e:
        logging.error(f"Stream error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


@routes.get("/dl/{encoded_id}")
async def download_handler(request):
    """Force download — streamed, not buffered."""
    try:
        encoded_id = request.match_info["encoded_id"]
        try:
            msg_id = int(b64_to_str(encoded_id))
        except Exception:
            msg_id = int(encoded_id)

        message = await get_media_message(msg_id)
        if not message:
            return web.Response(text="File not found", status=404)

        file_name, file_size, mime_type, _ = get_media_info(message)
        if file_name is None:
            return web.Response(text="Not a downloadable file", status=400)

        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Length': str(file_size),
            'Accept-Ranges': 'bytes',
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)

        async for chunk in bot_client.stream_media(message, offset=0, limit=file_size):
            await response.write(chunk)

        await response.write_eof()
        return response

    except Exception as e:
        logging.error(f"Download error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


def get_stream_link(file_id: int) -> str:
    encoded = str_to_b64(str(file_id))
    base_url = Config.get_stream_base_url()
    return f"{base_url}/watch/{encoded}"


def get_download_link(file_id: int) -> str:
    encoded = str_to_b64(str(file_id))
    base_url = Config.get_stream_base_url()
    return f"{base_url}/dl/{encoded}"


async def start_stream_server():
    if not Config.STREAM_ENABLED:
        return

    app = web.Application(client_max_size=50 * 1024 * 1024)
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.STREAM_PORT)
    await site.start()
    logging.info(f"Stream server started on port {Config.STREAM_PORT}")
