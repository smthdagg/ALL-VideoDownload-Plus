# ALL VideoDownload Plus

[中文使用说明](README.zh-CN.md) · [Deployment](docs/DEPLOYMENT.md) · [Cookie import](docs/COOKIE-IMPORT.md) · [Security](docs/SECURITY.md)

A self-hosted Telegram media downloader with a maintained wrapper around `upekshaip/tg-ytdlp-bot`. It adds platform resolvers, personal Cookie TXT import, Chinese/English navigation, access approval, a Web dashboard and VPS maintenance scripts. The upstream application is generated under `vendor/`; tracked templates and the patch generator are the source of custom behavior.

## Use the Bot

Send an original video/post URL or share text in a private chat. When supported by the platform and your account, the Bot downloads and returns media. Accounts must be approved in private deployments.

- **Start**: download tools, Settings, Help; administrators also see **User management**.
- **Settings**: download preferences, Cookies & accounts, interface & language, files & activity, advanced settings.
- **Cookies & accounts**: upload a browser-exported Netscape `cookies.txt` (UTF-8, at most100KB). Sites are detected automatically; platform selection is optional. Multiple sites can share one file. Only imported sites are replaced; others are preserved. The next download uses the new file without another command or restart.
- **User management**: approve requests, add/remove users, manage access. Personal download settings and Cookies are not administrator functions.

The visible Telegram command menu is intentionally short: `/start`, `/settings`, `/cookie`, `/help`; `/users` appears only for administrators. Advanced commands remain compatible but are grouped under the corresponding settings pages. Old Cookie buttons lead to the single importer; there is no separate Yuanbao update menu.

### Platform support

| Platform | Project support | Notes |
|---|---|---|
| WeChat Channels | Public preview/media resolver plus optional Yuanbao enhancement | Some links need a valid **Yuanbao** login Cookie. Preview metadata alone is not a downloadable video. |
| Douyin | Mobile/share-page resolver and optional API sidecar | Requires a working network path; some content requires a valid login. |
| TikTok | Bounded challenge retries and Telegram-compatible formats | Platform challenges can still prevent extraction. |
| X/Twitter | Multiple-video posts | Restricted posts may require Cookie import. |
| YouTube | yt-dlp and PO-token provider | Availability depends on account, region and platform restrictions. |
| Bilibili, Xiaohongshu | yt-dlp/gallery-dl plus the existing Xiaohongshu share integration | Import the platform's Cookie when login is required. |
| Instagram and other upstream-supported sites | yt-dlp/gallery-dl | Support depends on the upstream extractor and site rules. |

Importing a file does not renew a platform session or bypass account restrictions. A valid file can still contain a login revoked by the platform. Re-export after logging in when necessary.

## Install

Requirements: Docker/Compose v2, Git, Python3 and a Telegram Bot token plus Telegram API credentials.

```bash
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git
cd ALL-VideoDownload-Plus
cp .env.example .env
cp deploy/config.local.py.example deploy/config.local.py
# Fill the ignored config with your Telegram and dashboard credentials.
scripts/init-local.sh
python3 -m unittest discover -s tests
scripts/local-up.sh
```

The dashboard binds to `127.0.0.1:5555`. See the [deployment runbook](docs/DEPLOYMENT.md) for VPS installation, HTTPS, backup and rollback. Do not run the same Bot session on two hosts concurrently.

## Development

Custom sources: `scripts/templates/` and `scripts/apply-private-hardening.py`. Regenerate the ignored vendor tree before testing:

```bash
python3 scripts/apply-private-hardening.py
python3 -m unittest discover -s tests
python3 -m py_compile scripts/apply-private-hardening.py scripts/templates/*.py
```

Runtime changes also require Compose validation, an app image build, dependency checks, backup and live health verification. See [AGENTS.md](AGENTS.md).

Configuration, tokens, Cookie jars, Telegram sessions, user data and private backups are excluded from public source. Examples use placeholders. Historical platform snapshots are implementation references, not current usage instructions. See [architecture](docs/ARCHITECTURE.md), [credits](docs/CREDITS.md) and [license](LICENSE).

## Operations

VPS watchdog and runtime cleanup timers are provided by the operations installer. Restart and IP rotation are host operations; the dashboard reports the host boundary instead of restarting the container from inside itself. Configure storage thresholds and retention through the deployment environment; see the deployment runbook.
