# ALL VideoDownload Plus: Agent Handoff

Read this file before changing, testing, packaging, or deploying the project.

## Project Purpose

This repository is the reproducible wrapper and patch layer for ALL VideoDownload Plus, built around
`upekshaip/tg-ytdlp-bot`. It adds private access control, Chinese/English UI,
Douyin and WeChat Channels resolvers, TikTok reliability and Telegram-safe
formats, X multi-video handling, an authenticated admin dashboard, operational
timers, and migration tooling.

## Source Of Truth

- Tracked custom code lives in `scripts/apply-private-hardening.py` and
  `scripts/templates/`.
- `vendor/tg-ytdlp-bot/` is generated and ignored by the root repository.
- Do not make a fix only inside `vendor/`; encode it in the patch script or a
  tracked template, regenerate the vendor tree, and add a contract test.
- Private production values belong only in ignored runtime files. Never copy
  them into documentation, tests, commits, issues, or chat output.

## Current Runtime Baseline

- Public project name: `ALL VideoDownload Plus`.
- Python 3.12 Docker base.
- Stable `yt-dlp 2026.08.19` with `curl-cffi`.
- `bgutil-ytdlp-pot-provider 1.3.2` service and plugin.
- Caddy dashboard proxy and optional
  `Evil0ctal/Douyin_TikTok_Download_API` sidecar.
- No global prerelease dependency installation and no MoviePy 1.x dependency.

## Required Workflow

1. Inspect the root Git status and preserve unrelated user changes.
2. Add or update a test before behavior changes.
3. Change tracked templates or `scripts/apply-private-hardening.py`.
4. Run `python3 scripts/apply-private-hardening.py` to regenerate vendor files.
5. Run `python3 -m unittest discover -s tests` and Python syntax checks.
6. Validate `docker compose config` and build the app image for runtime changes.
7. Review `git diff --check`, the full diff, and secret exposure before commit.
8. Deploy only after backing up the current VPS files and tagging a rollback
   image. Verify Telegram startup, dashboard health, and a real platform URL.

## Deployment Layout

- Standard project path: `/opt/video-download-bot`.
- Generated app path: `/opt/video-download-bot/vendor/tg-ytdlp-bot`.
- The app dashboard binds to `127.0.0.1:5555`.
- A public dashboard may use Caddy on HTTPS port 8443 when host port 443 is
  occupied. The hostname and SSH connection details are deployment-private and
  are intentionally not committed.
- Never run the same Telegram Bot session locally and on the VPS concurrently.

## Verification

```bash
python3 scripts/apply-private-hardening.py
python3 -m unittest discover -s tests
python3 -m py_compile scripts/apply-private-hardening.py scripts/templates/*.py
cd vendor/tg-ytdlp-bot
docker compose config -q
docker compose build app
docker compose run --rm app pip check
```

Platform regression URLs and expected behavior are documented in
`docs/testing/platform-regressions.tdd.md`. TikTok challenge failures are
transient on some VPS networks; the tracked retry patch must remain bounded and
must only retry known challenge responses.

## Migration And Recovery

- Public package: `scripts/package-for-vps.sh`.
- Consistent private VPS backup: `scripts/prepare-vps-migration.sh`.
- Activate an extracted private package on a new VPS:
  `scripts/restore-vps-migration.sh`.
- Install watchdog and cleanup timers: `scripts/install-vps-operations.sh`.
- Private archives contain credentials, cookies, Telegram session state, user
  authorization, and preferences. They must remain mode 600 and must never be
  uploaded to GitHub.
- Stop the old VPS `app` service before activating the Bot on a new VPS.

## Private Files

At minimum, treat these as secrets or private state:

- `deploy/config.local.py`
- `deploy/cookies/*.txt`
- `vendor/tg-ytdlp-bot/.env`
- `vendor/tg-ytdlp-bot/magic.session*`
- `vendor/tg-ytdlp-bot/CONFIG/config.py`
- `vendor/tg-ytdlp-bot/CONFIG/private_users.json`
- `vendor/tg-ytdlp-bot/users/`
- generated private migration archives and SSH keys

See `docs/DEPLOYMENT.md`, `docs/ARCHITECTURE.md`, and `docs/SECURITY.md` for the
operational, architectural, and security contracts.
