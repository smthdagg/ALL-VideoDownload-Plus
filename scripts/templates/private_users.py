import json
import os
import threading
import time
from pathlib import Path


DEFAULT_PRIVATE_USERS_FILE = Path("CONFIG/private_users.json")


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


class PrivateUserStore:
    def __init__(self, path=DEFAULT_PRIVATE_USERS_FILE):
        self.path = Path(path)
        self._lock = threading.RLock()

    def _read(self):
        if not self.path.exists():
            return {"users": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"users": {}}
        users = payload.get("users") if isinstance(payload, dict) else None
        return {"users": users if isinstance(users, dict) else {}}

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
            if key in payload["users"]:
                return False
            payload["users"][key] = {
                "added_at": int(time.time()),
                "added_by": added_by,
            }
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
