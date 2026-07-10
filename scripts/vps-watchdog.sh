#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/video-download-bot/vendor/tg-ytdlp-bot}"
APP_SERVICE="${APP_SERVICE:-app}"
LOG_FILE="${LOG_FILE:-/var/log/video-download-watchdog.log}"
TAIL_LINES="${TAIL_LINES:-260}"
STARTUP_GRACE_SECONDS="${STARTUP_GRACE_SECONDS:-90}"
STATE_DIR="${STATE_DIR:-/var/lib/video-download-watchdog}"
MISS_THRESHOLD="${MISS_THRESHOLD:-3}"

log() {
  local message="$1"
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S%z')" "$message" | tee -a "$LOG_FILE"
}

restart_app() {
  local reason="$1"
  log "restart ${APP_SERVICE}: ${reason}"
  rm -f "${STATE_DIR}/session_miss_count" 2>/dev/null || true
  docker compose -f "${APP_DIR}/docker-compose.yml" --project-directory "$APP_DIR" restart "$APP_SERVICE" >>"$LOG_FILE" 2>&1
}

ensure_time_sync() {
  if command -v timedatectl >/dev/null 2>&1; then
    timedatectl set-ntp true >>"$LOG_FILE" 2>&1 || true
  fi

  if systemctl list-unit-files systemd-timesyncd.service >/dev/null 2>&1; then
    systemctl enable --now systemd-timesyncd >>"$LOG_FILE" 2>&1 || true
  fi
}

if [[ ! -d "$APP_DIR" ]]; then
  log "missing app dir: ${APP_DIR}"
  exit 1
fi

mkdir -p "$STATE_DIR"
ensure_time_sync

if ! systemctl is-active --quiet docker; then
  log "docker inactive, starting docker"
  systemctl start docker >>"$LOG_FILE" 2>&1 || true
fi

container_id="$(docker compose -f "${APP_DIR}/docker-compose.yml" --project-directory "$APP_DIR" ps -q "$APP_SERVICE" 2>>"$LOG_FILE" || true)"

if [[ -z "$container_id" ]]; then
  log "container missing, starting compose stack"
  docker compose -f "${APP_DIR}/docker-compose.yml" --project-directory "$APP_DIR" up -d >>"$LOG_FILE" 2>&1
  exit 0
fi

running="$(docker inspect -f '{{.State.Running}}' "$container_id" 2>>"$LOG_FILE" || printf 'false')"
if [[ "$running" != "true" ]]; then
  restart_app "container is not running"
  exit 0
fi

started_at="$(docker inspect -f '{{.State.StartedAt}}' "$container_id" 2>>"$LOG_FILE" || true)"
started_epoch="$(date -d "$started_at" +%s 2>/dev/null || printf '0')"
now_epoch="$(date +%s)"
container_age=$((now_epoch - started_epoch))

if (( started_epoch > 0 && container_age < STARTUP_GRACE_SECONDS )); then
  log "warming up age=${container_age}s"
  exit 0
fi

recent_logs="$(docker logs --since "$started_at" --tail "$TAIL_LINES" "$container_id" 2>&1 || true)"

if grep -Eqi 'BadMsgNotification|msg_id is too high|client time has to be synchronized' <<<"$recent_logs"; then
  ensure_time_sync
  restart_app "telegram client time drift detected"
  exit 0
fi

if grep -Eqi 'Traceback|pyrogram\.errors|ConnectionError|AuthKeyUnregistered|FloodWait' <<<"$recent_logs"; then
  restart_app "recent telegram/python error detected"
  exit 0
fi

if grep -Eq 'Session started|Started [0-9]+ HandlerTasks' <<<"$recent_logs"; then
  rm -f "${STATE_DIR}/session_miss_count" 2>/dev/null || true
  log "ok"
  exit 0
fi

miss_count="$(cat "${STATE_DIR}/session_miss_count" 2>/dev/null || printf '0')"
miss_count=$((miss_count + 1))
printf '%s\n' "$miss_count" >"${STATE_DIR}/session_miss_count"

if (( miss_count >= MISS_THRESHOLD )); then
  restart_app "telegram session not confirmed after ${miss_count} checks"
  exit 0
fi

log "session pending miss=${miss_count}/${MISS_THRESHOLD}"
