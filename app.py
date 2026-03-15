# Web server — also serves as keep-alive for free hosting

from flask import Flask, redirect, Response, request
from configs import Config
import requests

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


@app.route('/watch/<file_id>')
def watch(file_id):
    url = f"http://localhost:8081/watch/{file_id}"
    resp = requests.get(url, stream=True, params=request.args)
    return Response(
        resp.iter_content(chunk_size=1024),
        content_type=resp.headers.get('Content-Type', 'text/html'),
        status=resp.status_code
    )


@app.route('/dl/<file_id>')
def download(file_id):
    url = f"http://localhost:8081/dl/{file_id}"
    resp = requests.get(url, stream=True, params=request.args)
    return Response(
        resp.iter_content(chunk_size=1024),
        content_type=resp.headers.get('Content-Type', 'application/octet-stream'),
        status=resp.status_code,
        headers={
            'Content-Disposition': resp.headers.get('Content-Disposition', ''),
            'Content-Length': resp.headers.get('Content-Length', '')
        }
    )


if __name__ == "__main__":
    app.run()
