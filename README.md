# Video Download Bot System

Video Download Bot System is a private-first Telegram downloader focused on WeChat Channels / Weixin Video, Douyin, TikTok, Instagram, X/Twitter, and YouTube, with additional support for Bilibili, Xiaohongshu, and other compatible platforms. Send a platform link to the Bot and receive the downloaded media in Telegram.

This repository is a deployment wrapper and patch set around
[`upekshaip/tg-ytdlp-bot`](https://github.com/upekshaip/tg-ytdlp-bot). It keeps the upstream bot as the engine, then adds private-mode defaults, safer dashboard binding, Douyin handling, WeChat Channels handling, TikTok Telegram compatibility, and deployment scripts. This is a semi-original project built through custom development with Codex assistance: the mature downloader engine is upstream, while the deployment layer, privacy hardening, Chinese-platform resolvers, tests, and documentation are custom work in this repo.

中文说明见 [README.zh-CN.md](README.zh-CN.md).

## Supported Platforms

| Platform | Typical links | Notes |
| --- | --- | --- |
| WeChat Channels / Weixin Video | `weixin.qq.com/sph/...` | Public links are tried first; some links need a Yuanbao cookie fallback. |
| Douyin | `v.douyin.com/...`, `douyin.com/...` | Share text and short links are normalized; optional cookie/API resolver support is available. |
| TikTok | `tiktok.com/...` | Prefers Telegram-compatible H.264 + AAC MP4 when possible. |
| Instagram | posts, reels, images | A valid cookie may be required for restricted media. |
| X / Twitter | `x.com/...`, `twitter.com/...` | Supports posts containing multiple videos. |
| YouTube | `youtube.com/...`, `youtu.be/...` | Uses the bundled PO-token provider and optional cookies. |
| Other compatible sites | Bilibili, Xiaohongshu, and many `yt-dlp` / `gallery-dl` sites | Availability follows the platform and upstream extractor. |

No downloader can guarantee permanent access to every platform. Platform changes, login requirements, regional restrictions, rate limits, expired cookies, and copyright rules can affect results.

## Features

- Telegram bot downloads videos from TikTok, Douyin, WeChat Channels / Weixin Video, YouTube, Instagram, X/Twitter, Bilibili, Xiaohongshu, and many other `yt-dlp` / `gallery-dl` supported sites.
- Complete Chinese / English UI for Bot messages, command menus, common errors, guides, the Web login, operations dashboard, and user administration. First contact follows the Telegram client language, while `/lang` switches it manually.
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

## Custom Enhancements Over Upstream

The upstream `tg-ytdlp-bot` provides the core Telegram bot, `yt-dlp`/`gallery-dl` integration, quality selection, upload flow, and dashboard. This repo keeps that engine and applies a focused private-deployment patch set:

- **Private-by-default access control**: config template is oriented around one-person or small-circle use, with `ADMIN`, `PRIVATE_ALLOWED_USERS`, and group access disabled unless explicitly configured.
- **Safer dashboard exposure**: Docker Compose binds the dashboard to `127.0.0.1:5555` by default, so VPS users can access it through SSH tunnel instead of exposing it to the public internet.
- **Two-level user administration**: frequent approval and blocking actions stay in Telegram, while the Web dashboard adds search, status filters, history, and a fuller management view.
- **Complete bilingual UI**: Bot messages, menus, download status, common errors, Cookie guides, Web login, operations dashboard, and user administration support Chinese and English; the Web UI remembers the most recent choice.
- **Douyin resolver chain**: Douyin share text and short links are normalized; the resolver tries mobile page metadata first, then optional `Evil0ctal/Douyin_TikTok_Download_API`, then optional remote resolver or captured resolver output.
- **WeChat Channels support**: adds a resolver for `weixin.qq.com/sph/...` links, including a Yuanbao cookie fallback when the public page only exposes preview metadata.
- **Telegram admin cookie update**: `/set_yuanbao_cookie` lets an admin update Yuanbao cookies directly in Telegram by replying with a cookie file or raw Cookie header.
- **TikTok Telegram-safe format preference**: prefers H.264 + AAC MP4 formats to avoid videos that upload successfully but play silently or poorly inside Telegram.
- **X/Twitter multi-video posts**: when a single X/Twitter status contains multiple video entries, the patch probes all entries and downloads them as a multi-item post instead of only taking the first video.
- **Public-safe packaging**: `scripts/package-for-vps.sh` excludes generated runtime config, cookies, Telegram session files, logs, downloads, and private archives by default; `--include-private` is explicit for personal migration only.
- **VPS watchdog loop**: `scripts/vps-watchdog.sh` checks Docker, the app container, NTP time sync, and Pyrogram session startup, then restarts only the bot service when it detects time-drift or crash symptoms.
- **Patch-driven upstream workflow**: local changes are encoded in `scripts/apply-private-hardening.py` and `scripts/templates/`, so the upstream bot can be re-cloned and patched reproducibly.
- **Focused tests**: resolver tests cover custom Douyin mobile and WeChat Channels behavior.

## Chinese / English Interface

- On first private contact, the Bot uses the language reported by the Telegram client. Chinese clients receive Chinese; other languages default to English.
- Send `/lang` for language buttons, or use `/lang zh` and `/lang en`. The preference is stored per numeric Telegram ID and survives restarts.
- Global and administrator Telegram command menus are registered separately in Chinese and English.
- The Web login, operations dashboard, and `/admin/users` page each provide a `中文 / EN` switch and share the saved browser preference.
- A third-party downloader may still return English technical fields from a website or `yt-dlp`; the Bot wraps common failures in the selected UI language while detailed diagnostics remain in server logs.

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

## Requirements

- Docker Engine or Docker Desktop
- Docker Compose v2
- Git
- Python 3 for patch and test scripts
- A Linux VPS with sufficient disk space for 24/7 deployment

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
- `DASHBOARD_PUBLIC_URL` (optional; only HTTPS URLs enable the Web admin button in Telegram)

Then run:

```bash
scripts/init-local.sh
scripts/local-up.sh
```

Do not run the same Bot account locally and on the VPS at the same time. Two active Telegram sessions can cause duplicate handlers or session conflicts.

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

Upload (example with SSH port `2222`):

```bash
scp -P 2222 video-download-bot-vps.tar.gz root@YOUR_VPS:/opt/
ssh -p 2222 root@YOUR_VPS
mkdir -p /opt/video-download-bot
tar -xzf /opt/video-download-bot-vps.tar.gz -C /opt/video-download-bot --strip-components=1
cd /opt/video-download-bot
scripts/init-local.sh
scripts/local-up.sh
```

Open dashboard over SSH tunnel:

```bash
ssh -p 2222 -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

Then browse `http://localhost:5555`.

The reference VPS deployment in this repository publishes the dashboard at
`https://v.oaclub.com:8443`. Host port 443 is already used by the VPS proxy, so
the dashboard uses Caddy on 8443. Recreate this setup with:

```bash
cd /opt/video-download-bot
scripts/configure-vps-dashboard.sh
```

The script backs up the current Compose file, Caddyfile, and private dashboard
configuration before applying the change.

### VPS Watchdog Loop

For 24/7 VPS use, install the system-level watchdog loop. It checks Docker, the app container, NTP time sync, and whether the Telegram Pyrogram session actually started. If the bot hits Telegram time-drift errors or a recent Python/Telegram crash, it restarts only the `app` service.

```bash
sudo install -m 0755 scripts/vps-watchdog.sh /usr/local/bin/video-download-watchdog

sudo tee /etc/systemd/system/video-download-watchdog.service >/dev/null <<'EOF'
[Unit]
Description=Video Download Bot System watchdog
Wants=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
Environment=APP_DIR=/opt/video-download-bot/vendor/tg-ytdlp-bot
Environment=APP_SERVICE=app
Environment=LOG_FILE=/var/log/video-download-watchdog.log
ExecStart=/usr/local/bin/video-download-watchdog
EOF

sudo tee /etc/systemd/system/video-download-watchdog.timer >/dev/null <<'EOF'
[Unit]
Description=Run Video Download Bot System watchdog every minute

[Timer]
OnBootSec=2min
OnUnitActiveSec=1min
AccuracySec=10s
Persistent=true
Unit=video-download-watchdog.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now video-download-watchdog.timer
```

Check it:

```bash
systemctl list-timers --all video-download-watchdog.timer
systemctl status video-download-watchdog.service --no-pager -l
tail -f /var/log/video-download-watchdog.log
```

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

For WeChat Channels Yuanbao fallback, set the runtime environment value after `scripts/init-local.sh` has created `vendor/tg-ytdlp-bot/.env`:

```env
WECHAT_CHANNELS_YUANBAO_COOKIE=
WECHAT_CHANNELS_TIMEOUT=30
```

You can update this at runtime by sending `/set_yuanbao_cookie` to the bot as an admin and replying with a cookie file or Cookie header.

### Douyin Cookie Update

Douyin can often work without a personal cookie, but keeping a fresh cookie improves success rate when Douyin changes anti-bot checks.

Supported input formats:

- Netscape `cookies.txt` exported from the browser;
- raw request header, for example `Cookie: name=value; name2=value2`.

Update steps:

1. Log in to <https://www.douyin.com/> in your browser.
2. Export Douyin cookies as Netscape cookies.txt, or copy a request `Cookie` header for `douyin.com`.
3. Save it as:

   ```text
   deploy/cookies/douyin.txt
   ```

4. Re-run initialization so the cookie is synchronized into the optional Douyin sidecar:

   ```bash
   scripts/init-local.sh
   scripts/local-up.sh
   ```

On a VPS, run the same commands inside the deployed project directory, for example `/opt/video-download-bot`.

Notes:

- `deploy/cookies/douyin.txt` is ignored by Git.
- Public-safe packages created by `scripts/package-for-vps.sh` exclude it.
- Private migration packages created with `--include-private` can include it, so keep those archives private.

### WeChat Channels Yuanbao Cookie

Some WeChat Channels links only expose preview metadata from the public `weixin.qq.com/sph/...` page. For those links, this project can optionally use a logged-in Tencent Yuanbao web cookie as a fallback.

Yuanbao entry:

- Current web app and login page: <https://yuanbao.tencent.com/>
- The former `/chat/` URL now redirects to the web app root.

Recommended workflow:

1. Open <https://yuanbao.tencent.com/> in your browser and log in.
2. Open browser developer tools, refresh the page, then find an authenticated request to `yuanbao.tencent.com`.
3. Copy the request `Cookie` header, or export it as a cookie file.
4. As an admin, open `/settings` -> Cookies -> `Update WeChat Channels Yuanbao Cookie`, or select `/set_yuanbao_cookie` from the Telegram command menu.
5. Paste the Cookie on the command line. For a long Cookie or a cookie file, send it first and then reply to that message with `/set_yuanbao_cookie`.
6. Send `/set_yuanbao_cookie` without an argument whenever you need the complete capture and update guide in the currently selected Bot language.

The Yuanbao menu entries are registered only for administrator chats. Other users cannot see the scoped command or use the update handler.

Treat all cookies as passwords. They can expire when the platform logs out the account, changes security checks, or invalidates the session. Never commit them, paste them into GitHub, or include them in public packages.

If the Yuanbao request returns HTTP `401`, the saved cookie has expired or been rejected. Log in again and repeat the steps above. Yuanbao occasionally changes its internal API paths, so capture a cookie from the current web app instead of relying on an old endpoint-specific tutorial.

Manual VPS update:

1. Open `vendor/tg-ytdlp-bot/.env`.
2. Set `WECHAT_CHANNELS_YUANBAO_COOKIE` to the copied Cookie header.
3. Restart the bot:

   ```bash
   scripts/local-up.sh
   ```

Treat this cookie like a password. Do not commit it, paste it into GitHub issues, or include it in public VPS packages.

## Configuration Notes

The safe default is private mode:

```python
PRIVATE_MODE = True
ADMIN = [123456789]
PRIVATE_ALLOWED_USERS = []
ALLOWED_GROUP = []
```

Only admins and explicitly allowed users can use the bot in private chat. Group access is disabled unless group IDs are added to `ALLOWED_GROUP`.

### Private User Management

Administrators can maintain the runtime allowlist directly in Telegram without restarting the bot:

- `/users` opens the administrator user-management menu.
- `/add_user 123456789` grants access immediately. An administrator can also reply to a user's original or forwarded message with `/add_user` when Telegram exposes the sender ID.
- `/remove_user 123456789` removes a dynamically granted user.
- `/list_users` shows administrators, configuration-file users, and dynamically granted users.
- `/blacklist_user 123456789` permanently blocks a user, revokes existing access, and removes pending requests.
- `/unblacklist_user 123456789` removes the permanent block; the user must apply again or be added manually.
- `/log 123456789` shows that user's download history to an administrator.

Telegram management actions are authorized by the numeric IDs in `ADMIN` and do not ask for another password. `/users` handles routine work. When `DASHBOARD_PUBLIC_URL` is configured, the menu also contains an `Open Web administration` button.

The Web user-management page is available at `/admin/users` and includes:

- counts for pending, dynamic, configuration-managed, administrator, and permanently blacklisted accounts;
- status filters and search by name, Telegram username, or numeric ID;
- add, approve, reject, revoke, permanently blacklist, and unblacklist actions;
- the latest 100 download-history entries for a selected user;
- full removal/blacklist protection for administrators, plus removal protection with blacklist override for `PRIVATE_ALLOWED_USERS`.

The Web dashboard always requires its independent `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`; Telegram administrator status does not automatically log a browser in. To enable the Bot link, first place the dashboard behind an HTTPS reverse proxy and configure:

```python
DASHBOARD_PUBLIC_URL = "https://bot-admin.example.com"
```

HTTP URLs, URLs containing credentials, and temporary URLs with query parameters are rejected. Leave this setting empty when the dashboard is accessed only through an SSH tunnel; the Bot will then hide the Web link.

Users listed in `PRIVATE_ALLOWED_USERS` remain configuration-managed and must be removed from `deploy/config.local.py` followed by a restart. Removing a user revokes access but does not erase historical logs or the user's server-side directory.

Private chats, returned media, temporary downloads, uploaded user cookies, format preferences, and `/usage` records are separated by Telegram user ID. Service-level resolver cookies, the Yuanbao cookie, sidecars, and public metadata caches remain shared by the bot instance. Other users cannot browse each other's files or logs; administrators can inspect a specific user's history with `/log`.

The dynamic allowlist is stored in `vendor/tg-ytdlp-bot/CONFIG/private_users.json`. It is excluded from public-safe packages because Telegram user IDs are private deployment data.

### Access Request and Approval

Share the following link, replacing `YOUR_BOT_USERNAME` with the Bot username:

```text
https://t.me/YOUR_BOT_USERNAME?start=request_access
```

The user opens the Bot and presses Start. Because the account is not yet authorized, the Bot displays an `Apply for access` button. Pressing it creates one pending request and sends every administrator an approval message containing the applicant's name, username, and numeric Telegram ID.

An administrator can press `Approve`, `Reject`, or `Permanently blacklist` in Telegram, or process requests from the Web user-management page. Approval updates the runtime allowlist immediately and notifies the applicant; no restart is required. Only one pending request is allowed per user, so repeated clicks do not generate repeated administrator notifications. A rejected account must wait 24 hours before submitting another request.

Permanent blacklisting overrides both dynamic and configuration-file authorization, immediately revokes existing access, removes pending requests, and hides the application button from that account. Only an administrator can restore eligibility with `/unblacklist_user USER_ID`. Pending requests and permanently blacklisted IDs also appear in `/users`.

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
- Custom work in this repo: deployment wrapper, privacy hardening, custom Douyin/WeChat Channels resolvers, Telegram admin cookie update command, TikTok compatibility format selection, tests, documentation, and VPS/local operational workflow, developed with Codex assistance.

## Legal and Safety Notice

Use this only for content you own, have permission to download, or are legally allowed to archive. Respect platform terms, copyright, creator rights, and local law.

Never commit real bot tokens, Telegram API credentials, cookies, session files, or generated archives.
