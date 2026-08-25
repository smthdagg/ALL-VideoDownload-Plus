#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/video-download-bot/vendor/tg-ytdlp-bot}"
USERS_DIR="${USERS_DIR:-${APP_DIR}/users}"
LOG_FILE="${LOG_FILE:-/var/log/video-download-cleanup.log}"
MIN_AGE_MINUTES="${MIN_AGE_MINUTES:-120}"
RETENTION_DAYS="${RETENTION_DAYS:-2}"
DISK_HIGH_PERCENT="${DISK_HIGH_PERCENT:-80}"
DISK_TARGET_PERCENT="${DISK_TARGET_PERCENT:-70}"

log() {
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S%z')" "$*" | tee -a "$LOG_FILE"
}

if [[ ! -d "$USERS_DIR" ]]; then
  log "users directory does not exist: $USERS_DIR"
  exit 0
fi

media_expr=(
  -name '*.part' -o -name '*.ytdl' -o -name '*.temp' -o -name '*.tmp' -o
  -name '*.mp3' -o -name '*.mp4' -o -name '*.mkv' -o -name '*.avi' -o
  -name '*.mov' -o -name '*.wmv' -o -name '*.flv' -o -name '*.webm' -o
  -name '*.m4a' -o -name '*.aac' -o -name '*.ogg' -o -name '*.wav' -o
  -name '*.jpg' -o -name '*.jpeg' -o -name '*.png'
)

# Never touch per-user settings, cookies, logs, caches, or files still being written.
find "$USERS_DIR" -type f -mmin "+$MIN_AGE_MINUTES" \( "${media_expr[@]}" \) -print0 \
  | xargs -0r rm -f --

find "$USERS_DIR" -type f -mtime "+$RETENTION_DAYS" \( -name '*.jsonl' -o -name '*.srt' -o -name '*.vtt' -o -name '*.ass' -o -name '*.ssa' \) -print0 \
  | xargs -0r rm -f --

used_percent="$(df -P "$APP_DIR" | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
if [[ -z "$used_percent" || "$used_percent" -lt "$DISK_HIGH_PERCENT" ]]; then
  log "completed; disk=${used_percent:-unknown}%"
  exit 0
fi

log "disk=${used_percent}% exceeds ${DISK_HIGH_PERCENT}%; removing oldest media files"
while [[ "$used_percent" -gt "$DISK_TARGET_PERCENT" ]]; do
  candidate="$(find "$USERS_DIR" -type f -mmin "+$MIN_AGE_MINUTES" \( "${media_expr[@]}" \) -printf '%T@ %p\n' 2>/dev/null | sort -n | head -n 1 | cut -d' ' -f2- || true)"
  [[ -n "$candidate" ]] || break
  rm -f -- "$candidate" || true
  used_percent="$(df -P "$APP_DIR" | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
done

log "completed; disk=${used_percent:-unknown}%"
