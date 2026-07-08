#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/vendor/tg-ytdlp-bot"
COOKIE_FILE="$ROOT_DIR/deploy/cookies/douyin.txt"
CONFIG_DIR="$APP_DIR/docker/douyin-api/douyin_web"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
IMAGE="evil0ctal/douyin_tiktok_download_api:latest"

if [ ! -f "$COOKIE_FILE" ]; then
  fallback_cookie_file="$(find "$APP_DIR/users" -maxdepth 2 -name cookie.txt -print 2>/dev/null | head -n 1 || true)"
  if [ -n "$fallback_cookie_file" ]; then
    COOKIE_FILE="$fallback_cookie_file"
  fi
fi

if [ ! -f "$COOKIE_FILE" ]; then
  echo "No deploy/cookies/douyin.txt found; Douyin sidecar will use its image default cookie."
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not available; cannot prepare Douyin sidecar config yet."
  exit 0
fi

mkdir -p "$CONFIG_DIR"
tmp_config="$(mktemp)"
trap 'rm -f "$tmp_config"' EXIT

docker run --rm --entrypoint cat "$IMAGE" /app/crawlers/douyin/web/config.yaml > "$tmp_config"

python3 - "$COOKIE_FILE" "$tmp_config" "$CONFIG_FILE" <<'PY'
import json
import re
import sys
from pathlib import Path

cookie_path = Path(sys.argv[1])
template_path = Path(sys.argv[2])
output_path = Path(sys.argv[3])


def from_netscape(text: str) -> str:
    allowed_domains = {".douyin.com", "www.douyin.com"}
    values = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 7 or cols[0] not in allowed_domains:
            continue
        name = cols[5].strip()
        value = cols[6].strip()
        if name and value and name != "douyin.com":
            values[name] = value
    return "; ".join(f"{name}={value}" for name, value in values.items())


def from_raw_header(text: str) -> str:
    cleaned = text.strip()
    if cleaned.lower().startswith("cookie:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    return " ".join(line.strip() for line in cleaned.splitlines() if line.strip())


cookie_text = cookie_path.read_text(encoding="utf-8", errors="ignore")
cookie_header = from_netscape(cookie_text) if "\t" in cookie_text else from_raw_header(cookie_text)
if not cookie_header:
    raise SystemExit(f"No Douyin cookies found in {cookie_path}")

template = template_path.read_text(encoding="utf-8")
replacement = "      Cookie: " + json.dumps(cookie_header, ensure_ascii=False)
updated, count = re.subn(r"^      Cookie: .*$", replacement, template, count=1, flags=re.MULTILINE)
if count != 1:
    raise SystemExit("Could not find Douyin Cookie field in sidecar config template")

output_path.write_text(updated, encoding="utf-8")
print(f"Prepared Douyin sidecar config from {cookie_path} ({cookie_header.count(';') + 1} cookies).")
PY
