# ALL VideoDownload Plus

[![GitHub release](https://img.shields.io/github/v/release/smthdagg/ALL-VideoDownload-Plus?display_name=tag)](https://github.com/smthdagg/ALL-VideoDownload-Plus/releases)
[![License](https://img.shields.io/github/license/smthdagg/ALL-VideoDownload-Plus)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](docs/DEPLOYMENT.md)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](docs/DEPLOYMENT.md)

![User access flow](docs/images/user-access-flow.svg)

> 中文首页先介绍核心使用流程；英文说明、部署手册、架构图和安全边界见下文及 `docs/`。

## 中文说明

ALL VideoDownload Plus 是一个独立发布的 Telegram 多平台下载项目，不是上游项目的公开模板。它面向私人 VPS 部署，中文优先支持视某号、某音、TT、Instagram、X、YouTube，并兼容 8站、小某书及其他 `yt-dlp` / `gallery-dl` 平台。上游项目只作为下载引擎，本项目独立维护权限、解析增强、Cookie 工具、部署、安全和文档。

直接把原始平台链接发送给 Bot，即可解析并下载视频、图片、图集、音频或 X 多视频帖子。Bot 支持中英文 Help 与菜单、`/lang` 语言切换、画质预设、Cookie 管理、用户申请审批、永久拉黑、Web 管理后台、自动清理和 VPS watchdog 自愈。

![System architecture](docs/images/system-architecture.svg)

![Storage policy](docs/images/storage-policy.svg)

### Bot UI preview

The bilingual Help screen keeps the common workflow, Cookie import, playlist,
quality, cleanup, and language commands in one readable panel.

![Chinese Bot Help preview](docs/images/bot-help-zh.png)

### Dashboard and settings preview

The screenshots show the bilingual Bot settings menu, the separate Web
dashboard login, and the user-approval management view. Dashboard credentials
are independent from Telegram IDs.

![Bot settings preview](docs/images/bot-settings-zh.png)

![Dashboard login preview](docs/images/dashboard-login-zh.png)

![Dashboard user management preview](docs/images/dashboard-users-zh.png)

### 中文快速开始

```bash
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git
cd ALL-VideoDownload-Plus
cp .env.example .env
scripts/init-local.sh
scripts/local-up.sh
```

首次运行前填写 `deploy/config.local.py` 中的 Telegram `API_ID`、`API_HASH`、Bot Token、管理员数字 ID 和后台登录凭据。Bot 内常用命令：`/help` 查看完整帮助，`/lang` 切换语言，`/settings` 设置画质/Cookie，`/format` 设置格式，`/clean` 清理个人临时文件。

### 中文支持平台清单

| 平台 | 支持内容 | 当前状态 |
| --- | --- | --- |
| 视某号 | 视某号公开视频、预览卡片和媒体 | 重点适配；公开解析失败时支持 Yuanbao Cookie fallback |
| 某音 | 视频、分享文案、短链和无水印媒体 | 重点适配；移动端解析、可选 API sidecar |
| TT | 视频、音频流和兼容 Telegram 的媒体 | 重点适配；有限挑战重试，优先 H.264 + AAC + MP4 |
| Instagram | 帖子、Reels、Stories、图片和图集 | 重点适配；私密或登录可见内容需要 Cookie |
| X / Twitter | 帖子、图片和一个帖子内的多个视频 | 重点适配；多媒体会全部处理 |
| YouTube | 视频、音频、Shorts 和播放列表 | 重点适配；使用 PO Token provider，可选 Cookie |
| 8站 | 视频和音频 | 通用兼容；登录可见或地区限制内容需要 Cookie |
| 小某书 | 笔记中的视频、图片和图集 | 通用兼容；具体能力取决于上游解析器 |
| Facebook、Vimeo、Reddit、Twitch | 视频、Reels、Clip 和帖子媒体 | 通用兼容；私密或受限内容需要对应平台登录态 |
| 某手及其他站点 | 视频、音频、图片和图集 | 实验性/通用兼容；以当前上游 extractor 结果为准 |

完整的支持内容、登录态要求、平台限制和 Cookie 说明见：[中文平台支持矩阵](README.zh-CN.md#支持的平台与链接类型)。平台改版、地区限制、限流和 Cookie 过期都可能造成暂时失败。

### 中文 VPS 与迁移

VPS 部署、Docker、SSH 隧道、后台域名、watchdog、磁盘清理、迁移和回滚请阅读：[中文部署与迁移手册](docs/DEPLOYMENT.zh-CN.md)。从正在运行的 VPS 制作最新私有备份：

```bash
sudo scripts/prepare-vps-migration.sh
```

私有迁移包包含 Token、Cookie、Telegram Session、用户权限和偏好，只能存放在自己的受保护位置，不能上传 GitHub。

---

## English

ALL VideoDownload Plus is a private-first Telegram downloader focused on 视某号, 某音, TT, Instagram, X/Twitter, and YouTube, with additional support for 8站, 小某书, and other compatible platforms. Send a platform link to the Bot and receive the downloaded media in Telegram.

This release includes the complete bilingual Bot Help and command menu, private-user approval and blacklist controls, per-user cookies and preferences, X multi-video handling, 视某号 Yuanbao fallback, TT retry and audio/video compatibility, 某音 resolver integration, an authenticated Web administration panel, automatic cleanup, watchdog recovery, and reproducible VPS migration packages.

New users receive an access-request button with language selection. After approval,
the Bot explains `/settings` -> Cookie and `/cookies_from_browser` for importing
their own cookies.txt. Files, settings, Cookies, and usage records are keyed by
the Telegram numeric ID and are not shared between users.

## Release Scope

- **Bot experience:** English and Chinese Help, localized Telegram command menus, `/lang`, `/settings`, quality presets, cookie tools, and platform-specific guides.
- **Platform work:** TT challenge retries with bounded backoff, Telegram-safe audio/video formats, X multi-video posts, 某音 mobile/API fallbacks, 视某号 public and Yuanbao resolvers, and Instagram gallery handling.
- **Private operations:** approval workflow, rate-limited access requests, permanent blacklist, per-user isolation, authenticated dashboard, log visibility, disk cleanup, watchdog recovery, and migration-safe backups.
- **Maintenance model:** custom behavior is stored in tracked patch scripts and templates; generated upstream code stays reproducible and private runtime state never enters GitHub.

This is an independent project and release with a deployment wrapper and patch set around
[`upekshaip/tg-ytdlp-bot`](https://github.com/upekshaip/tg-ytdlp-bot). It keeps the upstream bot as the engine, then adds private-mode defaults, safer dashboard binding, 某音 handling, 视某号 handling, TT Telegram compatibility, and deployment scripts. This is a semi-original project built through custom development with Codex assistance: the mature downloader engine is upstream, while the deployment layer, privacy hardening, Chinese-platform resolvers, tests, and documentation are custom work in this repo.

中文完整版见 [README.zh-CN.md](README.zh-CN.md).

## Supported Platforms

| Platform | Supported content | Notes |
| --- | --- | --- |
| 视某号 | Public videos, preview cards, and media | Public parsing first; some media needs a Yuanbao Cookie fallback. |
| 某音 | Videos, shared text, short links, and direct media | Mobile/API resolver support is available. |
| TT | Videos, audio streams, and Telegram-compatible media | Prefers H.264 + AAC + MP4 and bounded retries. |
| Instagram | Posts, Reels, Stories, images, and galleries | A valid Cookie may be required for restricted media. |
| X / Twitter | Posts, images, and multiple videos in one post | Multiple media entries are processed. |
| YouTube | Videos, audio, Shorts, and playlists | Uses the bundled PO-token provider and optional Cookies. |
| 8站 | Videos and audio | Availability follows the upstream extractor and access rules. |
| 小某书 | Videos, images, and galleries in notes | Availability follows the upstream extractor. |
| Facebook, Vimeo, Reddit, Twitch | Videos, Reels, Clips, and post media | Private or restricted media may require a platform Cookie. |
| 某手 and other compatible sites | Videos, audio, images, and galleries | Experimental/general compatibility follows upstream support. |

No downloader can guarantee permanent access to every platform. Platform changes, login requirements, regional restrictions, rate limits, expired cookies, and copyright rules can affect results.

## Features

- Telegram bot downloads videos from TT, 某音, 视某号, YouTube, Instagram, X/Twitter, 8站, 小某书, and many other `yt-dlp` / `gallery-dl` supported sites.
- Complete Chinese / English UI for Bot messages, command menus, common errors, guides, the Web login, operations dashboard, and user administration. First contact follows the Telegram client language, while `/lang` switches it manually.
- Private-use access control: admins and explicitly allowed Telegram user IDs only.
- Local Docker workflow for testing before VPS deployment.
- VPS-friendly Docker Compose stack.
- Dashboard bound to `127.0.0.1` by default; use SSH tunneling instead of exposing it publicly.
- 某音 support:
  - normalizes shared text and short links;
  - uses mobile page metadata when possible;
  - can use the optional `Evil0ctal/Douyin_TikTok_Download_API` sidecar;
  - supports an optional remote resolver endpoint.
- 视某号 support:
  - handles public shared video links;
  - optional Yuanbao cookie fallback for links that only expose preview metadata.
- TT Telegram compatibility mode: prefers H.264 + AAC MP4 to avoid silent or incompatible uploads, and automatically retries transient JavaScript challenge responses from TT.
- Admin command for updating Yuanbao cookie from Telegram: `/set_yuanbao_cookie`.

## Custom Enhancements Over Upstream

The upstream `tg-ytdlp-bot` provides the core Telegram bot, `yt-dlp`/`gallery-dl` integration, quality selection, upload flow, and dashboard. This repo keeps that engine and applies a focused private-deployment patch set:

- **Private-by-default access control**: config template is oriented around one-person or small-circle use, with `ADMIN`, `PRIVATE_ALLOWED_USERS`, and group access disabled unless explicitly configured.
- **Safer dashboard exposure**: Docker Compose binds the dashboard to `127.0.0.1:5555` by default, so VPS users can access it through SSH tunnel instead of exposing it to the public internet.
- **Two-level user administration**: frequent approval and blocking actions stay in Telegram, while the Web dashboard adds search, status filters, history, and a fuller management view.
- **Complete bilingual UI**: Bot messages, menus, download status, common errors, Cookie guides, Web login, operations dashboard, and user administration support Chinese and English; the Web UI remembers the most recent choice.
- **某音 resolver chain**: shared text and short links are normalized; the resolver tries mobile page metadata first, then optional `Evil0ctal/Douyin_TikTok_Download_API`, then optional remote resolver or captured resolver output.
- **视某号 support**: adds a resolver for public shared video links, including a Yuanbao Cookie fallback when the public page only exposes preview metadata.
- **Telegram admin cookie update**: `/set_yuanbao_cookie` lets an admin update Yuanbao cookies directly in Telegram by replying with a cookie file or raw Cookie header.
- **TT Telegram-safe format preference**: prefers H.264 + AAC MP4 formats to avoid videos that upload successfully but play silently or poorly inside Telegram.
- **Supported runtime baseline**: Docker uses Python 3.12, stable `yt-dlp 2026.08.19`, and `bgutil-ytdlp-pot-provider 1.3.2`. Global prerelease installation and the unused MoviePy 1.x dependency have been removed.
- **X/Twitter multi-video posts**: when a single X/Twitter status contains multiple video entries, the patch probes all entries and downloads them as a multi-item post instead of only taking the first video.
- **Public-safe packaging**: `scripts/package-for-vps.sh` excludes generated runtime config, cookies, Telegram session files, logs, downloads, and private archives by default; `--include-private` is explicit for personal migration only.
- **VPS watchdog loop**: `scripts/vps-watchdog.sh` checks Docker, the app container, NTP time sync, and Pyrogram session startup, then restarts only the bot service when it detects time-drift or crash symptoms.
- **Automatic storage protection**: `scripts/runtime-cleanup.sh` removes stale media and partial files while preserving user settings, cookies, logs, and caches. It runs every 30 minutes on the VPS, and removes the oldest eligible media first when disk usage exceeds 80%.
- **User-facing storage warnings**: the Bot warns private users at 75% disk usage, at most once every six hours per user, and points them to `/clean`. The cleanup service removes media after the configured retention period and can enforce an optional `MAX_MEDIA_STORAGE_GB` cap.
- **Patch-driven upstream workflow**: local changes are encoded in `scripts/apply-private-hardening.py` and `scripts/templates/`, so the upstream bot can be re-cloned and patched reproducibly.
- **Focused tests**: resolver tests cover custom 某音 mobile and 视某号 behavior.

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
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git
cd ALL-VideoDownload-Plus
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
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git /opt/video-download-bot
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

Low-level private archive, including config, cookies, session, user access, and preferences:

```bash
scripts/package-for-vps.sh --include-private
```

Keep `--include-private` archives private. They may contain Telegram credentials, cookies, and session files.

For a consistent migration from a running VPS, use the wrapper that briefly
stops and automatically restores only the Bot container:

```bash
sudo scripts/prepare-vps-migration.sh
```

The complete transfer, activation, acceptance, and rollback procedure is in
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

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

When host port 443 is already occupied, publish the dashboard through Caddy on
8443 with an explicit deployment hostname:

```bash
cd /opt/video-download-bot
DASHBOARD_DOMAIN=bot-admin.example.com scripts/configure-vps-dashboard.sh
```

The script backs up the current Compose file, Caddyfile, and private dashboard
configuration before applying the change.

### VPS Watchdog Loop

For 24/7 VPS use, install the system-level watchdog loop. It checks Docker, the app container, NTP time sync, and whether the Telegram Pyrogram session actually started. If the bot hits Telegram time-drift errors or a recent Python/Telegram crash, it restarts only the `app` service.

Install both the watchdog and storage cleanup timers with:

```bash
sudo scripts/install-vps-operations.sh
```

### Runtime storage cleanup

The VPS installer also provides a storage cleanup timer. It runs every 30 minutes, removes media and incomplete download files older than two hours, removes old subtitle metadata, and preserves per-user settings, cookies, logs, and format caches. When disk usage exceeds 80%, it removes the oldest eligible media until usage falls below 70%.

```bash
bash scripts/install-runtime-cleanup.sh
systemctl status video-download-runtime-cleanup.timer --no-pager -l
journalctl -u video-download-runtime-cleanup.service -n 50 --no-pager
```

The Web dashboard cleanup action uses the actual application directory instead of a hard-coded legacy path. Docker container logs are capped at 100 MB per file and three rotated files per service.

Host-bound controls are reported honestly: restart, WireGuard IP rotation, engine upgrades, and list refreshes require the VPS host and are not executed from inside the app container. User approval, blacklist, history, configuration editing, cleanup, metrics, and domain-list editing remain available through the authenticated dashboard.

```bash
sudo install -m 0755 scripts/vps-watchdog.sh /usr/local/bin/video-download-watchdog

sudo tee /etc/systemd/system/video-download-watchdog.service >/dev/null <<'EOF'
[Unit]
Description=ALL VideoDownload Plus watchdog
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
Description=Run ALL VideoDownload Plus watchdog every minute

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

For the 视某号 Yuanbao fallback, set the runtime environment value after `scripts/init-local.sh` has created `vendor/tg-ytdlp-bot/.env`:

```env
WECHAT_CHANNELS_YUANBAO_COOKIE=
WECHAT_CHANNELS_TIMEOUT=30
```

You can update this at runtime by sending `/set_yuanbao_cookie` to the bot as an admin and replying with a cookie file or Cookie header.

### 某音 Cookie Update

某音 can often work without a personal Cookie, but keeping a fresh Cookie improves success rate when platform anti-bot checks change.

Supported input formats:

- Netscape `cookies.txt` exported from the browser;
- raw request header, for example `Cookie: name=value; name2=value2`.

Update steps:

1. Log in to the 某音 website in your browser.
2. Export the platform cookies as Netscape cookies.txt, or copy a request `Cookie` header from the platform.
3. Save it as:

   ```text
   deploy/cookies/douyin.txt
   ```

4. Re-run initialization so the cookie is synchronized into the optional 某音 sidecar:

   ```bash
   scripts/init-local.sh
   scripts/local-up.sh
   ```

On a VPS, run the same commands inside the deployed project directory, for example `/opt/video-download-bot`.

Notes:

- `deploy/cookies/douyin.txt` is ignored by Git.
- Public-safe packages created by `scripts/package-for-vps.sh` exclude it.
- Private migration packages created with `--include-private` can include it, so keep those archives private.

### 视某号 Yuanbao Cookie

Some 视某号 shared links only expose preview metadata from the public page. For those links, this project can optionally use a logged-in Tencent Yuanbao web Cookie as a fallback.

Yuanbao entry:

- Current web app and login page: <https://yuanbao.tencent.com/>
- The former `/chat/` URL now redirects to the web app root.

Recommended workflow:

1. Open <https://yuanbao.tencent.com/> in your browser and log in.
2. Open browser developer tools, refresh the page, then find an authenticated request to `yuanbao.tencent.com`.
3. Copy the request `Cookie` header, or export it as a cookie file.
4. As an admin, open `/settings` -> Cookies -> `Update 视某号 Yuanbao Cookie`, or select `/set_yuanbao_cookie` from the Telegram command menu.
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
- Optional 某音/TT sidecar: `Evil0ctal/Douyin_TikTok_Download_API`.
- Custom work in this repo: deployment wrapper, privacy hardening, custom 某音/视某号 resolvers, Telegram admin cookie update command, TT compatibility format selection, tests, documentation, and VPS/local operational workflow, developed with Codex assistance.

## Legal and Safety Notice

Use this only for content you own, have permission to download, or are legally allowed to archive. Respect platform terms, copyright, creator rights, and local law.

Never commit real bot tokens, Telegram API credentials, cookies, session files, or generated archives.
