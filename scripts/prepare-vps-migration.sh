#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/video-download-bot}"
APP_DIR="${APP_DIR:-$PROJECT_DIR/vendor/tg-ytdlp-bot}"
OUTPUT_DIR="${OUTPUT_DIR:-/root/video-download-migrations}"
stamp="$(date +%Y%m%d-%H%M%S)"
archive="$OUTPUT_DIR/video-download-bot-private-$stamp.tar.gz"
app_was_running=0

if [ ! -x "$PROJECT_DIR/scripts/package-for-vps.sh" ] || [ ! -f "$APP_DIR/docker-compose.yml" ]; then
  echo "Video Download Bot System is not initialized under $PROJECT_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
chmod 700 "$OUTPUT_DIR"

cd "$APP_DIR"
if docker compose ps --status running --services | grep -qx app; then
  app_was_running=1
fi

restore_app() {
  if [ "$app_was_running" = "1" ]; then
    cd "$APP_DIR"
    docker compose up -d --no-deps app >/dev/null
  fi
}
trap restore_app EXIT INT TERM

if [ "$app_was_running" = "1" ]; then
  docker compose stop -t 30 app
fi

"$PROJECT_DIR/scripts/package-for-vps.sh" --include-private --output "$archive"
chmod 600 "$archive" "$archive.sha256"
tar -tzf "$archive" >/dev/null

restore_app
app_was_running=0
trap - EXIT INT TERM

if [ -f "$APP_DIR/CONFIG/config.py" ] && ! tar -tzf "$archive" | grep -q 'vendor/tg-ytdlp-bot/CONFIG/config.py$'; then
  echo "Migration archive is missing the runtime config" >&2
  exit 1
fi

echo "Migration archive ready: $archive"
echo "Checksum: $archive.sha256"
echo "The source Bot is running again. Stop it before starting this Bot on a new VPS."
