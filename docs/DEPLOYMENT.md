# Deployment

This project supports two normal workflows:

1. local Docker testing;
2. VPS Docker deployment for 24-hour operation.

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

## Dashboard Access

The dashboard should stay bound to localhost on the VPS:

```bash
ssh -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

Then open:

```text
http://localhost:5555
```

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

## Updating Upstream

Run:

```bash
scripts/init-local.sh
```

The script updates/clones upstream under `vendor/tg-ytdlp-bot`, reapplies local
patches, and rewrites the runtime Docker files.
