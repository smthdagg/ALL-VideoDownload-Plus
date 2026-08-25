# Video Download Bot System Deployment

This project supports two normal workflows:

1. local Docker testing;
2. VPS Docker deployment for 24-hour operation.

The recommended lifecycle is: test locally, stop the local Bot, deploy one copy to the VPS, and keep the dashboard private. Do not run the same Telegram Bot account locally and on the VPS at the same time.

## Current VPS Profile

The reference deployment for this repository uses:

- SSH port: `2222`;
- project directory: `/opt/video-download-bot`;
- public dashboard: `https://v.oaclub.com:8443`;
- internal dashboard: `127.0.0.1:5555`;
- dashboard proxy: the Compose Caddy service;
- existing host port 443: reserved for the VPS proxy service.

The public dashboard can be recreated with `scripts/configure-vps-dashboard.sh`. The script makes a dated backup before changing the Compose port mapping, Caddy configuration, or private dashboard URL.

## Local Docker

```bash
cp .env.example .env
scripts/init-local.sh
```

Fill `deploy/config.local.py`, then run:

```bash
scripts/init-local.sh
scripts/local-up.sh
```

Useful commands:

```bash
scripts/logs.sh
scripts/local-down.sh
```

## VPS Deployment By Git Clone

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

The SSH port is independent of Docker and Telegram. For a VPS using port `2222`:

```bash
ssh -p 2222 root@YOUR_VPS
```

## VPS Deployment By Archive

Public-safe package:

```bash
scripts/package-for-vps.sh
```

Private migration package:

```bash
scripts/package-for-vps.sh --include-private
```

Use `--include-private` only for your own server. That archive can include
tokens, cookies, and session files.

Never publish a private migration archive. It may also contain user data and runtime state.

## Dashboard Access

The dashboard should stay bound to localhost on the VPS:

```bash
ssh -p 2222 -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

Then open:

```text
http://localhost:5555
```

### Public dashboard when port 443 is occupied

Some VPS installations already use host port 443 for a proxy or panel. Keep that service unchanged and publish this dashboard through a separate HTTPS port:

```text
https://bot-admin.example.com:8443
```

Use [deploy/Caddyfile.dashboard.example](../deploy/Caddyfile.dashboard.example) as the reverse-proxy template. Map host port `80` to Caddy port `80` for ACME validation and host port `8443` to Caddy port `443` for HTTPS. The Caddy site proxies to the Compose service `app:5555`.

For the standard VPS layout, run [scripts/configure-vps-dashboard.sh](../scripts/configure-vps-dashboard.sh) from `/opt/video-download-bot`. It creates a dated backup, updates the private public URL, configures Caddy, validates Compose, and restarts only the Caddy service.

Set the matching value in the private `deploy/config.local.py` when configuring manually:

```python
DASHBOARD_PUBLIC_URL = "https://bot-admin.example.com:8443"
```

Verify the HTTPS login page and `/health` before sharing the URL. Keep the dashboard password independent from Telegram credentials.

### Public dashboard when port 443 is occupied

Some VPS installations already use host port 443 for a proxy or panel. Keep that service unchanged and publish this dashboard through a separate HTTPS port:

```text
https://bot-admin.example.com:8443
```

Use [deploy/Caddyfile.dashboard.example](../deploy/Caddyfile.dashboard.example) as the reverse-proxy template. Map host port `80` to Caddy port `80` for ACME validation and host port `8443` to Caddy port `443` for HTTPS. The Caddy site proxies to the Compose service `app:5555`.

Set the matching value in the private `deploy/config.local.py`:

```python
DASHBOARD_PUBLIC_URL = "https://bot-admin.example.com:8443"
```

After changing the private config, run `scripts/init-local.sh` and restart the `app` service. Verify the HTTPS login page and `/health` before sharing the URL. Keep the dashboard password independent from Telegram credentials.

## Cookie Maintenance

Place site cookies in `deploy/cookies/*.txt`. Keep them in Netscape cookies.txt
format unless a resolver explicitly says otherwise.

For Douyin, put the exported cookie or raw Cookie header in:

```text
deploy/cookies/douyin.txt
```

Then run:

```bash
scripts/init-local.sh
scripts/local-up.sh
```

For WeChat Channels Yuanbao fallback, either set
`WECHAT_CHANNELS_YUANBAO_COOKIE` in `vendor/tg-ytdlp-bot/.env`, or send
`/set_yuanbao_cookie` to the bot as an admin and reply with a cookie file or
Cookie header.

Cookies are login credentials. They can expire after logout, security changes,
or session invalidation. Never commit them, include them in a public archive, or
paste them into issue reports. See the bilingual README for the current Douyin
and Yuanbao capture workflows.

## Updating Upstream

Run:

```bash
scripts/init-local.sh
```

The script updates/clones upstream under `vendor/tg-ytdlp-bot`, reapplies local
patches, and rewrites the runtime Docker files.
