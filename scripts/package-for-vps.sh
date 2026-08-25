#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INCLUDE_PRIVATE=0
OUTPUT=""

usage() {
  cat <<'EOF'
Usage: scripts/package-for-vps.sh [--include-private] [--output ARCHIVE]

Without --include-private, creates a public-safe package without credentials or
runtime user state. Private mode is only for migration between servers you own.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --include-private)
      INCLUDE_PRIVATE=1
      shift
      ;;
    --output)
      [ "$#" -ge 2 ] || { echo "--output requires a path" >&2; exit 2; }
      OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$OUTPUT" ]; then
  if [ "$INCLUDE_PRIVATE" = "1" ]; then
    OUTPUT="$ROOT_DIR/video-download-bot-private-migration.tar.gz"
  else
    OUTPUT="$ROOT_DIR/video-download-bot-vps.tar.gz"
  fi
fi

mkdir -p "$(dirname "$OUTPUT")"
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/video-download-package.XXXXXX")"
PACKAGE_DIR="$STAGING/video-download-bot"
trap 'rm -rf "$STAGING"' EXIT
mkdir -p "$PACKAGE_DIR"

RSYNC_EXCLUDES=(
  --exclude '.git'
  --exclude 'vendor/tg-ytdlp-bot/.git'
  --exclude '**/__pycache__'
  --exclude '**/*.pyc'
  --exclude 'vendor/tg-ytdlp-bot/users/*/downloads'
  --exclude 'vendor/tg-ytdlp-bot/download'
  --exclude 'vendor/tg-ytdlp-bot/downloads'
  --exclude 'vendor/tg-ytdlp-bot/logs'
  --exclude 'vendor/tg-ytdlp-bot/bot.log'
  --exclude 'vendor/tg-ytdlp-bot/magic.session-shm'
  --exclude 'vendor/tg-ytdlp-bot/magic.session-wal'
  --exclude 'vendor/tg-ytdlp-bot/docker/configuration-webserver/data'
  --exclude 'vendor/tg-ytdlp-bot/docker/configuration-webserver/config'
  --exclude 'vendor/tg-ytdlp-bot/docker/reqable-capture-empty/*'
  --exclude 'deploy/package'
  --exclude '*.tar.gz'
  --exclude '*.sha256'
  --exclude '.private'
  --exclude '*.pem'
  --exclude 'sshkey*'
)

if [ "$INCLUDE_PRIVATE" != "1" ]; then
  RSYNC_EXCLUDES+=(
    --exclude '.env'
    --exclude 'deploy/config.local.py'
    --exclude 'deploy/cookies/*.txt'
    --exclude 'vendor/tg-ytdlp-bot/.env'
    --exclude 'vendor/tg-ytdlp-bot/magic.session'
    --exclude 'vendor/tg-ytdlp-bot/CONFIG/config.py'
    --exclude 'vendor/tg-ytdlp-bot/CONFIG/.active_sessions.json'
    --exclude 'vendor/tg-ytdlp-bot/CONFIG/private_users.json'
    --exclude 'vendor/tg-ytdlp-bot/TXT/cookie.txt'
    --exclude 'vendor/tg-ytdlp-bot/users'
    --exclude 'vendor/tg-ytdlp-bot/dump.json'
    --exclude 'vendor/tg-ytdlp-bot/docker/configuration-webserver/site/cookies/*.txt'
    --exclude 'vendor/tg-ytdlp-bot/docker/douyin-api/douyin_web/config.yaml'
    --exclude 'vendor/tg-ytdlp-bot'
  )
fi

rsync -a "${RSYNC_EXCLUDES[@]}" "$ROOT_DIR/" "$PACKAGE_DIR/"

root_commit="unavailable"
upstream_commit="unavailable"
if git -C "$ROOT_DIR" rev-parse HEAD >/dev/null 2>&1; then
  root_commit="$(git -C "$ROOT_DIR" rev-parse HEAD)"
fi
if git -C "$ROOT_DIR/vendor/tg-ytdlp-bot" rev-parse HEAD >/dev/null 2>&1; then
  upstream_commit="$(git -C "$ROOT_DIR/vendor/tg-ytdlp-bot" rev-parse HEAD)"
fi

cat >"$PACKAGE_DIR/MIGRATION-MANIFEST.txt" <<EOF
ALL VideoDownload Plus migration package
Created UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Mode: $([ "$INCLUDE_PRIVATE" = "1" ] && echo private || echo public-safe)
Project commit: $root_commit
Upstream commit: $upstream_commit
Restore guide: docs/DEPLOYMENT.md
EOF

rm -f "$OUTPUT" "$OUTPUT.sha256"
tar -C "$STAGING" -czf "$OUTPUT" video-download-bot
members_file="$STAGING/archive-members.txt"
tar -tzf "$OUTPUT" >"$members_file"

if [ "$INCLUDE_PRIVATE" != "1" ]; then
  forbidden='(^|/)deploy/config\.local\.py$|(^|/)vendor/tg-ytdlp-bot/\.env$|(^|/)vendor/tg-ytdlp-bot/magic\.session$|(^|/)vendor/tg-ytdlp-bot/CONFIG/private_users\.json$|(^|/)vendor/tg-ytdlp-bot/users(/|$)|(^|/)deploy/cookies/[^/]+\.txt$'
  if grep -Eq "$forbidden" "$members_file"; then
    echo "Public package verification found a private runtime path" >&2
    exit 1
  fi
fi

if command -v sha256sum >/dev/null 2>&1; then
  (cd "$(dirname "$OUTPUT")" && sha256sum "$(basename "$OUTPUT")") >"$OUTPUT.sha256"
else
  digest="$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
  printf '%s  %s\n' "$digest" "$(basename "$OUTPUT")" >"$OUTPUT.sha256"
fi

if [ "$INCLUDE_PRIVATE" = "1" ]; then
  chmod 600 "$OUTPUT" "$OUTPUT.sha256"
  echo "Created private migration archive: $OUTPUT"
  echo "This archive contains credentials and private runtime state."
else
  chmod 644 "$OUTPUT" "$OUTPUT.sha256"
  echo "Created public-safe archive: $OUTPUT"
fi
echo "Checksum: $OUTPUT.sha256"
