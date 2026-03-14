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
</details>

<details>
<summary><b>🖼️ Feature 3: Custom Start Photo</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `START_PIC` | Direct URL to an image displayed with the start message. | Empty (no photo) |

**Example:**
</details>

<details>
<summary><b>🔇 Feature 4: Disable Channel Button</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `DISABLE_CHANNEL_BUTTON` | If `True`, files posted in channels won't get a share button added. | `False` |

</details>

<details>
<summary><b>📢 Feature 5: Multiple Force Subscribe</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `UPDATES_CHANNEL` | Force Sub Channel 1 ID | Empty |
| `FORCE_SUB_CHANNEL_2` | Force Sub Channel 2 ID | Empty |
| `FORCE_SUB_CHANNEL_3` | Force Sub Channel 3 ID | Empty |
| `FORCE_SUB_CHANNEL_4` | Force Sub Channel 4 ID | Empty |

**How it works:** Users must join ALL configured channels before they can use the bot. A join button is shown for each unjoin channel.

> ⚠️ Bot must be admin in all force sub channels.

</details>

<details>
<summary><b>🔗 Feature 6: URL Shortener</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `URL_SHORTENER` | Enable URL shortening (`True`/`False`) | `False` |
| `URL_SHORTENER_API` | API key from your shortener service | Empty |
| `URL_SHORTENER_WEBSITE` | Shortener domain | Empty |

**Supported Shorteners:**
- `gplinks.co`
- `shrinkme.io`
- `shorturllink.in`
- `droplink.co`
- Any service with similar API pattern

**Example:**
</details>

<details>
<summary><b>🔐 Feature 7: Token/Verify System</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `TOKEN_VERIFICATION` | Enable token verification (`True`/`False`) | `False` |
| `TOKEN_TIMEOUT` | Token validity duration in seconds | `7200` (2 hours) |
| `TOKEN_SHORTENER_API` | API key for token shortener (can differ from main shortener) | Empty |
| `TOKEN_SHORTENER_WEBSITE` | Shortener domain for tokens | Empty |

**How it works:**
1. User clicks a file link
2. Bot asks user to verify via a shortened link
3. User clicks the short link → completes verification
4. Token is valid for `TOKEN_TIMEOUT` seconds
5. During valid period, user can access files without re-verifying

> 💰 This feature is commonly used for **monetization** via URL shorteners.

</details>

<details>
<summary><b>🔒 Feature 8: Protect Content</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `PROTECT_CONTENT` | If `True`, users cannot forward/save files sent by the bot. | `False` |

> ⚠️ This uses Telegram's native content protection. Users still can't screenshot on mobile.

</details>

<details>
<summary><b>👮 Feature 9: Multi-Admin Panel</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMINS` | Space-separated list of admin user IDs | Empty |

**Admin Capabilities:**
- `/broadcast` — Send messages to all users
- `/status` — View user statistics
- `/ban_user` — Ban users
- `/unban_user` — Unban users
- `/banned_users` — View banned users list
- `/admins` — View admin list

**Owner-Only:**
- `/addadmin user_id` — Add new admin
- `/removeadmin user_id` — Remove admin
- `/settings` — View all bot settings

**Example:**
</details>

<details>
<summary><b>🔐 Feature 7: Token/Verify System</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `TOKEN_VERIFICATION` | Enable token verification (`True`/`False`) | `False` |
| `TOKEN_TIMEOUT` | Token validity duration in seconds | `7200` (2 hours) |
| `TOKEN_SHORTENER_API` | API key for token shortener (can differ from main shortener) | Empty |
| `TOKEN_SHORTENER_WEBSITE` | Shortener domain for tokens | Empty |

**How it works:**
1. User clicks a file link
2. Bot asks user to verify via a shortened link
3. User clicks the short link → completes verification
4. Token is valid for `TOKEN_TIMEOUT` seconds
5. During valid period, user can access files without re-verifying

> 💰 This feature is commonly used for **monetization** via URL shorteners.

</details>

<details>
<summary><b>🔒 Feature 8: Protect Content</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `PROTECT_CONTENT` | If `True`, users cannot forward/save files sent by the bot. | `False` |

> ⚠️ This uses Telegram's native content protection. Users still can't screenshot on mobile.

</details>

<details>
<summary><b>👮 Feature 9: Multi-Admin Panel</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMINS` | Space-separated list of admin user IDs | Empty |

**Admin Capabilities:**
- `/broadcast` — Send messages to all users
- `/status` — View user statistics
- `/ban_user` — Ban users
- `/unban_user` — Unban users
- `/banned_users` — View banned users list
- `/admins` — View admin list

**Owner-Only:**
- `/addadmin user_id` — Add new admin
- `/removeadmin user_id` — Remove admin
- `/settings` — View all bot settings

**Example:**
Admins can also be added dynamically via `/addadmin` command.

</details>

<details>
<summary><b>▶️ Feature 10: Stream/Download Links</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_ENABLED` | Enable stream server (`True`/`False`) | `False` |
| `STREAM_PORT` | Port for the stream server | `8080` |
| `STREAM_FQDN` | Your public domain | Empty |
| `STREAM_USE_HTTPS` | Use HTTPS for stream links | `True` |

**How it works:**
- Bot starts an `aiohttp` web server alongside the Telegram bot
- For each file, two links are generated:
  - **▶️ Stream** — Opens file in browser (great for videos)
  - **📥 Download** — Force-downloads the file

**Example:**
**Generated Links:**
> ⚠️ Requires a hosting platform that supports port binding (VPS, Koyeb, Railway, etc.)

</details>

<details>
<summary><b>🤖 Feature 11: Clone Bot</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `CLONE_ENABLED` | Enable clone feature (`True`/`False`) | `False` |

**How it works:**
1. User creates a bot via [@BotFather](https://t.me/BotFather)
2. User creates a private channel and adds the new bot as admin
3. User runs: `/clone BOT_TOKEN DB_CHANNEL_ID`
4. A clone of your bot starts running!
5. Clone bots automatically restart when main bot restarts

**Commands:**
- `/clone BOT_TOKEN -100CHANNEL_ID` — Create clone
- `/removeclone` — Remove your clone

> ⚠️ Clone bots use the same `API_ID` and `API_HASH` as the main bot.

</details>

<details>
<summary><b>🌐 Feature 12: Multi-Language</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_LANGUAGE` | Default language for new users | `en` |

**How it works:**
- New users get the default language
- Users can change language via `/language` command or 🌐 button
- Language preference is saved per-user in the database
- All bot messages, buttons, and prompts are translated

</details>

<details>
<summary><b>☁️ Cloudflare Worker URL</b></summary>

| Variable | Description | Default |
|----------|-------------|---------|
| `WORKER_URL` | Cloudflare Worker URL for share links | `https://files.Moviesss4ers.workers.dev` |

**Why use a Worker URL?**
- 🔄 **Bot Migration:** If your bot gets banned, update the worker to redirect to new bot — all old links work!
- 🛡️ **Anti-DMCA:** Adds a protection layer
- 📊 **Analytics:** Track link clicks

**Worker Setup:**
1. Go to [Cloudflare Workers](https://workers.cloudflare.com)
2. Create a new worker with this code:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const path = url.pathname.substring(1) // Remove leading /
  
  if (path) {
    // Redirect to your bot
    const botUsername = 'YOUR_BOT_USERNAME' // Change this
    return Response.redirect(`https://t.me/${botUsername}?start=${path}`, 302)
  }
  
  return new Response('File Store Bot', { status: 200 })
}
