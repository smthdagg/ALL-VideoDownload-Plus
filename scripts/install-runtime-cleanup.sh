#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/video-download-bot/vendor/tg-ytdlp-bot}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install -m 0755 "$SCRIPT_DIR/runtime-cleanup.sh" /usr/local/bin/video-download-runtime-cleanup

cat >/etc/systemd/system/video-download-runtime-cleanup.service <<EOF
[Unit]
Description=Clean stale ALL VideoDownload Plus runtime media
After=docker.service

[Service]
Type=oneshot
EnvironmentFile=-$SCRIPT_DIR/../.env
Environment=APP_DIR=$APP_DIR
ExecStart=/usr/local/bin/video-download-runtime-cleanup
EOF

cat >/etc/systemd/system/video-download-runtime-cleanup.timer <<'EOF'
[Unit]
Description=Run ALL VideoDownload Plus runtime cleanup every 30 minutes

[Timer]
OnBootSec=10min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now video-download-runtime-cleanup.timer
systemctl start video-download-runtime-cleanup.service
systemctl list-timers --all video-download-runtime-cleanup.timer
