#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/upekshaip/tg-ytdlp-bot.git}"
UPSTREAM_DIR="${UPSTREAM_DIR:-$ROOT_DIR/vendor/tg-ytdlp-bot}"

mkdir -p "$(dirname "$UPSTREAM_DIR")"

if [ -d "$UPSTREAM_DIR/.git" ]; then
  git -C "$UPSTREAM_DIR" fetch --depth 1 origin main
  git -C "$UPSTREAM_DIR" checkout main
  git -C "$UPSTREAM_DIR" pull --ff-only --depth 1 origin main
else
  git clone --depth 1 "$UPSTREAM_REPO" "$UPSTREAM_DIR"
fi

echo "Upstream ready at $UPSTREAM_DIR"

