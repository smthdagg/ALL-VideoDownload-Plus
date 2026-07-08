#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/vendor/tg-ytdlp-bot"

if [ ! -f "$APP_DIR/CONFIG/config.py" ]; then
  echo "Missing $APP_DIR/CONFIG/config.py. Run scripts/init-local.sh first."
  exit 1
fi

cd "$APP_DIR"
docker compose up -d --build
docker compose ps

echo "Dashboard: http://localhost:5555"
echo "Logs: scripts/logs.sh"

