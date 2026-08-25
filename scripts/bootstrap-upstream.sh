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
elif [ -d "$UPSTREAM_DIR" ] && [ -n "$(find "$UPSTREAM_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  echo "Recovering existing vendor directory without Git metadata"
  temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/tg-ytdlp-upstream.XXXXXX")"
  trap 'rm -rf "$temp_dir"' EXIT
  git clone --depth 1 "$UPSTREAM_REPO" "$temp_dir/repo"
  rsync -a "$temp_dir/repo/" "$UPSTREAM_DIR/"
  rm -rf "$temp_dir"
  trap - EXIT
else
  git clone --depth 1 "$UPSTREAM_REPO" "$UPSTREAM_DIR"
fi

echo "Upstream ready at $UPSTREAM_DIR"
