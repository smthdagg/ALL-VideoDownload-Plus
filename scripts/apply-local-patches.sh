#!/usr/bin/env bash
# Apply project-local modifications to the vendored tg-ytdlp-bot clone.
# Run after scripts/bootstrap-upstream.sh. Idempotent.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR="$ROOT_DIR/vendor/tg-ytdlp-bot"
PATCH_DIR="$ROOT_DIR/patches/tg-ytdlp-bot"

if [ ! -d "$VENDOR" ]; then
  echo "vendor clone missing; run scripts/bootstrap-upstream.sh first" >&2
  exit 1
fi

# 1) tracked-file patches
for patch in "$PATCH_DIR"/*.patch; do
  [ -e "$patch" ] || continue
  git -C "$VENDOR" apply --ignore-whitespace "$patch" 2>/dev/null \
    || echo "patch already applied or skipped: $(basename "$patch")"
done

# 2) new files (survive rsync-based recovery: no --delete in bootstrap)
rsync -a "$PATCH_DIR/yt_dlp_plugins/" "$VENDOR/yt_dlp_plugins/"

echo "local patches applied"
