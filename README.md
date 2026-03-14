<p align="center">
  <img src="https://telegra.ph/file/cadf1a4567c9ec2b7cb5e.jpg" alt="HPSuperFile StoreBot V2" width="200">
</p>

<h1 align="center">HPSuperFile StoreBot V2 ⚡</h1>

<p align="center">
  <b>A Powerful Telegram Permanent File Store Bot with 12+ Premium Features</b>
</p>

<p align="center">
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white"></a>
  <a href="https://docs.pyrogram.org"><img src="https://img.shields.io/badge/Pyrogram-Latest-green.svg?logo=telegram"></a>
  <a href="https://www.mongodb.com"><img src="https://img.shields.io/badge/MongoDB-Database-brightgreen.svg?logo=mongodb"></a>
  <a href="https://github.com/dengerous53/HPSuperFile_StoreBot/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://t.me/Dengerous53"><img src="https://img.shields.io/badge/Maintainer-@Dengerous53-blue.svg?logo=telegram"></a>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#%EF%B8%8F-deployment">Deployment</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-commands">Commands</a> •
  <a href="#-languages">Languages</a> •
  <a href="#-support">Support</a>
</p>

---

## 📌 What is This?

**HPSuperFile StoreBot V2** is a feature-rich Telegram bot that stores files permanently in a private database channel and generates shareable links. When users click the link, they receive the file directly in the bot's PM. If the bot ever gets banned or deleted, all links can be redirected to a new bot instantly — **zero downtime, zero broken links.**

> 🔥 **V2 Upgrade:** This version includes **12 premium features** including auto-delete, token verification, multi-language support, stream links, clone bot, and much more.

---

## ✨ Features

### 📦 Core Features
| # | Feature | Description |
|---|---------|-------------|
| 🗂️ | **File Storage** | Forward/send any file → stored permanently → get shareable link |
| 📢 | **Channel Integration** | Add bot as admin → auto-adds share buttons to channel posts |
| 📣 | **Broadcasting** | Broadcast messages to all bot users with detailed logs |
| 📊 | **User Statistics** | Track total users, banned users, and bot activity |
| 🔨 | **Ban/Unban System** | Ban users with duration and reason, auto-unban after expiry |
| 📁 | **Batch Links** | Save multiple files in a single shareable link |

### 🚀 V2 Premium Features
| # | Feature | Description | Config Variable |
|---|---------|-------------|-----------------|
| 1️⃣ | **Auto-Delete Messages** | Files auto-delete after configurable time to prevent DMCA | `AUTO_DELETE_TIME` |
| 2️⃣ | **Custom Caption** | Set custom captions with variables like `{filename}`, `{filesize}` | `CUSTOM_CAPTION` |
| 3️⃣ | **Custom Start Photo** | Display a banner image with the start message | `START_PIC` |
| 4️⃣ | **Disable Channel Button** | Option to hide share buttons on channel posts | `DISABLE_CHANNEL_BUTTON` |
| 5️⃣ | **Multiple Force Sub** | Require users to join up to 4 channels before using bot | `FORCE_SUB_CHANNEL_2/3/4` |
| 6️⃣ | **URL Shortener** | Monetize file links with shortener integration | `URL_SHORTENER_API` |
| 7️⃣ | **Token/Verify System** | Users must verify via short link before accessing files | `TOKEN_VERIFICATION` |
| 8️⃣ | **Protect Content** | Prevent users from forwarding/saving received files | `PROTECT_CONTENT` |
| 9️⃣ | **Multi-Admin Panel** | Add multiple admins with full bot management access | `ADMINS` |
| 🔟 | **Stream/Download Links** | Generate direct HTTP stream & download links for media | `STREAM_ENABLED` |
| 1️⃣1️⃣ | **Clone Bot** | Users can create their own clone of the bot | `CLONE_ENABLED` |
| 1️⃣2️⃣ | **Multi-Language (i18n)** | Support for 8 languages with per-user preference | `DEFAULT_LANGUAGE` |

---

## 🌐 Languages

Users can switch their preferred language using `/language` command or the 🌐 button.

| Code | Language | Flag |
|------|----------|------|
| `en` | English | 🇬🇧 |
| `hi` | Hindi | 🇮🇳 |
| `es` | Spanish | 🇪🇸 |
| `fr` | French | 🇫🇷 |
| `ar` | Arabic | 🇸🇦 |
| `pt` | Portuguese | 🇧🇷 |
| `id` | Indonesian | 🇮🇩 |
| `tr` | Turkish | 🇹🇷 |

---

## ⚙️ Configuration

### 🔴 Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org) | `12345678` |
| `API_HASH` | Telegram API Hash from [my.telegram.org](https://my.telegram.org) | `abcdef1234567890` |
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) | `123456:ABC-DEF` |
| `BOT_USERNAME` | Bot username **without @** | `MyFileStoreBot` |
| `DB_CHANNEL` | Private channel ID for file storage (bot must be admin) | `-1001234567890` |
| `BOT_OWNER` | Your Telegram user ID | `123456789` |
| `DATABASE_URL` | MongoDB connection URI | `mongodb+srv://user:pass@cluster.mongodb.net` |
| `LOG_CHANNEL` | Channel ID for bot logs | `-1001234567890` |

### 🟡 Optional Variables — Features

<details>
<summary><b>🕐 Feature 1: Auto-Delete</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTO_DELETE_TIME` | Time in seconds before files are auto-deleted. Set `0` to disable. | `600` (10 min) |
| `AUTO_DELETE_MSG` | Custom warning message. Use `{time}` variable. | Built-in message |
| `AUTO_DELETE_FINAL_MSG` | Message shown after file is deleted. | Built-in message |

**How it works:** When a user receives a file, a countdown warning appears. After the configured time, the file is deleted and the warning is updated.

</details>

<details>
<summary><b>📝 Feature 2: Custom Caption</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `CUSTOM_CAPTION` | Caption template for forwarded files. Leave empty to keep original. | `None` |

**Available Variables:**
| Variable | Description |
|----------|-------------|
| `{filename}` | Name of the file |
| `{filesize}` | Human-readable file size (e.g., `1.25 GB`) |
| `{caption}` | Original caption of the file |
| `{mention}` | User mention link |
| `{username}` | User's username |

**Example:**
