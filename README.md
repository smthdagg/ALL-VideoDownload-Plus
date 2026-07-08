# VideoDownload Telegram Bot

Private-first Telegram video downloader for self-hosting on Docker or a VPS.

This repository is a deployment wrapper and patch set around
[`upekshaip/tg-ytdlp-bot`](https://github.com/upekshaip/tg-ytdlp-bot). It keeps the upstream bot as the engine, then adds private-mode defaults, safer dashboard binding, Douyin handling, WeChat Channels handling, and deployment scripts.

中文说明见 [README.zh-CN.md](README.zh-CN.md).

## Features

- Telegram bot downloads videos from YouTube, TikTok, Instagram, X/Twitter, Bilibili, Xiaohongshu, and many other `yt-dlp` / `gallery-dl` supported sites.
- Private-use access control: admins and explicitly allowed Telegram user IDs only.
- Local Docker workflow for testing before VPS deployment.
- VPS-friendly Docker Compose stack.
- Dashboard bound to `127.0.0.1` by default; use SSH tunneling instead of exposing it publicly.
- Douyin support:
  - normalizes shared text and short links;
  - uses mobile page metadata when possible;
  - can use the optional `Evil0ctal/Douyin_TikTok_Download_API` sidecar;
  - supports an optional remote resolver endpoint.
- WeChat Channels support:
  - handles public `weixin.qq.com/sph/...` links;
  - optional Yuanbao cookie fallback for links that only expose preview metadata.
- TikTok Telegram compatibility mode: prefers H.264 + AAC MP4 to avoid silent or incompatible uploads.
- Admin command for updating Yuanbao cookie from Telegram: `/set_yuanbao_cookie`.

## What This Repo Contains

This repo does not vendor the full upstream bot into Git. `scripts/init-local.sh` clones or updates it under `vendor/tg-ytdlp-bot`, then applies local patches.

Tracked files include:

- `scripts/` - bootstrap, patch, Docker, packaging, and helper scripts.
- `scripts/templates/` - custom parser modules injected into the upstream bot.
- `deploy/config.local.py.example` - safe config template.
- `.env.example` - safe environment template.
- `tests/` - focused unit tests for the custom resolvers.
- `docs/` - architecture, deployment, security, and attribution notes.

Ignored private/runtime files include:

- `deploy/config.local.py`
- `deploy/cookies/*.txt`
- `vendor/tg-ytdlp-bot/.env`
- `vendor/tg-ytdlp-bot/magic.session`
- generated package archives and runtime downloads/logs.

## Quick Start: Local Docker

Requirements:

- Docker
- Docker Compose v2
- Python 3 for patch scripts
- Git

Setup:

```bash
git clone https://github.com/smthdagg/VideoDownload.git
cd VideoDownload
cp .env.example .env
scripts/init-local.sh
```

The first run creates `deploy/config.local.py`. Fill in:

- `BOT_NAME`
- `BOT_NAME_FOR_USERS`
- `ADMIN`
- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `LOGS_ID`
- `DASHBOARD_PASSWORD`

Then run:

```bash
scripts/init-local.sh
scripts/local-up.sh
```

Dashboard:

```text
http://localhost:5555
```

Stop local service:

```bash
scripts/local-down.sh
```

Follow logs:

```bash
scripts/logs.sh
```

## VPS Deployment

On the VPS, install Docker and Docker Compose. Then either clone this repository directly on the VPS or build a transfer archive.

### Option A: Clone on VPS

```bash
git clone https://github.com/smthdagg/VideoDownload.git /opt/video-download-bot
cd /opt/video-download-bot
cp .env.example .env
cp deploy/config.local.py.example deploy/config.local.py
```

Fill `deploy/config.local.py`, then:

```bash
scripts/init-local.sh
scripts/local-up.sh
```

### Option B: Package Locally, Upload to VPS

Public-safe archive, without secrets:

```bash
scripts/package-for-vps.sh
```

Personal migration archive, including local config/cookies/session:

```bash
scripts/package-for-vps.sh --include-private
```

Keep `--include-private` archives private. They may contain Telegram credentials, cookies, and session files.

Upload:

```bash
scp video-download-bot-vps.tar.gz root@YOUR_VPS:/opt/
ssh root@YOUR_VPS
mkdir -p /opt/video-download-bot
tar -xzf /opt/video-download-bot-vps.tar.gz -C /opt/video-download-bot --strip-components=1
cd /opt/video-download-bot
scripts/init-local.sh
scripts/local-up.sh
```

Open dashboard over SSH tunnel:

```bash
ssh -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

Then browse `http://localhost:5555`.

## Cookies

Optional cookie files go in:

```text
deploy/cookies/youtube.txt
deploy/cookies/instagram.txt
deploy/cookies/tiktok.txt
deploy/cookies/twitter.txt
deploy/cookies/facebook.txt
deploy/cookies/vk.txt
deploy/cookies/douyin.txt
```

Use Netscape cookies.txt format unless a resolver explicitly documents a raw Cookie header.

For WeChat Channels Yuanbao fallback, set:

```env
WECHAT_CHANNELS_YUANBAO_COOKIE=
WECHAT_CHANNELS_TIMEOUT=30
```

You can update this at runtime by sending `/set_yuanbao_cookie` to the bot as an admin and replying with a cookie file or Cookie header.

## Configuration Notes

The safe default is private mode:

```python
PRIVATE_MODE = True
ADMIN = [123456789]
PRIVATE_ALLOWED_USERS = []
ALLOWED_GROUP = []
```

Only admins and explicitly allowed users can use the bot in private chat. Group access is disabled unless group IDs are added to `ALLOWED_GROUP`.

## Validation

Run local tests:

```bash
python3 -m unittest discover -s tests
python3 -m py_compile scripts/apply-private-hardening.py
```

Check that no private files would be committed:

```bash
git status --ignored -s
```

## Attribution

See [docs/CREDITS.md](docs/CREDITS.md).

Short version:

- Core Telegram downloader: `upekshaip/tg-ytdlp-bot`.
- Download engines: `yt-dlp`, `gallery-dl`, `ffmpeg`.
- Optional Douyin/TikTok sidecar: `Evil0ctal/Douyin_TikTok_Download_API`.
- Custom work in this repo: deployment wrapper, privacy hardening, custom Douyin/WeChat resolvers, Telegram admin cookie update command, TikTok compatibility format selection, tests, and documentation.

## Legal and Safety Notice

Use this only for content you own, have permission to download, or are legally allowed to archive. Respect platform terms, copyright, creator rights, and local law.

Never commit real bot tokens, Telegram API credentials, cookies, session files, or generated archives.
