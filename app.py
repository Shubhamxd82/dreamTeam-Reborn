# Web server — also serves as keep-alive for free hosting

from flask import Flask, redirect
from configs import Config

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


if __name__ == "__main__":
    app.run()
