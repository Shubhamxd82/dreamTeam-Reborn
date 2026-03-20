# Stream/Download Link Handler — Feature 10

import logging
from aiohttp import web
from pyrogram import Client
from configs import Config
from handlers.helpers import str_to_b64, b64_to_str, humanbytes

logging.basicConfig(level=logging.INFO)

routes = web.RouteTableDef()
bot_client = None

# ── Embedded HTML templates ────────────────────────────────────────────────────

STREAM_HTML = """<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8" />
  <title>BOT_NAME_PLACEHOLDER | FILE_NAME_PLACEHOLDER</title>
  <link rel="icon" href="https://telegra.ph/file/5a53e66bb148003666d62.jpg" type="image/x-icon">
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />

  <!-- Fonts & Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
  <!-- Plyr & Bootstrap -->
  <link rel="stylesheet" href="https://cdn.plyr.io/3.6.12/plyr.css" />
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />

  <style>
    :root {
      --primary-color: #00f0ff;
      --secondary-color: #7000ff;
      --bg-gradient: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      --glass-bg: rgba(255, 255, 255, 0.05);
      --glass-border: 1px solid rgba(255, 255, 255, 0.1);
      --card-radius: 16px;
    }
    body {
      background: var(--bg-gradient);
      color: #fff;
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0f0c29; }
    ::-webkit-scrollbar-thumb { background: var(--secondary-color); border-radius: 4px; }

    .navbar {
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .navbar-brand {
      color: var(--primary-color) !important;
      font-weight: 600;
      letter-spacing: 1px;
    }
    .player-wrapper {
      background: #000;
      border-radius: var(--card-radius);
      overflow: hidden;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
      margin-top: 20px;
      border: var(--glass-border);
    }
    .plyr--video .plyr__control--overlaid,
    .plyr--video .plyr__control:hover { background: var(--secondary-color); }
    .plyr--full-ui input[type=range] { color: var(--primary-color); }

    .btn-custom {
      border: none;
      border-radius: 12px;
      padding: 12px 20px;
      font-weight: 500;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      text-transform: uppercase;
      font-size: 0.9rem;
      letter-spacing: 0.5px;
      cursor: pointer;
    }
    .btn-custom:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); filter: brightness(1.2); }
    .btn-mx       { background: linear-gradient(45deg, #2980b9, #2c3e50); color: white; }
    .btn-vlc      { background: linear-gradient(45deg, #e67e22, #d35400); color: white; }
    .btn-download { background: linear-gradient(45deg, #00b09b, #96c93d); color: white; font-weight: 600; width: 100%; }
    .btn-telegram { background: linear-gradient(45deg, #0088cc, #36aee2); color: white; width: 100%; }
    .btn-share    { background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #aaa; width: 100%; }
    .btn-share:hover { background: rgba(255,255,255,0.1); color: white; }

    .glass-card {
      background: var(--glass-bg);
      backdrop-filter: blur(12px);
      border: var(--glass-border);
      border-radius: var(--card-radius);
      padding: 20px;
      margin-bottom: 20px;
    }
    .file-info-title { color: var(--primary-color); font-size: 1.1rem; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; }
    .info-item  { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .info-label { color: #888; }
    .info-value { color: #fff; font-family: monospace; }

    footer { margin-top: auto; background: rgba(0,0,0,0.4); padding: 15px; text-align: center; font-size: 0.8rem; color: #666; }
    footer a { color: var(--primary-color); text-decoration: none; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    main { animation: fadeIn 0.8s ease-out; }

    .telegram-float {
      position: fixed; left: 18px; bottom: 90px;
      width: 56px; height: 56px;
      background: #ffffff; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      text-decoration: none !important; border: none; outline: none;
      font-size: 28px; z-index: 9999;
      box-shadow: 0 0 18px rgba(0, 136, 204, 0.6);
      transition: .3s ease;
    }
    .telegram-float i { color: #0088CC; line-height: 1; }
    .telegram-float:hover { transform: scale(1.15); box-shadow: 0 0 30px rgba(0,136,204,1); }
  </style>
</head>

<body>
  <!-- Header -->
  <nav class="navbar navbar-dark">
    <div class="container">
      <span class="navbar-brand mb-0 h1"><i class="fa-solid fa-robot me-2"></i>BOT_NAME_PLACEHOLDER</span>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="container py-4">

    <!-- Player -->
    <div class="player-wrapper mb-4">
      <video id="myVideo" src="STREAM_URL_PLACEHOLDER" class="w-100" controls>
        Your browser does not support the video tag.
      </video>
    </div>

    <!-- External Players -->
    <div class="d-flex flex-wrap gap-2 mb-3">
      <a onclick="mx_player()" class="btn btn-custom btn-mx flex-fill" title="MX Player">
        <img src="https://i.ibb.co/41WvtQ3/mx.png" alt="MX" style="height:22px;"> MX Player
      </a>
      <a onclick="vlc_player()" class="btn btn-custom btn-vlc flex-fill" title="VLC Player">
        <img src="https://i.ibb.co/px6fQs1/vlc.png" alt="VLC" style="height:22px;"> VLC Player
      </a>
    </div>

    <!-- Actions -->
    <div class="row g-3 mb-3">
      <div class="col-md-6">
        <a onclick="streamDownload()" class="btn btn-custom btn-download">
          <i class="fa-solid fa-cloud-arrow-down"></i> &nbsp; Direct Download
        </a>
      </div>
      <div class="col-md-6">
        <a onclick="showLinkModal('TG_BUTTON_PLACEHOLDER')" class="btn btn-custom btn-telegram">
          <i class="fa-brands fa-telegram"></i> &nbsp; Get File in Telegram
        </a>
      </div>
    </div>

    <!-- File Info -->
    <div class="glass-card">
      <div class="file-info-title"><i class="fa-solid fa-circle-info me-2"></i> File Details</div>
      <div style="margin-bottom: 8px; word-break: break-word;">
        <span class="info-label">Filename: </span>
        <span class="info-value">FILE_NAME_PLACEHOLDER</span>
      </div>
      <div style="margin-bottom: 8px;">
        <span class="info-label">Size</span>
        <span class="info-value">FILE_SIZE_PLACEHOLDER</span>
      </div>
      <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
        <span class="info-label">Powered by: </span>
        <span class="info-value"><a href="https://t.me/Shubhlinks" target="_blank" style="color: var(--primary-color); text-decoration: none;">Shubhlinks</a></span>
      </div>
    </div>
 
    <!-- Share -->
    <button onclick="shareButton()" class="btn btn-custom btn-share">
      <i class="fa-solid fa-share-nodes"></i> &nbsp; Share with Friends
    </button>

    <!-- Disclaimer -->
    <div class="mt-4 text-center" style="font-size: 0.75rem; color: #555;">
      DISCLAIMER_PLACEHOLDER <br>
      <a href="REPORT_LINK_PLACEHOLDER" style="color: #666;">Report Issue</a>
    </div>

  </main>

  <!-- Footer -->
  <footer>
    <p>&copy; 2025 <a href="https://t.me/Shubhlinks" target="_blank" style="color:#999; font-weight:600; text-decoration:none;">Shubhlinks</a>. All rights reserved.</p>
  </footer>

  <!-- Scripts -->
  <script src="https://cdn.plyr.io/3.6.12/plyr.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", () => {
      const player = new Plyr("#myVideo", {
        controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'captions', 'settings', 'pip', 'airplay', 'fullscreen'],
        settings: ['captions', 'quality', 'speed']
      });
    });

    var streamUrl = 'STREAM_URL_PLACEHOLDER';
    var downloadUrl = 'DOWNLOAD_URL_PLACEHOLDER';

    function mx_player() {
      var clean = streamUrl.replace(/^https?:\\/\\//, '');
      window.location.href = 'intent://' + clean + '#Intent;scheme=https;package=com.mxtech.videoplayer.ad;action=android.intent.action.VIEW;type=video/*;end';
    }
    function vlc_player() {
      var clean = streamUrl.replace(/^https?:\\/\\//, '');
      window.location.href = 'intent://' + clean + '#Intent;scheme=https;package=org.videolan.vlc;action=android.intent.action.VIEW;type=video/*;end';
    }
    function streamDownload() {
      window.location.href = downloadUrl;
    }
    function showLinkModal(url) {
      if (url) window.open(url, '_blank');
    }
    function shareButton() {
      if (navigator.share) {
        navigator.share({
          title: 'FILE_NAME_PLACEHOLDER',
          text: 'Watch this video on BOT_NAME_PLACEHOLDER',
          url: window.location.href,
        });
      } else {
        navigator.clipboard.writeText(window.location.href);
        alert('Link copied to clipboard!');
      }
    }
  </script>

  <!-- Telegram Float Button -->
  <a href="https://t.me/UHDBots" class="telegram-float" target="_blank" aria-label="Telegram">
    <i class="fa-brands fa-telegram fa-beat"></i>
  </a>
</body>
</html>"""

