"""User-facing disk pressure notices for the Telegram Bot."""

import os
import shutil
import threading
import time
from pathlib import Path


DEFAULT_WARNING_PERCENT = 75
DEFAULT_HIGH_PERCENT = 80
NOTICE_INTERVAL_SECONDS = 6 * 60 * 60
_notice_lock = threading.Lock()
_last_notice_by_user = {}


def _percent(value, default):
    try:
        return float(os.getenv(value, str(default)))
    except (TypeError, ValueError):
        return float(default)


def format_bytes(value):
    value = max(0, float(value or 0))
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    if index == 0:
        return f"{int(value)} B"
    return f"{value:.1f} {units[index]}"


def classify_disk_usage(used_percent, warning_percent, high_percent):
    used_percent = float(used_percent)
    if used_percent >= float(high_percent):
        return "high"
    if used_percent >= float(warning_percent):
        return "warning"
    return "ok"


def get_disk_status(path=None):
    target = Path(path or os.getenv("DISK_USAGE_PATH", "."))
    usage = shutil.disk_usage(target)
    used_percent = (usage.used / usage.total * 100) if usage.total else 0
    warning_percent = _percent("DISK_WARNING_PERCENT", DEFAULT_WARNING_PERCENT)
    high_percent = _percent("DISK_HIGH_PERCENT", DEFAULT_HIGH_PERCENT)
    return {
        "used_percent": used_percent,
        "free_bytes": usage.free,
        "total_bytes": usage.total,
        "warning_percent": warning_percent,
        "high_percent": high_percent,
        "state": classify_disk_usage(used_percent, warning_percent, high_percent),
    }


def maybe_send_disk_warning(message):
    """Send at most one disk warning per user during the configured interval."""
    if not getattr(getattr(message, "chat", None), "id", None):
        return False
    try:
        chat_type = str(getattr(getattr(message, "chat", None), "type", "")).lower()
        if not chat_type.endswith("private"):
            return False
        user_id = int(message.chat.id)
        status = get_disk_status()
    except (AttributeError, TypeError, ValueError, OSError):
        return False
    if status["state"] == "ok":
        return False
    now = time.time()
    with _notice_lock:
        if now - _last_notice_by_user.get(user_id, 0) < NOTICE_INTERVAL_SECONDS:
            return False
        _last_notice_by_user[user_id] = now
    from HELPERS.private_i18n import text
    from HELPERS.safe_messeger import safe_send_message

    safe_send_message(
        user_id,
        text(
            "disk_warning",
            user_id=user_id,
            used_percent=f"{status['used_percent']:.1f}",
            warning_percent=f"{status['warning_percent']:.0f}",
            high_percent=f"{status['high_percent']:.0f}",
            free_space=format_bytes(status["free_bytes"]),
        ),
        message=message,
    )
    return True
