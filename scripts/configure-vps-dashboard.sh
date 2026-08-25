#!/usr/bin/env bash
set -euo pipefail

# Configure the public dashboard when the VPS already uses host port 443.
PROJECT_DIR="${PROJECT_DIR:-/opt/video-download-bot}"
APP_DIR="${APP_DIR:-$PROJECT_DIR/vendor/tg-ytdlp-bot}"
DASHBOARD_DOMAIN="${DASHBOARD_DOMAIN:-v.oaclub.com}"
DASHBOARD_HTTPS_PORT="${DASHBOARD_HTTPS_PORT:-8443}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/video-download-backups}"

if [ ! -f "$APP_DIR/docker-compose.yml" ] || [ ! -f "$PROJECT_DIR/deploy/config.local.py" ]; then
  echo "Missing deployed project or private config under $PROJECT_DIR" >&2
  exit 1
fi

stamp="$(date +%Y%m%d-%H%M%S)"
backup="$BACKUP_ROOT/dashboard-$stamp"
mkdir -p "$backup"
cp "$APP_DIR/docker-compose.yml" "$backup/docker-compose.yml"
cp "$APP_DIR/docker/configuration-webserver/conf/Caddyfile" "$backup/Caddyfile"
cp "$PROJECT_DIR/deploy/config.local.py" "$backup/config.local.py"

python3 - "$APP_DIR/docker-compose.yml" "$DASHBOARD_HTTPS_PORT" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
https_port = sys.argv[2]
text = path.read_text(encoding="utf-8")
marker = "  configuration-webserver:\n    image: caddy:2-alpine\n"
replacement = (
    "  configuration-webserver:\n"
    "    image: caddy:2-alpine\n"
    "    ports:\n"
    "      - \"80:80\"\n"
    f"      - \"{https_port}:443\"\n"
    f"      - \"{https_port}:443/udp\"\n"
)
if f'      - "{https_port}:443"' not in text:
    if marker not in text:
        raise SystemExit("Caddy service marker not found")
    text = text.replace(marker, replacement, 1)
path.write_text(text, encoding="utf-8")
PY

python3 - "$PROJECT_DIR/deploy/config.local.py" "$DASHBOARD_DOMAIN" "$DASHBOARD_HTTPS_PORT" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
domain = sys.argv[2]
port = sys.argv[3]
text = path.read_text(encoding="utf-8")
updated = re.sub(
    r"(?m)^\s*DASHBOARD_PUBLIC_URL\s*=.*$",
    f'    DASHBOARD_PUBLIC_URL = "https://{domain}:{port}"',
    text,
    count=1,
)
if updated == text:
    marker = re.search(r"(?m)^\s*DASHBOARD_PASSWORD\s*=.*$", text)
    if not marker:
        raise SystemExit("DASHBOARD_PASSWORD setting not found")
    line_end = text.find("\n", marker.end())
    if line_end < 0:
        line_end = len(text)
    updated = text[:line_end + 1] + f'    DASHBOARD_PUBLIC_URL = "https://{domain}:{port}"\n' + text[line_end + 1:]
path.write_text(updated, encoding="utf-8")
PY

template="$PROJECT_DIR/deploy/Caddyfile.dashboard.example"
if [ ! -f "$template" ]; then
  echo "Missing $template" >&2
  exit 1
fi
sed "s/bot-admin\.example\.com/$DASHBOARD_DOMAIN/g; s/:8443/:$DASHBOARD_HTTPS_PORT/g"   "$template" > "$APP_DIR/docker/configuration-webserver/conf/Caddyfile"

cd "$APP_DIR"
docker compose config >/dev/null
docker compose up -d --no-deps --force-recreate configuration-webserver
sleep 8
docker compose ps configuration-webserver app
curl -fsS http://127.0.0.1:5555/health
printf '\nDashboard URL: https://%s:%s\n' "$DASHBOARD_DOMAIN" "$DASHBOARD_HTTPS_PORT"
printf 'Backup: %s\n' "$backup"
