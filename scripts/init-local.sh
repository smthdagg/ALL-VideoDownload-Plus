#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$ROOT_DIR/vendor/tg-ytdlp-bot"

"$ROOT_DIR/scripts/bootstrap-upstream.sh"

if [ ! -f "$ROOT_DIR/deploy/config.local.py" ]; then
  cp "$ROOT_DIR/deploy/config.local.py.example" "$ROOT_DIR/deploy/config.local.py"
  echo "Created deploy/config.local.py. Fill Telegram values, then run this script again."
  exit 1
fi

cp "$ROOT_DIR/deploy/config.local.py" "$APP_DIR/CONFIG/config.py"
python3 "$ROOT_DIR/scripts/apply-private-hardening.py"

if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
fi

if grep -q '^TZ=' "$APP_DIR/.env"; then
  sed -i.bak 's|^TZ=.*|TZ=Asia/Singapore|' "$APP_DIR/.env"
  rm -f "$APP_DIR/.env.bak"
else
  printf '\nTZ=Asia/Singapore\n' >> "$APP_DIR/.env"
fi

ensure_env_var() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "$APP_DIR/.env"; then
    printf '%s=%s\n' "$key" "$value" >> "$APP_DIR/.env"
  fi
}

ensure_env_var "DOUYIN_REMOTE_RESOLVER_URL" ""
ensure_env_var "DOUYIN_REMOTE_RESOLVER_METHOD" "GET"
ensure_env_var "DOUYIN_REMOTE_RESOLVER_HEADERS_JSON" ""
ensure_env_var "REQABLE_CAPTURE_DIR" "$HOME/Library/Application Support/com.reqable.macosx/capture"
ensure_env_var "DOUYIN_REQABLE_CAPTURE_DIR" "/reqable-capture"
ensure_env_var "DOUYIN_REQABLE_CAPTURE_MAX_AGE_SECONDS" "7200"
ensure_env_var "DOUYIN_REQABLE_CAPTURE_ENABLED" "0"
ensure_env_var "DOUYIN_REQABLE_CAPTURE_FIRST" "0"
ensure_env_var "WECHAT_CHANNELS_YUANBAO_COOKIE" ""
ensure_env_var "WECHAT_CHANNELS_TIMEOUT" "30"

mkdir -p "$ROOT_DIR/deploy/cookies" "$APP_DIR/docker/configuration-webserver/site/cookies"
mkdir -p "$APP_DIR/docker/reqable-capture-empty"
for name in cookie youtube youtube-1 youtube-2 youtube-3 youtube-4 youtube-5 youtube-6 youtube-7 youtube-8 youtube-9 youtube-10 instagram tiktok twitter facebook vk; do
  src="$ROOT_DIR/deploy/cookies/$name.txt"
  dst="$APP_DIR/docker/configuration-webserver/site/cookies/$name.txt"
  if [ -f "$src" ]; then
    cp "$src" "$dst"
  elif [ ! -f "$dst" ]; then
    : > "$dst"
  fi
done

"$ROOT_DIR/scripts/sync-douyin-cookie.sh"

echo "Local config initialized."
echo "Next: scripts/local-up.sh"
