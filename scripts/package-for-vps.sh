#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="$ROOT_DIR/deploy/package"
ARCHIVE="$ROOT_DIR/video-download-bot-vps.tar.gz"
INCLUDE_PRIVATE=0

if [ "${1:-}" = "--include-private" ]; then
  INCLUDE_PRIVATE=1
fi

rm -rf "$PACKAGE_DIR" "$ARCHIVE"
mkdir -p "$PACKAGE_DIR"

RSYNC_EXCLUDES=(
  --exclude '.git'
  --exclude 'vendor/tg-ytdlp-bot/.git'
  --exclude '**/__pycache__'
  --exclude '**/*.pyc'
  --exclude 'vendor/tg-ytdlp-bot/users'
  --exclude 'vendor/tg-ytdlp-bot/download'
  --exclude 'vendor/tg-ytdlp-bot/downloads'
  --exclude 'vendor/tg-ytdlp-bot/logs'
  --exclude 'vendor/tg-ytdlp-bot/bot.log'
  --exclude 'vendor/tg-ytdlp-bot/dump.json'
  --exclude 'vendor/tg-ytdlp-bot/magic.session-shm'
  --exclude 'vendor/tg-ytdlp-bot/magic.session-wal'
  --exclude 'vendor/tg-ytdlp-bot/docker/reqable-capture-empty/*'
  --exclude 'deploy/package'
  --exclude 'video-download-bot-vps.tar.gz'
  --exclude '.private'
)

if [ "$INCLUDE_PRIVATE" != "1" ]; then
  RSYNC_EXCLUDES+=(
    --exclude 'deploy/config.local.py'
    --exclude 'deploy/cookies/*.txt'
    --exclude 'vendor/tg-ytdlp-bot/.env'
    --exclude 'vendor/tg-ytdlp-bot/magic.session'
    --exclude 'vendor/tg-ytdlp-bot/docker/configuration-webserver/site/cookies/*.txt'
    --exclude 'vendor/tg-ytdlp-bot/docker/douyin-api/douyin_web/config.yaml'
  )
fi

rsync -a "${RSYNC_EXCLUDES[@]}" "$ROOT_DIR/" "$PACKAGE_DIR/"

tar -C "$PACKAGE_DIR/.." -czf "$ARCHIVE" "$(basename "$PACKAGE_DIR")"

echo "Created $ARCHIVE"
if [ "$INCLUDE_PRIVATE" = "1" ]; then
  echo "Warning: archive includes private config/cookies/session files. Keep it private."
else
  echo "Public-safe archive: private config, cookies, .env, and Telegram session files were excluded."
  echo "Use --include-private only for personal VPS migration archives."
fi
echo "Upload example:"
echo "  scp $ARCHIVE root@YOUR_VPS:/opt/"
echo "  ssh root@YOUR_VPS 'mkdir -p /opt/video-download-bot && tar -xzf /opt/video-download-bot-vps.tar.gz -C /opt/video-download-bot --strip-components=1 && cd /opt/video-download-bot && scripts/init-local.sh && scripts/local-up.sh'"
