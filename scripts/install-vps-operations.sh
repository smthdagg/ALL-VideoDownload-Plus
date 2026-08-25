#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/video-download-bot}"
APP_DIR="${APP_DIR:-$PROJECT_DIR/vendor/tg-ytdlp-bot}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root on the VPS" >&2
  exit 1
fi
if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
  echo "Missing initialized application at $APP_DIR" >&2
  exit 1
fi

APP_DIR="$APP_DIR" "$PROJECT_DIR/scripts/install-runtime-cleanup.sh"
install -m 0755 "$PROJECT_DIR/scripts/vps-watchdog.sh" /usr/local/bin/video-download-watchdog

cat >/etc/systemd/system/video-download-watchdog.service <<EOF
[Unit]
Description=Video Download Bot System watchdog
Wants=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
Environment=APP_DIR=$APP_DIR
Environment=APP_SERVICE=app
Environment=LOG_FILE=/var/log/video-download-watchdog.log
ExecStart=/usr/local/bin/video-download-watchdog
EOF

cat >/etc/systemd/system/video-download-watchdog.timer <<'EOF'
[Unit]
Description=Run Video Download Bot System watchdog every minute

[Timer]
OnBootSec=2min
OnUnitActiveSec=1min
AccuracySec=10s
Persistent=true
Unit=video-download-watchdog.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now video-download-watchdog.timer
systemctl start video-download-watchdog.service
systemctl is-active video-download-watchdog.timer video-download-runtime-cleanup.timer
