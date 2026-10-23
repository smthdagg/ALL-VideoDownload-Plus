import json
import os
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


DEFAULT_PRIVATE_USERS_FILE = Path("CONFIG/private_users.json")
REQUEST_RETRY_SECONDS = 24 * 60 * 60


def build_dashboard_admin_url(value):
    raw_url = str(value or "").strip()
    if not raw_url:
        return None
    try:
        parsed = urlsplit(raw_url)
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        return None
    path = parsed.path.rstrip("/") + "/admin/users"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def normalize_user_id(value):
    if isinstance(value, bool):
        raise ValueError("Telegram user ID must be a positive integer")
    try:
        user_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Telegram user ID must be a positive integer") from exc
    if user_id <= 0:
        raise ValueError("Telegram user ID must be a positive integer")
    return user_id


def collect_allowed_user_ids(admin_ids, static_user_ids, dynamic_user_ids):
    allowed = set()
    for value in list(admin_ids or []) + list(static_user_ids or []) + list(dynamic_user_ids or []):
        try:
            allowed.add(normalize_user_id(value))
        except ValueError:
            continue
    return allowed


def build_access_request_markup(user_id=None):
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from HELPERS.private_i18n import text

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text("apply_access", user_id=user_id, language="en" if user_id is None else None), callback_data="private_users|request")],
        [
            InlineKeyboardButton("中文", callback_data="lang_select_zh"),
            InlineKeyboardButton("English", callback_data="lang_select_en"),
        ],
    ])


class PrivateUserStore:
    def __init__(self, path=DEFAULT_PRIVATE_USERS_FILE):
        self.path = Path(path)
        self._lock = threading.RLock()

    def _read(self):
        if not self.path.exists():
            return {"users": {}, "requests": {}, "blacklist": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"users": {}, "requests": {}, "blacklist": {}}
        users = payload.get("users") if isinstance(payload, dict) else None
        requests = payload.get("requests") if isinstance(payload, dict) else None
        blacklist = payload.get("blacklist") if isinstance(payload, dict) else None
        return {
            "users": users if isinstance(users, dict) else {},
            "requests": requests if isinstance(requests, dict) else {},
            "blacklist": blacklist if isinstance(blacklist, dict) else {},
        }

    def _write(self, payload):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, self.path)

    def list_entries(self):
        with self._lock:
            users = self._read()["users"]
            entries = {}
            for raw_id, metadata in users.items():
                try:
                    user_id = normalize_user_id(raw_id)
                except ValueError:
                    continue
                entries[user_id] = metadata if isinstance(metadata, dict) else {}
            return entries

    def list_ids(self):
        return set(self.list_entries())

    def add(self, user_id, added_by):
        user_id = normalize_user_id(user_id)
        added_by = normalize_user_id(added_by)
        with self._lock:
            payload = self._read()
            key = str(user_id)
            if key in payload["blacklist"]:
                return False
            if key in payload["users"]:
                if payload["requests"].pop(key, None) is not None:
                    self._write(payload)
                return False
            payload["users"][key] = {
                "added_at": int(time.time()),
                "added_by": added_by,
            }
            payload["requests"].pop(key, None)
            self._write(payload)
            return True

    def remove(self, user_id):
        user_id = normalize_user_id(user_id)
        with self._lock:
            payload = self._read()
            if payload["users"].pop(str(user_id), None) is None:
                return False
            self._write(payload)
            return True

    def submit_request(self, user_id, profile):
        user_id = normalize_user_id(user_id)
        now = int(time.time())
        with self._lock:
            payload = self._read()
            key = str(user_id)
            if key in payload["blacklist"]:
                return "blacklisted"
            if key in payload["users"]:
                return "allowed"

            existing = payload["requests"].get(key, {})
            if existing.get("status") == "pending":
                return "pending"
            if existing.get("status") == "rejected":
                try:
                    reviewed_at = int(existing.get("reviewed_at", 0))
                except (TypeError, ValueError):
                    reviewed_at = now
                if now - reviewed_at < REQUEST_RETRY_SECONDS:
                    return "rejected"

            clean_profile = {}
            for field in ("first_name", "last_name", "username"):
                value = (profile or {}).get(field)
                if value:
                    clean_profile[field] = str(value).replace("\n", " ").strip()[:128]
            payload["requests"][key] = {
                **clean_profile,
                "status": "pending",
                "submitted_at": now,
            }
            self._write(payload)
            return "created"

    def list_pending_requests(self):
        with self._lock:
            requests = self._read()["requests"]
            pending = {}
            for raw_id, metadata in requests.items():
                if not isinstance(metadata, dict) or metadata.get("status") != "pending":
                    continue
                try:
                    pending[normalize_user_id(raw_id)] = dict(metadata)
                except ValueError:
                    continue
            return pending

    def approve(self, user_id, reviewed_by):
        user_id = normalize_user_id(user_id)
        reviewed_by = normalize_user_id(reviewed_by)
        with self._lock:
            payload = self._read()
            key = str(user_id)
            if key in payload["blacklist"]:
                return False
            request = payload["requests"].get(key)
            if not isinstance(request, dict) or request.get("status") != "pending":
                return False
            payload["users"][key] = {
                "added_at": int(time.time()),
                "added_by": reviewed_by,
                "source": "approved_request",
            }
            payload["requests"].pop(key, None)
            self._write(payload)
            return True

    def list_blacklisted(self):
        with self._lock:
            blacklist = self._read()["blacklist"]
            entries = {}
            for raw_id, metadata in blacklist.items():
                try:
                    user_id = normalize_user_id(raw_id)
                except ValueError:
                    continue
                entries[user_id] = metadata if isinstance(metadata, dict) else {}
            return entries

    def list_blacklisted_ids(self):
        return set(self.list_blacklisted())

    def is_blacklisted(self, user_id):
        try:
            user_id = normalize_user_id(user_id)
        except ValueError:
            return False
        return user_id in self.list_blacklisted_ids()

    def blacklist(self, user_id, reviewed_by, reason=None):
        user_id = normalize_user_id(user_id)
        reviewed_by = normalize_user_id(reviewed_by)
        with self._lock:
            payload = self._read()
            key = str(user_id)
            if key in payload["blacklist"]:
                return False
            metadata = {
                "blocked_at": int(time.time()),
                "blocked_by": reviewed_by,
            }
            if reason:
                metadata["reason"] = str(reason).replace("\n", " ").strip()[:200]
            payload["blacklist"][key] = metadata
            payload["users"].pop(key, None)
            payload["requests"].pop(key, None)
            self._write(payload)
            return True

    def unblacklist(self, user_id):
        user_id = normalize_user_id(user_id)
        with self._lock:
            payload = self._read()
            if payload["blacklist"].pop(str(user_id), None) is None:
                return False
            self._write(payload)
            return True

    def reject(self, user_id, reviewed_by):
        user_id = normalize_user_id(user_id)
        reviewed_by = normalize_user_id(reviewed_by)
        with self._lock:
            payload = self._read()
            key = str(user_id)
            request = payload["requests"].get(key)
            if not isinstance(request, dict) or request.get("status") != "pending":
                return False
            payload["requests"][key] = {
                **request,
                "status": "rejected",
                "reviewed_at": int(time.time()),
                "reviewed_by": reviewed_by,
            }
            self._write(payload)
            return True


_store = None
_store_lock = threading.Lock()


def get_private_user_store():
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                configured_path = os.getenv("PRIVATE_USERS_FILE", str(DEFAULT_PRIVATE_USERS_FILE))
                _store = PrivateUserStore(configured_path)
    return _store
