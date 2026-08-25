#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
APP_DIR="$PROJECT_DIR/vendor/tg-ytdlp-bot"

if [ ! -f "$PROJECT_DIR/deploy/config.local.py" ]; then
  echo "This is a public-safe package. Create deploy/config.local.py before activation." >&2
  exit 1
fi

echo "Confirm the source VPS app is stopped before activating this Telegram Bot."
"$PROJECT_DIR/scripts/init-local.sh"

cd "$APP_DIR"
docker compose config >/dev/null
docker compose up -d --build

if [ "$(id -u)" -eq 0 ] && command -v systemctl >/dev/null 2>&1; then
  PROJECT_DIR="$PROJECT_DIR" APP_DIR="$APP_DIR" "$PROJECT_DIR/scripts/install-vps-operations.sh"
fi

for attempt in 1 2 3 4 5 6; do
  if curl -fsS http://127.0.0.1:5555/health >/dev/null; then
    break
  fi
  if [ "$attempt" = "6" ]; then
    echo "Dashboard health check failed" >&2
    docker compose logs --tail=100 app >&2
    exit 1
  fi
  sleep 5
done

docker compose ps
echo "Migration activation completed. Configure the public dashboard separately if needed."
