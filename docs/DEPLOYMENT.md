# Video Download Bot System Deployment And Migration

This document is the canonical runbook for local installation, VPS deployment,
backup, migration, rollback, and handoff. Production hostnames, IP addresses,
SSH ports, credentials, and cookies are intentionally not stored in Git.

中文版本：[DEPLOYMENT.zh-CN.md](DEPLOYMENT.zh-CN.md)

## Requirements

- Docker Engine or Docker Desktop
- Docker Compose v2
- Git
- Python 3
- `rsync`, `tar`, and a SHA-256 utility
- A Telegram Bot token plus Telegram `API_ID` and `API_HASH`

The supported container baseline is Python 3.12, stable yt-dlp 2026.08.19, and
bgutil-ytdlp-pot-provider 1.3.2.

## Local Installation

```bash
git clone https://github.com/smthdagg/VideoDownload.git
cd VideoDownload
cp .env.example .env
scripts/init-local.sh
```

The first initialization creates ignored `deploy/config.local.py`. Fill the
Telegram values, numeric administrator ID, log chat ID, and independent Web
dashboard credentials. Then run:

```bash
scripts/init-local.sh
python3 -m unittest discover -s tests
scripts/local-up.sh
```

Open `http://localhost:5555`. Stop the local service before starting the same
Bot on a VPS:

```bash
scripts/local-down.sh
```

## Fresh VPS Installation

```bash
git clone https://github.com/smthdagg/VideoDownload.git /opt/video-download-bot
cd /opt/video-download-bot
cp .env.example .env
cp deploy/config.local.py.example deploy/config.local.py
```

Fill `deploy/config.local.py`, then initialize, test, and start:

```bash
scripts/init-local.sh
python3 -m unittest discover -s tests
scripts/local-up.sh
sudo scripts/install-vps-operations.sh
```

Verify:

```bash
cd /opt/video-download-bot/vendor/tg-ytdlp-bot
docker compose ps
docker compose exec -T app pip check
curl -fsS http://127.0.0.1:5555/health
systemctl is-active video-download-watchdog.timer
systemctl is-active video-download-runtime-cleanup.timer
```

## Dashboard

The application binds the dashboard to `127.0.0.1:5555`. For private access,
use an SSH tunnel with the deployment's actual SSH port:

```bash
ssh -p YOUR_SSH_PORT -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

When a public HTTPS dashboard is required and host port 443 is occupied, use
Caddy on host port 8443:

```bash
cd /opt/video-download-bot
DASHBOARD_DOMAIN=bot-admin.example.com \
DASHBOARD_HTTPS_PORT=8443 \
scripts/configure-vps-dashboard.sh
```

The script backs up Compose, Caddy, and the private config before making a
change. It does not contain a default production hostname. Ensure DNS points to
the VPS and verify `https://bot-admin.example.com:8443/login`.

## Public-Safe Package

Create a package suitable for inspection or transfer without credentials:

```bash
scripts/package-for-vps.sh
```

The package excludes private config, cookies, sessions, dynamic users, user
directories, runtime databases, downloaded media, logs, TLS state, SSH keys,
generated archives, and the reproducible vendor tree. It includes a manifest
and SHA-256 checksum; `scripts/init-local.sh` clones the vendor tree on target.

## Prepare A Private VPS Migration

Run this on the source VPS:

```bash
cd /opt/video-download-bot
sudo scripts/prepare-vps-migration.sh
```

The script:

1. records whether the Bot is running;
2. stops only the `app` container so the Telegram session is consistent;
3. packages private config, cookies, Telegram session, dynamic authorization,
   user preferences, and runtime database;
4. excludes downloaded media, transient logs, Caddy TLS private state, caches,
   SSH keys, and prior archives;
5. writes a SHA-256 checksum and sets both files to mode 600;
6. restores the source Bot automatically, including after a packaging error.

Archives are written under `/root/video-download-migrations` by default. Never
upload them to GitHub or send them through an untrusted channel.

## Transfer And Restore On A New VPS

Copy the archive and checksum using the deployment's SSH port:

```bash
scp -P YOUR_SSH_PORT \
  root@OLD_VPS:/root/video-download-migrations/video-download-bot-private-TIMESTAMP.tar.gz* \
  /root/
```

On the new VPS, verify the checksum:

```bash
cd /root
sha256sum -c video-download-bot-private-TIMESTAMP.tar.gz.sha256
```

Inspect and extract without replacing an unrelated directory:

```bash
mkdir -p /opt/video-download-bot
tar -tzf /root/video-download-bot-private-TIMESTAMP.tar.gz | head
tar -xzf /root/video-download-bot-private-TIMESTAMP.tar.gz \
  -C /opt/video-download-bot --strip-components=1
```

Before activation, stop the old VPS Bot to prevent two servers using the same
Telegram session:

```bash
ssh -p YOUR_SSH_PORT root@OLD_VPS \
  'cd /opt/video-download-bot/vendor/tg-ytdlp-bot && docker compose stop app'
```

Activate the new VPS:

```bash
cd /opt/video-download-bot
sudo scripts/restore-vps-migration.sh
```

The restore script reconnects an archive's vendor directory to upstream Git,
reapplies all tracked patches, validates Compose, rebuilds the containers,
installs operational timers, and checks dashboard health. Configure the public
dashboard separately because hostnames are deployment-specific.

## Migration Acceptance Checklist

```bash
cd /opt/video-download-bot/vendor/tg-ytdlp-bot
docker compose ps
docker compose exec -T app pip check
curl -fsS http://127.0.0.1:5555/health
docker compose logs --since=5m app | grep -E 'Session started|Started [0-9]+ HandlerTasks'
systemctl is-active video-download-watchdog.timer video-download-runtime-cleanup.timer
```

Then test one authorized Telegram message and representative links for TikTok,
Douyin, WeChat Channels, Instagram, X/Twitter, and YouTube. Confirm audio and
video streams for TikTok rather than checking only that a file exists.

## Rollback

Do not delete the old VPS until the new VPS passes the acceptance checklist.
If activation fails:

1. stop the new VPS `app` container;
2. start the old VPS `app` container;
3. inspect the new VPS logs and keep the migration archive unchanged;
4. retry only after fixing the tracked project or deployment-specific config.

For an in-place upgrade, make a dated runtime backup and tag the current app
image before rebuilding. Restore the files and old image if startup, Telegram
session, dashboard health, or a real download test fails.

## Updating Upstream

`scripts/init-local.sh` updates the upstream checkout and reapplies the tracked
patch layer. Updates are not deployed blindly. Run tests, build, and real URL
checks before replacing the active VPS container.

## Handoff

Future coding agents must read [AGENTS.md](../AGENTS.md) first. The ignored
`vendor/tg-ytdlp-bot` tree is generated output; durable fixes belong in
`scripts/apply-private-hardening.py`, `scripts/templates/`, tests, and docs.
