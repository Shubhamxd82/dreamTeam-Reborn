# Web server — also serves as keep-alive for free hosting

from flask import Flask, Response, request, jsonify
from configs import Config
import requests as req

app = Flask(__name__)

LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{bot} — File Store Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#080a0f; --surface:#0e1118; --border:rgba(255,255,255,0.06);
    --accent:#e63946; --accent2:#ff6b6b; --text:#f0f0f0;
    --muted:#6b7280; --glow:rgba(230,57,70,0.3);
  }}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px 16px;overflow-x:hidden}}
  body::before{{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 50% -10%,rgba(230,57,70,0.12) 0%,transparent 60%),radial-gradient(ellipse 40% 30% at 80% 80%,rgba(230,57,70,0.06) 0%,transparent 50%);pointer-events:none;z-index:0}}
  .container{{position:relative;z-index:1;width:100%;max-width:520px;text-align:center}}
  .logo-wrap{{display:flex;align-items:center;justify-content:center;gap:14px;margin-bottom:32px;animation:fadeDown 0.6s ease both}}
  .logo-mark{{width:52px;height:52px;background:var(--accent);border-radius:14px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 30px var(--glow)}}
  .logo-mark svg{{width:26px;height:26px;fill:white}}
  .logo-text{{font-family:'Bebas Neue',sans-serif;font-size:32px;letter-spacing:3px}}
  .status-badge{{display:inline-flex;align-items:center;gap:6px;background:rgba(34,197,94,0.08);border:1px solid rgba(34,197,94,0.2);color:#4ade80;font-size:12px;font-weight:600;padding:6px 14px;border-radius:20px;letter-spacing:1px;text-transform:uppercase;margin-bottom:28px;animation:fadeDown 0.6s ease 0.1s both}}
  .pulse{{width:7px;height:7px;background:#4ade80;border-radius:50%;animation:pulse 1.5s ease infinite}}
  .headline{{font-family:'Bebas Neue',sans-serif;font-size:48px;letter-spacing:2px;line-height:1;margin-bottom:14px;animation:fadeUp 0.7s ease 0.2s both}}
  .headline span{{color:var(--accent2)}}
  .subtext{{font-size:15px;color:var(--muted);line-height:1.6;margin-bottom:36px;animation:fadeUp 0.7s ease 0.3s both}}
  .cta{{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:white;text-decoration:none;padding:14px 28px;border-radius:12px;font-size:15px;font-weight:600;letter-spacing:0.3px;box-shadow:0 8px 30px var(--glow);transition:all 0.2s ease;animation:fadeUp 0.7s ease 0.35s both;margin-bottom:40px}}
  .cta:hover{{background:var(--accent2);transform:translateY(-2px);box-shadow:0 12px 40px var(--glow)}}
  .cta svg{{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2}}
  .features{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:36px;animation:fadeUp 0.7s ease 0.4s both}}
  .feature{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:10px;text-align:left}}
  .feature-icon{{width:34px;height:34px;background:rgba(230,57,70,0.1);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
  .feature-icon svg{{width:16px;height:16px;fill:none;stroke:var(--accent2);stroke-width:2}}
  .feature-text{{font-size:12px;font-weight:500}}
  .feature-sub{{font-size:10px;color:var(--muted);margin-top:2px}}
  .footer{{font-size:11px;color:var(--muted);animation:fadeUp 0.7s ease 0.5s both}}
  .footer a{{color:var(--accent2);text-decoration:none}}
  @keyframes fadeDown{{from{{opacity:0;transform:translateY(-16px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.5;transform:scale(0.8)}}}}
  @media(max-width:480px){{.headline{{font-size:36px}}.features{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="container">
  <div class="logo-wrap">
    <div class="logo-mark"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></div>
    <span class="logo-text">FileStore</span>
  </div>
  <div class="status-badge"><div class="pulse"></div>Online &amp; Running</div>
  <div class="headline">Permanent <span>File</span> Storage</div>
  <div class="subtext">Store any file and get a permanent shareable link instantly.<br>Stream videos, download files — all from Telegram.</div>
  <a href="https://t.me/{bot}" class="cta">
    <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
    Open @{bot}
  </a>
  <div class="features">
    <div class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg></div><div><div class="feature-text">Permanent Links</div><div class="feature-sub">Links never expire</div></div></div>
    <div class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg></div><div><div class="feature-text">Stream Videos</div><div class="feature-sub">Watch without download</div></div></div>
    <div class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div><div><div class="feature-text">Multi-Language</div><div class="feature-sub">12+ languages</div></div></div>
    <div class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg></div><div><div class="feature-text">Clone Bots</div><div class="feature-sub">Create your own bot</div></div></div>
    <div class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><div><div class="feature-text">Protected Content</div><div class="feature-sub">Anti-forward mode</div></div></div>
    <div class="feature"><div class="feature-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 010 14.14M4.93 4.93a10 10 0 000 14.14"/></svg></div><div><div class="feature-text">Auto Delete</div><div class="feature-sub">Copyright protection</div></div></div>
  </div>
  <div class="footer">Powered by <a href="https://t.me/{bot}">@{bot}</a> &nbsp;·&nbsp; Built with Pyrogram</div>
</div>
</body>
</html>"""


@app.route('/')
def hello_world():
    html = LANDING_PAGE.format(bot=Config.BOT_USERNAME)
    return Response(html, content_type='text/html')


@app.route('/serve_bot')
def serve_bot_info():
    """
    Called by Cloudflare Worker to get current FileServeBot username.
    Worker uses this to build redirect URLs dynamically.
    """
    username = Config.SERVE_BOT_USERNAME or Config.BOT_USERNAME
    return jsonify({"username": username})


def _proxy(path, **kwargs):
    """Forward a request to the internal aiohttp stream server on port 8081."""
    url = f"http://localhost:8081{path}"
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    resp = req.get(url, stream=True, headers=headers,
                   params=request.args, **kwargs)
    excluded = {'transfer-encoding', 'content-encoding', 'connection'}
    out_headers = {k: v for k, v in resp.headers.items()
                   if k.lower() not in excluded}
    return Response(
        resp.iter_content(chunk_size=65536),
        status=resp.status_code,
        headers=out_headers
    )


@app.route('/watch/<file_id>')
def watch(file_id):
    return _proxy(f"/watch/{file_id}")


@app.route('/stream/<file_id>')
def stream(file_id):
    return _proxy(f"/stream/{file_id}")


@app.route('/dl/<file_id>')
def download(file_id):
    return _proxy(f"/dl/{file_id}")


if __name__ == "__main__":
    app.run()
