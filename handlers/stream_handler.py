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
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stream Video</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root { --bg:#080a0f; --surface:#0e1118; --border:rgba(255,255,255,0.06); --accent:#e63946; --accent2:#ff6b6b; --text:#f0f0f0; --muted:#6b7280; --glow:rgba(230,57,70,0.3); }
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;overflow-x:hidden}
  body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(230,57,70,0.12) 0%,transparent 60%),radial-gradient(ellipse 40% 30% at 80% 80%,rgba(230,57,70,0.06) 0%,transparent 50%);pointer-events:none;z-index:0}
  .container{position:relative;z-index:1;max-width:1000px;margin:0 auto;padding:20px 16px 40px}
  header{display:flex;align-items:center;gap:12px;padding:20px 0 32px;animation:fadeDown 0.6s ease both}
  .logo-mark{width:36px;height:36px;background:var(--accent);border-radius:8px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 20px var(--glow)}
  .logo-mark svg{width:18px;height:18px;fill:white}
  .logo-text{font-family:'Bebas Neue',sans-serif;font-size:22px;letter-spacing:2px}
  .badge{margin-left:auto;background:rgba(230,57,70,0.12);border:1px solid rgba(230,57,70,0.3);color:var(--accent2);font-size:11px;font-weight:500;padding:4px 10px;border-radius:20px;letter-spacing:1px;text-transform:uppercase}
  .video-wrapper{position:relative;border-radius:16px;overflow:hidden;background:#000;box-shadow:0 0 0 1px var(--border),0 40px 80px rgba(0,0,0,0.6),0 0 60px rgba(230,57,70,0.08);animation:fadeUp 0.7s ease 0.1s both}
  .video-wrapper::before{content:'';position:absolute;inset:0;border-radius:16px;padding:1px;background:linear-gradient(135deg,rgba(230,57,70,0.3),transparent 50%,rgba(230,57,70,0.1));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;z-index:2}
  video{width:100%;display:block;max-height:70vh;background:#000}
  .info-bar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:20px 0 0;animation:fadeUp 0.7s ease 0.2s both;flex-wrap:wrap}
  .file-info{display:flex;flex-direction:column;gap:4px}
  .file-name{font-family:'Bebas Neue',sans-serif;font-size:22px;letter-spacing:1.5px;line-height:1}
  .file-meta{font-size:12px;color:var(--muted)}
  .action-btns{display:flex;gap:10px}
  .btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:10px;font-family:'DM Sans',sans-serif;font-size:13px;font-weight:500;text-decoration:none;cursor:pointer;border:none;transition:all 0.2s ease}
  .btn svg{width:15px;height:15px}
  .btn-primary{background:var(--accent);color:white;box-shadow:0 4px 20px var(--glow)}
  .btn-primary:hover{background:var(--accent2);transform:translateY(-1px)}
  .btn-ghost{background:rgba(255,255,255,0.05);color:var(--text);border:1px solid var(--border)}
  .btn-ghost:hover{background:rgba(255,255,255,0.09);transform:translateY(-1px)}
  .stats-row{display:flex;gap:1px;margin-top:20px;border-radius:12px;overflow:hidden;border:1px solid var(--border);animation:fadeUp 0.7s ease 0.3s both}
  .stat{flex:1;background:var(--surface);padding:14px 16px;display:flex;flex-direction:column;gap:4px}
  .stat:not(:last-child){border-right:1px solid var(--border)}
  .stat-label{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted)}
  .stat-value{font-family:'Bebas Neue',sans-serif;font-size:17px;letter-spacing:1px}
  .player-section{margin-top:20px;border:1px solid var(--border);border-radius:14px;overflow:hidden;animation:fadeUp 0.7s ease 0.4s both}
  .player-header{padding:12px 16px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
  .player-header svg{width:14px;height:14px;fill:none;stroke:var(--muted);stroke-width:2}
  .player-header span{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);font-weight:500}
  .player-btns{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border)}
  .player-btn{display:flex;align-items:center;justify-content:center;gap:10px;padding:16px;background:var(--surface);text-decoration:none;font-size:13px;font-weight:500;font-family:'DM Sans',sans-serif;transition:all 0.2s ease;cursor:pointer;border:none}
  .player-btn:hover{background:rgba(255,255,255,0.04)}
  .player-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .player-icon svg{width:16px;height:16px}
  .btn-vlc{color:#f97316}
  .btn-vlc .player-icon{background:rgba(249,115,22,0.12);border:1px solid rgba(249,115,22,0.2)}
  .btn-vlc .player-icon svg{fill:#f97316}
  .btn-mx{color:#3b82f6}
  .btn-mx .player-icon{background:rgba(59,130,246,0.12);border:1px solid rgba(59,130,246,0.2)}
  .btn-mx .player-icon svg{fill:none;stroke:#3b82f6;stroke-width:2}
  .btn-label{display:flex;flex-direction:column;gap:2px}
  .btn-name{font-size:13px;font-weight:600}
  .btn-sub{font-size:10px;color:var(--muted);font-weight:400}
  .stream-indicator{display:flex;align-items:center;gap:8px;margin-top:20px;padding:12px 16px;background:rgba(230,57,70,0.06);border:1px solid rgba(230,57,70,0.15);border-radius:10px;animation:fadeUp 0.7s ease 0.5s both}
  .pulse-dot{width:8px;height:8px;background:var(--accent);border-radius:50%;animation:pulse 1.5s ease infinite;box-shadow:0 0 6px var(--accent);flex-shrink:0}
  .stream-indicator span{font-size:12px;color:var(--accent2);font-weight:500}
  footer{margin-top:32px;text-align:center;font-size:11px;color:var(--muted);animation:fadeUp 0.7s ease 0.6s both}
  @keyframes fadeDown{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
  @keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
  @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.5;transform:scale(0.8)}}
  @media(max-width:600px){.info-bar{flex-direction:column;align-items:flex-start}.stats-row{flex-wrap:wrap}.stat{min-width:45%}.btn{padding:10px 16px}.player-btns{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo-mark"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></div>
    <span class="logo-text">StreamVault</span>
    <span class="badge">&#9679; Live</span>
  </header>
  <div class="video-wrapper">
    <video controls autoplay playsinline>
      <source src="STREAM_URL_PLACEHOLDER">
      Your browser does not support video playback.
    </video>
  </div>
  <div class="info-bar">
    <div class="file-info">
      <div class="file-name">Now Playing</div>
      <div class="file-meta">Streaming directly from secure server</div>
    </div>
    <div class="action-btns">
      <a href="DOWNLOAD_URL_PLACEHOLDER" class="btn btn-ghost">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
        Download
      </a>
      <button class="btn btn-primary" onclick="document.querySelector('video').requestFullscreen()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg>
        Fullscreen
      </button>
    </div>
  </div>
  <div class="stats-row">
    <div class="stat"><div class="stat-label">Source</div><div class="stat-value">Telegram</div></div>
    <div class="stat"><div class="stat-label">Protocol</div><div class="stat-value">HTTPS</div></div>
    <div class="stat"><div class="stat-label">Mode</div><div class="stat-value">Stream</div></div>
    <div class="stat"><div class="stat-label">Status</div><div class="stat-value">Active</div></div>
  </div>
  <div class="player-section">
    <div class="player-header">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>
      <span>Open in External Player</span>
    </div>
    <div class="player-btns">
      <a href="#" onclick="openVLC();return false;" class="player-btn btn-vlc">
        <div class="player-icon"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg></div>
        <div class="btn-label"><span class="btn-name">VLC Player</span><span class="btn-sub">Open externally</span></div>
      </a>
      <a href="#" onclick="openMX();return false;" class="player-btn btn-mx">
        <div class="player-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg></div>
        <div class="btn-label"><span class="btn-name">MX Player</span><span class="btn-sub">Open externally</span></div>
      </a>
    </div>
  </div>
  <div class="stream-indicator">
    <div class="pulse-dot"></div>
    <span>Secure stream active &#8212; content delivered end-to-end</span>
  </div>
  <footer>Powered by StreamVault Bot &nbsp;&middot;&nbsp; Unauthorized redistribution prohibited</footer>
</div>
<script>
  var streamUrl = 'STREAM_URL_PLACEHOLDER';
  var streamPath = streamUrl.replace('https://', '').replace('http://', '');
  function openVLC() {
    window.location.href = 'intent://' + streamPath + '#Intent;scheme=https;package=org.videolan.vlc;action=android.intent.action.VIEW;type=video/*;end';
  }
  function openMX() {
    window.location.href = 'intent://' + streamPath + '#Intent;scheme=https;package=com.mxtech.videoplayer.ad;action=android.intent.action.VIEW;type=video/*;end';
  }
</script>
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

@routes.get("/watch/{msg_id}/{filename}")
async def watch_page_handler(request):
    """Serve the HTML player page."""
    try:
        msg_id = int(request.match_info["msg_id"])
        base_url = Config.get_stream_base_url()
        filename = request.match_info["filename"]
        h = _make_hash(msg_id)
        stream_url = f"{base_url}/stream/{msg_id}/{filename}?hash={h}"
        download_url = f"{base_url}/dl/{msg_id}/{filename}?hash={h}"
        html = STREAM_HTML.replace("STREAM_URL_PLACEHOLDER", stream_url)
        html = html.replace("DOWNLOAD_URL_PLACEHOLDER", download_url)
        return web.Response(text=html, content_type="text/html")
    except Exception as e:
        logging.error(f"Watch page error: {e}")
        return web.Response(text=f"Error: {e}", status=500)


@routes.get("/stream/{msg_id}/{filename}")
async def stream_handler(request):
    """Stream raw video bytes — called by the HTML <video> tag."""
    try:
        msg_id = int(request.match_info["msg_id"])
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


@routes.get("/dl/{msg_id}/{filename}")
async def download_handler(request):
    """Serve download page on browser visit; raw file on direct/non-html request."""
    try:
        msg_id = int(request.match_info["msg_id"])
        filename = request.match_info["filename"]
        accept = request.headers.get("Accept", "")

        # Browser visit → show premium download page
        if "text/html" in accept and "direct" not in request.query:
            base_url = Config.get_stream_base_url()
            h = _make_hash(msg_id)
            file_url = f"{base_url}/dl/{msg_id}/{filename}?hash={h}&direct=1"
            html = DOWNLOAD_HTML.replace("FILE_URL_PLACEHOLDER", file_url)
            return web.Response(text=html, content_type="text/html")

        # Actual file download
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

def _make_hash(file_id: int) -> str:
    """Generate a short URL-safe hash for integrity check."""
    import hashlib, base64
    raw = hashlib.sha256(
        f"{file_id}{Config.LINK_SECRET_KEY}".encode()
    ).digest()[:6]
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _safe_filename(filename: str) -> str:
    """Make filename URL-safe using + for spaces, strip special chars, max 30 chars."""
    import re, os
    name, ext = os.path.splitext(filename)
    # Remove special chars except dots, hyphens, underscores, alphanumeric
    clean = re.sub(r'[^\w\s\-.]', '', name)
    # Replace spaces with +
    clean = clean.strip().replace(' ', '+')
    # Truncate to 30 chars, strip trailing +
    clean = clean[:30].rstrip('+')
    return clean + ext


def get_stream_link(file_id: int, filename: str = "file") -> str:
    base_url = Config.get_stream_base_url()
    h = _make_hash(file_id)
    fn = _safe_filename(filename)
    return f"{base_url}/watch/{file_id}/{fn}?hash={h}"


def get_download_link(file_id: int, filename: str = "file") -> str:
    base_url = Config.get_stream_base_url()
    h = _make_hash(file_id)
    fn = _safe_filename(filename)
    return f"{base_url}/dl/{file_id}/{fn}?hash={h}"


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
