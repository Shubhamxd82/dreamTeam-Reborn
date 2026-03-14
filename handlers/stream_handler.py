# Stream/Download Link Handler — Feature 10

import logging
import mimetypes
from aiohttp import web
from pyrogram import Client
from pyrogram.types import Message
from configs import Config
from handlers.helpers import str_to_b64, b64_to_str, humanbytes

logging.basicConfig(level=logging.INFO)

routes = web.RouteTableDef()
bot_client = None


def set_bot_client(client: Client):
    """Set the bot client for streaming."""
    global bot_client
    bot_client = client


@routes.get("/")
async def root_handler(request):
    return web.json_response({
        "status": "alive",
        "bot": Config.BOT_USERNAME,
        "stream": Config.STREAM_ENABLED
    })


@routes.get("/watch/{encoded_id}")
async def stream_handler(request):
    """Stream a file directly in browser."""
    try:
        encoded_id = request.match_info["encoded_id"]
        try:
            file_id = int(b64_to_str(encoded_id))
        except:
            file_id = int(encoded_id)

        message = await bot_client.get_messages(
            chat_id=Config.DB_CHANNEL,
            message_ids=file_id
        )

        if not message or not message.media:
            return web.Response(text="File not found", status=404)

        # Get file info
        media = message.document or message.video or message.audio
        if not media:
            return web.Response(text="Not a downloadable file", status=400)

        file_name = getattr(media, 'file_name', 'file')
        file_size = getattr(media, 'file_size', 0)
        mime_type = getattr(media, 'mime_type', 'application/octet-stream')

        # Handle range requests for video streaming
        range_header = request.headers.get('Range')
        offset = 0
        limit = file_size

        if range_header:
            range_spec = range_header.replace('bytes=', '')
            parts = range_spec.split('-')
            offset = int(parts[0]) if parts[0] else 0
            limit = int(parts[1]) + 1 if parts[1] else file_size

        # Create streaming response
        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'inline; filename="{file_name}"',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(limit - offset),
        }

        if range_header:
            headers['Content-Range'] = f'bytes {offset}-{limit - 1}/{file_size}'
            response = web.StreamResponse(
                status=206,
                headers=headers
            )
        else:
            response = web.StreamResponse(
                status=200,
                headers=headers
            )

        await response.prepare(request)

        async for chunk in bot_client.stream_media(message, offset=offset // (1024 * 1024), limit=(limit - offset) // (1024 * 1024) + 1):
            await response.write(chunk)

        return response

    except Exception as e:
        logging.error(f"Stream error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


@routes.get("/dl/{encoded_id}")
async def download_handler(request):
    """Force download a file."""
    try:
        encoded_id = request.match_info["encoded_id"]
        try:
            file_id = int(b64_to_str(encoded_id))
        except:
            file_id = int(encoded_id)

        message = await bot_client.get_messages(
            chat_id=Config.DB_CHANNEL,
            message_ids=file_id
        )

        if not message or not message.media:
            return web.Response(text="File not found", status=404)

        media = message.document or message.video or message.audio
        file_name = getattr(media, 'file_name', 'file')
        file_size = getattr(media, 'file_size', 0)
        mime_type = getattr(media, 'mime_type', 'application/octet-stream')

        headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{file_name}"',
            'Content-Length': str(file_size),
        }

        response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)

        async for chunk in bot_client.stream_media(message):
            await response.write(chunk)

        return response

    except Exception as e:
        logging.error(f"Download error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


def get_stream_link(file_id: int) -> str:
    """Generate stream link for a file."""
    encoded = str_to_b64(str(file_id))
    base_url = Config.get_stream_base_url()
    return f"{base_url}/watch/{encoded}"


def get_download_link(file_id: int) -> str:
    """Generate download link for a file."""
    encoded = str_to_b64(str(file_id))
    base_url = Config.get_stream_base_url()
    return f"{base_url}/dl/{encoded}"


async def start_stream_server():
    """Start the aiohttp web server for streaming."""
    if not Config.STREAM_ENABLED:
        return

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.STREAM_PORT)
    await site.start()
    logging.info(f"Stream server started on port {Config.STREAM_PORT}")