DOWNLOAD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Download File</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root{--bg:#080a0f;--surface:#0e1118;--surface2:#141820;--border:rgba(255,255,255,0.06);--accent:#e63946;--accent2:#ff6b6b;--text:#f0f0f0;--muted:#6b7280;--glow:rgba(230,57,70,0.35)}
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px 16px}
  body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 70% 50% at 50% 0%,rgba(230,57,70,0.1) 0%,transparent 60%);pointer-events:none}
  .card{position:relative;z-index:1;width:100%;max-width:440px;background:var(--surface);border:1px solid var(--border);border-radius:20px;overflow:hidden;box-shadow:0 40px 80px rgba(0,0,0,0.5);animation:rise 0.7s cubic-bezier(0.16,1,0.3,1) both}
  .card-top{height:3px;background:linear-gradient(90deg,var(--accent),var(--accent2),transparent)}
  .card-body{padding:32px}
  .icon-wrap{width:64px;height:64px;background:rgba(230,57,70,0.1);border:1px solid rgba(230,57,70,0.2);border-radius:16px;display:flex;align-items:center;justify-content:center;margin-bottom:24px}
  .icon-wrap svg{width:28px;height:28px;color:var(--accent);fill:none;stroke:currentColor;stroke-width:1.5}
  .title{font-family:'Bebas Neue',sans-serif;font-size:32px;letter-spacing:2px;line-height:1;margin-bottom:6px}
  .subtitle{font-size:13px;color:var(--muted);margin-bottom:28px}
  .file-card{background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:24px;display:flex;align-items:center;gap:14px}
  .file-icon{width:42px;height:42px;background:rgba(230,57,70,0.08);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .file-icon svg{width:20px;height:20px;fill:none;stroke:var(--accent2);stroke-width:1.5}
  .file-details{flex:1;min-width:0}
  .file-name{font-size:14px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px}
  .file-size{font-size:11px;color:var(--muted)}
  .secure-badge{display:flex;align-items:center;gap:4px;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);border-radius:6px;padding:4px 8px;flex-shrink:0}
  .secure-badge svg{width:11px;height:11px;fill:none;stroke:#4ade80;stroke-width:2}
  .secure-badge span{font-size:10px;color:#4ade80;font-weight:600;letter-spacing:0.5px;text-transform:uppercase}
  .download-btn{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;padding:16px;background:var(--accent);color:white;text-decoration:none;border-radius:12px;font-size:15px;font-weight:600;transition:all 0.25s ease;box-shadow:0 8px 30px var(--glow)}
  .download-btn:hover{background:var(--accent2);transform:translateY(-2px);box-shadow:0 12px 40px var(--glow)}
  .download-btn svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2}
  .divider{display:flex;align-items:center;gap:12px;margin:20px 0}
  .divider::before,.divider::after{content:'';flex:1;height:1px;background:var(--border)}
  .divider span{font-size:11px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
  .features{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .feature{display:flex;align-items:center;gap:8px;padding:10px 12px;background:rgba(255,255,255,0.02);border:1px solid var(--border);border-radius:8px}
  .feature svg{width:13px;height:13px;fill:none;stroke:var(--accent2);stroke-width:2;flex-shrink:0}
  .feature span{font-size:11px;color:var(--muted)}
  .card-footer{padding:16px 32px;border-top:1px solid var(--border);display:flex;align-items:center;justify-content:center}
  .card-footer span{font-size:11px;color:var(--muted)}
  .card-footer strong{color:var(--accent2);font-weight:600}
  @keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:translateY(0)}}
  @media(max-width:480px){.card-body{padding:24px}.features{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="card">
  <div class="card-top"></div>
  <div class="card-body">
    <div class="icon-wrap"><svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg></div>
    <div class="title">Your File</div>
    <div class="subtitle">Ready to download &#8212; secured &amp; delivered instantly</div>
    <div class="file-card">
      <div class="file-icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
      <div class="file-details">
        <div class="file-name">Secure File</div>
        <div class="file-size">Served via Telegram CDN</div>
      </div>
      <div class="secure-badge">
        <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span>Safe</span>
      </div>
    </div>
    <a href="FILE_URL_PLACEHOLDER" class="download-btn">
      <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
      Download Now
    </a>
    <div class="divider"><span>Includes</span></div>
    <div class="features">
      <div class="feature"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg><span>Fast delivery</span></div>
      <div class="feature"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg><span>Secure transfer</span></div>
      <div class="feature"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg><span>No expiry</span></div>
      <div class="feature"><svg viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.8 19.79 19.79 0 01.22 1.18 2 2 0 012.18 0h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.91 7.91"/></svg><span>Direct link</span></div>
    </div>
  </div>
  <div class="card-footer"><span>Powered by <strong>StreamVault Bot</strong> &nbsp;&middot;&nbsp; Telegram File CDN</span></div>
</div>
</body>
</html>"""

# ── Bot client ─────────────────────────────────────────────────────────────────

def set_bot_client(client: Client):
    global bot_client
    bot_client = client


# ── Helpers ────────────────────────────────────────────────────────────────────

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


# ── Routes ─────────────────────────────────────────────────────────────────────

@routes.get("/watch/{encoded_id}")
async def watch_page_handler(request):
    """Serve the HTML player page."""
    try:
        encoded_id = request.match_info["encoded_id"]
        base_url = Config.get_stream_base_url()
        stream_url = f"{base_url}/stream/{encoded_id}"
        download_url = f"{base_url}/dl/{encoded_id}"

        # Fetch file info to populate name and size on the page
        try:
            msg_id = int(b64_to_str(encoded_id))
        except Exception:
            msg_id = int(encoded_id)

        file_name = "Unknown File"
        file_size_str = "Unknown"
        message = await get_media_message(msg_id)
        if message:
            name, size, _, _ = get_media_info(message)
            if name:
                file_name = name
            if size:
                file_size_str = humanbytes(size)

        # ── Fill all placeholders ──────────────────────────────────────────────
        # TODO: Replace the values below with your own branding / config values
        bot_name        = "StreamVault"          # e.g. Config.BOT_USERNAME
        tg_button_url   = ""                     # e.g. f"https://t.me/{Config.BOT_USERNAME}"
        disclaimer_text = ""                     # e.g. "For personal use only."
        report_link_url = "#"                    # e.g. "https://t.me/YourSupportBot"

        html = STREAM_HTML.replace("STREAM_URL_PLACEHOLDER",   stream_url)
        html = html.replace("DOWNLOAD_URL_PLACEHOLDER",        download_url)
        html = html.replace("FILE_NAME_PLACEHOLDER",           file_name)
        html = html.replace("FILE_SIZE_PLACEHOLDER",           file_size_str)
        html = html.replace("BOT_NAME_PLACEHOLDER",            bot_name)
        html = html.replace("TG_BUTTON_PLACEHOLDER",           tg_button_url)
        html = html.replace("DISCLAIMER_PLACEHOLDER",          disclaimer_text)
        html = html.replace("REPORT_LINK_PLACEHOLDER",         report_link_url)

        return web.Response(text=html, content_type="text/html")
    except Exception as e:
        logging.error(f"Watch page error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


@routes.get("/stream/{encoded_id}")
async def stream_handler(request):
    """Stream raw video bytes — called by the HTML <video> tag."""
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

        async for chunk in bot_client.stream_media(message, offset=start, limit=content_length):
            try:
                await response.write(chunk)
            except (ConnectionResetError, ConnectionError, Exception):
                return response

        await response.write_eof()
        return response

    except (ConnectionResetError, ConnectionError):
        return web.Response(status=499)
    except Exception as e:
        logging.error(f"Stream error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


@routes.get("/dl/{encoded_id}")
async def download_handler(request):
    """Serve download page on browser visit; raw file on direct/non-html request."""
    try:
        encoded_id = request.match_info["encoded_id"]
        accept = request.headers.get("Accept", "")

        # Browser visit → show premium download page
        if "text/html" in accept and "direct" not in request.query:
            base_url = Config.get_stream_base_url()
            file_url = f"{base_url}/dl/{encoded_id}?direct=1"
            html = DOWNLOAD_HTML.replace("FILE_URL_PLACEHOLDER", file_url)
            return web.Response(text=html, content_type="text/html")

        # Actual file download
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
            try:
                await response.write(chunk)
            except (ConnectionResetError, ConnectionError):
                return response

        await response.write_eof()
        return response

    except Exception as e:
        logging.error(f"Download error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


# ── Link generators (used by send_file.py) ─────────────────────────────────────

def get_stream_link(file_id: int) -> str:
    encoded = str_to_b64(str(file_id))
    base_url = Config.get_stream_base_url()
    return f"{base_url}/watch/{encoded}"


def get_download_link(file_id: int) -> str:
    encoded = str_to_b64(str(file_id))
    base_url = Config.get_stream_base_url()
    return f"{base_url}/dl/{encoded}"


# ── Server startup ─────────────────────────────────────────────────────────────

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
