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

