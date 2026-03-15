# Web server — also serves as keep-alive for free hosting

from flask import Flask, Response, request
from configs import Config
import requests as req

app = Flask(__name__)


@app.route('/')
def hello_world():
    return {
        "status": "alive",
        "bot": Config.BOT_USERNAME,
        "features": [
            "auto_delete", "custom_caption", "start_pic",
            "disable_channel_button", "multi_force_sub",
            "url_shortener", "token_verify", "protect_content",
            "admin_panel", "stream_download", "clone_bot",
            "multi_language"
        ]
    }


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
