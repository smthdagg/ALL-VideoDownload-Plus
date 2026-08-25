# Security

This project is designed for private self-hosting. The safe baseline is:

- bot access restricted to Telegram admins and explicitly allowed users;
- dashboard bound to `127.0.0.1`;
- cookies and Telegram credentials ignored by Git;
- deployment secrets stored only in local runtime files.

## Never Commit

Do not commit:

- Telegram bot tokens;
- Telegram `API_ID` / `API_HASH`;
- Pyrogram session strings or `.session` files;
- dashboard passwords;
- cookies;
- generated VPS packages created with `--include-private`;
- VPS SSH keys or server passwords.

## Dashboard

Keep the dashboard private. On a VPS, use SSH tunneling:

```bash
ssh -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

Do not expose the dashboard port directly to the public internet unless you add
your own reverse proxy authentication, TLS, and firewall rules.

The dashboard has an independent username and password. Telegram administrator
status is not a Web login mechanism. Authenticated browser sessions use
HttpOnly, SameSite=Strict cookies; the Secure flag is enabled when
`DASHBOARD_PUBLIC_URL` is an HTTPS URL. Cross-site state-changing requests are
rejected and wildcard CORS is disabled.

To show a Web administration button in the Bot, terminate TLS at a reverse
proxy and set `DASHBOARD_PUBLIC_URL` to the clean HTTPS base URL. Never put a
password, token, or other secret in that URL. Leave the setting empty for an
SSH-tunnel-only deployment.

## Telegram Access Control

The recommended personal-use config is:

```python
PRIVATE_MODE = True
ADMIN = [123456789]
PRIVATE_ALLOWED_USERS = []
ALLOWED_GROUP = []
```

Add user IDs only when you explicitly trust them.

## Cookie Risk

Cookies can grant access to your logged-in platform sessions. Treat them like
passwords:

- store them only in `deploy/cookies/` or private `.env` files;
- rotate them when a device, browser, or account changes;
- remove them before sharing logs or archives.

## Docker Images And Migration Archives

The generated `.dockerignore` excludes `.env`, Cookie files, Telegram sessions,
dynamic users, per-user directories, and runtime databases from Docker build
layers. Do not remove these exclusions to make a build "easier"; Compose mounts
runtime state from the VPS filesystem after the container starts.

`scripts/package-for-vps.sh` creates a public-safe archive by default. Private
migration mode contains credentials and account state. On a running VPS, use
`scripts/prepare-vps-migration.sh` so the Bot session is stopped consistently
and automatically restarted afterward. Private archives and checksum files are
mode 600 and belong only in a root-owned directory or trusted encrypted storage.

Private migration packages intentionally exclude downloaded media, transient
logs, Caddy TLS storage, SSH keys, caches, and older archives. Inspect archive
member names and verify the SHA-256 checksum before extraction.

## Pre-Publish Checklist

Before pushing:

```bash
python3 -m unittest discover -s tests
python3 -m py_compile scripts/apply-private-hardening.py
git status --ignored -s
```

Search for common secret markers:

```bash
rg -n --hidden --glob '!.git/**' --glob '!vendor/**' \
  '(BOT_TOKEN|API_HASH|API_ID|Cookie:|sessionid|passport_|sid_guard)'
```
