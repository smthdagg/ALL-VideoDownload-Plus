from datetime import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CONFIG.config import Config
from HELPERS.app_instance import get_app
from HELPERS.decorators import background_handler
from HELPERS.private_users import (
    build_dashboard_admin_url,
    collect_allowed_user_ids,
    get_private_user_store,
    normalize_user_id,
)
from HELPERS.private_i18n import text, user_language
from HELPERS.safe_messeger import safe_send_message


app = get_app()


def _is_admin(user_id):
    try:
        return int(user_id) in {int(value) for value in Config.ADMIN}
    except (TypeError, ValueError):
        return False


def _configured_user_ids():
    result = set()
    for value in getattr(Config, "PRIVATE_ALLOWED_USERS", []):
        try:
            result.add(normalize_user_id(value))
        except ValueError:
            continue
    return result


def _all_allowed_user_ids():
    store = get_private_user_store()
    admin_ids = collect_allowed_user_ids(Config.ADMIN, [], [])
    allowed = collect_allowed_user_ids(
        Config.ADMIN,
        getattr(Config, "PRIVATE_ALLOWED_USERS", []),
        store.list_ids(),
    )
    return (allowed - store.list_blacklisted_ids()) | admin_ids


def _profile(user):
    return {
        "first_name": getattr(user, "first_name", None),
        "last_name": getattr(user, "last_name", None),
        "username": getattr(user, "username", None),
    }


def _request_label(user_id, metadata, viewer_id):
    chinese = user_language(viewer_id) == "zh"
    name = " ".join(
        value for value in (metadata.get("first_name"), metadata.get("last_name")) if value
    ).strip() or ("未提供姓名" if chinese else "Name unavailable")
    username = f"@{metadata['username']}" if metadata.get("username") else ("无用户名" if chinese else "no username")
    return f"{name} ({username}, ID: {user_id})"


def _approval_keyboard(user_id, viewer_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text("approve", user_id=viewer_id), callback_data=f"private_users|approve|{user_id}"),
            InlineKeyboardButton(text("reject", user_id=viewer_id), callback_data=f"private_users|reject|{user_id}"),
        ],
        [InlineKeyboardButton(text("permanent_blacklist", user_id=viewer_id), callback_data=f"private_users|blacklist|{user_id}")],
    ])


def _notify_admins(app, user_id, metadata):
    for admin_id in Config.ADMIN:
        admin_id = int(admin_id)
        safe_send_message(
            admin_id,
            text("request_admin_notice", user_id=admin_id, label=_request_label(user_id, metadata, admin_id)),
            reply_markup=_approval_keyboard(user_id, admin_id),
        )


def _target_user_id(message):
    text = (message.text or message.caption or "").strip()
    parts = text.split(maxsplit=1)
    if len(parts) == 2:
        return normalize_user_id(parts[1].strip())

    reply = getattr(message, "reply_to_message", None)
    if reply:
        forward_origin = getattr(reply, "forward_origin", None)
        candidates = (
            getattr(reply, "forward_from", None),
            getattr(forward_origin, "sender_user", None),
            getattr(reply, "from_user", None),
        )
        for candidate in candidates:
            if candidate and getattr(candidate, "id", None):
                return normalize_user_id(candidate.id)
    raise ValueError("缺少 Telegram 用户 ID")


def _menu_keyboard(viewer_id):
    rows = [
        [
            InlineKeyboardButton(text("add_user", user_id=viewer_id), callback_data="private_users|add_help"),
            InlineKeyboardButton(text("remove_user", user_id=viewer_id), callback_data="private_users|remove_help"),
        ],
        [InlineKeyboardButton(text("list_users", user_id=viewer_id), callback_data="private_users|list")],
    ]
    for user_id in sorted(get_private_user_store().list_pending_requests())[:20]:
        rows.append([
            InlineKeyboardButton(f"{text('approve', user_id=viewer_id)} {user_id}", callback_data=f"private_users|approve|{user_id}"),
            InlineKeyboardButton(text("reject", user_id=viewer_id), callback_data=f"private_users|reject|{user_id}"),
        ])
        rows.append([
            InlineKeyboardButton(text("permanent_blacklist", user_id=viewer_id), callback_data=f"private_users|blacklist|{user_id}")
        ])
    dashboard_url = build_dashboard_admin_url(
        getattr(Config, "DASHBOARD_PUBLIC_URL", "")
    )
    if dashboard_url:
        rows.append([InlineKeyboardButton(text("open_web_admin", user_id=viewer_id), url=dashboard_url)])
    rows.append([InlineKeyboardButton(text("close", user_id=viewer_id), callback_data="private_users|close")])
    return InlineKeyboardMarkup(rows)


def _list_text(viewer_id):
    store = get_private_user_store()
    dynamic_entries = store.list_entries()
    admin_ids = sorted({int(value) for value in Config.ADMIN})
    configured_ids = sorted(_configured_user_ids())

    if user_language(viewer_id) == "zh":
        lines = ["用户管理", "", f"管理员：{len(admin_ids)} 人"]
        configured_title = "配置文件授权"
        dynamic_title = "Bot 菜单动态授权"
        blacklist_title = "永久黑名单"
        pending_title = "待审批申请"
        added_label = "添加于"
        help_lines = [
            "添加：/add_user 用户ID，或回复/转发对方消息发送 /add_user",
            "移除：/remove_user 用户ID",
            "拉黑：/blacklist_user 用户ID",
            "解除：/unblacklist_user 用户ID",
            "日志：/log 用户ID",
        ]
    else:
        lines = ["User management", "", f"Administrators: {len(admin_ids)}"]
        configured_title = "Configuration-managed access"
        dynamic_title = "Dynamic Bot access"
        blacklist_title = "Permanent blacklist"
        pending_title = "Pending requests"
        added_label = "added"
        help_lines = [
            "Add: /add_user USER_ID, or reply/forward and send /add_user",
            "Remove: /remove_user USER_ID",
            "Blacklist: /blacklist_user USER_ID",
            "Unblacklist: /unblacklist_user USER_ID",
            "History: /log USER_ID",
        ]
    lines.extend(f"- {user_id}" for user_id in admin_ids)
    lines.extend(["", f"{configured_title}: {len(configured_ids)}"])
    lines.extend(f"- {user_id}" for user_id in configured_ids)
    lines.extend(["", f"{dynamic_title}: {len(dynamic_entries)}"])
    for user_id in sorted(dynamic_entries):
        metadata = dynamic_entries[user_id]
        added_at = metadata.get("added_at")
        try:
            date_text = datetime.fromtimestamp(int(added_at)).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError, OSError):
            date_text = "未知"
        lines.append(f"- {user_id} ({added_label} {date_text})")
    blacklisted = store.list_blacklisted()
    lines.extend(["", f"{blacklist_title}: {len(blacklisted)}"])
    lines.extend(f"- {user_id}" for user_id in sorted(blacklisted))
    lines.extend([
        "",
        f"{pending_title}: {len(store.list_pending_requests())}",
        "",
        *help_lines,
    ])
    return "\n".join(lines)


def _deny(message_or_query):
    query_message = getattr(message_or_query, "message", None)
    chat_id = (
        getattr(getattr(query_message, "chat", None), "id", None)
        or getattr(getattr(message_or_query, "chat", None), "id", None)
    )
    if chat_id:
        safe_send_message(chat_id, text("admin_only", user_id=chat_id))


@app.on_message(filters.command("users") & filters.private)
@background_handler(label="private_users_menu")
def private_users_menu(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    safe_send_message(message.chat.id, _list_text(message.chat.id), reply_markup=_menu_keyboard(message.chat.id), message=message)


@app.on_message(filters.command("list_users") & filters.private)
@background_handler(label="list_private_users")
def list_private_users(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    safe_send_message(message.chat.id, _list_text(message.chat.id), reply_markup=_menu_keyboard(message.chat.id), message=message)


@app.on_message(filters.command("add_user") & filters.private)
@background_handler(label="add_private_user")
def add_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, text("add_user_help", user_id=message.chat.id), message=message)
        return

    if target_id in {int(value) for value in Config.ADMIN} or target_id in _configured_user_ids():
        safe_send_message(message.chat.id, text("user_already_allowed", user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)), message=message)
        return
    store = get_private_user_store()
    if store.is_blacklisted(target_id):
        safe_send_message(
            message.chat.id,
            text("user_in_blacklist", user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)),
            message=message,
        )
        return
    added = store.add(target_id, added_by=message.chat.id)
    key = "user_added" if added else "user_already_dynamic"
    safe_send_message(message.chat.id, text(key, user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)), message=message)


@app.on_message(filters.command("remove_user") & filters.private)
@background_handler(label="remove_private_user")
def remove_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, text("remove_user_help", user_id=message.chat.id), message=message)
        return

    if target_id in {int(value) for value in Config.ADMIN}:
        safe_send_message(message.chat.id, text("cannot_remove_admin", user_id=message.chat.id), message=message)
        return
    if target_id in _configured_user_ids():
        safe_send_message(
            message.chat.id,
            text("static_user_remove", user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)),
            message=message,
        )
        return
    removed = get_private_user_store().remove(target_id)
    key = "user_removed" if removed else "user_not_dynamic"
    safe_send_message(message.chat.id, text(key, user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)), message=message)


@app.on_message(filters.command("blacklist_user") & filters.private)
@background_handler(label="blacklist_private_user")
def blacklist_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, f"/blacklist_user: {text('missing_user_id', user_id=message.chat.id)}", message=message)
        return
    if target_id in {int(value) for value in Config.ADMIN}:
        safe_send_message(message.chat.id, text("cannot_blacklist_admin", user_id=message.chat.id), message=message)
        return
    blocked = get_private_user_store().blacklist(
        target_id,
        reviewed_by=message.chat.id,
        reason="manual",
    )
    key = "user_blacklisted" if blocked else "user_already_blacklisted"
    safe_send_message(message.chat.id, text(key, user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)), message=message)


@app.on_message(filters.command("unblacklist_user") & filters.private)
@background_handler(label="unblacklist_private_user")
def unblacklist_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, f"/unblacklist_user: {text('missing_user_id', user_id=message.chat.id)}", message=message)
        return
    removed = get_private_user_store().unblacklist(target_id)
    key = "user_unblacklisted" if removed else "user_not_blacklisted"
    safe_send_message(message.chat.id, text(key, user_id=message.chat.id, user_id_value=target_id).replace("{user_id}", str(target_id)), message=message)


@app.on_callback_query(filters.regex(r"^private_users\|"))
def private_users_callback(app, callback_query):
    user_id = callback_query.from_user.id
    parts = callback_query.data.split("|")
    action = parts[1] if len(parts) > 1 else ""

    if action == "request":
        if user_id in _all_allowed_user_ids():
            callback_query.answer(text("already_allowed", user_id=user_id), show_alert=True)
            return
        profile = _profile(callback_query.from_user)
        state = get_private_user_store().submit_request(user_id, profile)
        if state == "created":
            _notify_admins(app, user_id, profile)
            callback_query.answer(text("request_created", user_id=user_id), show_alert=True)
        elif state == "pending":
            callback_query.answer(text("request_pending", user_id=user_id), show_alert=True)
        elif state == "rejected":
            callback_query.answer(text("request_rejected", user_id=user_id), show_alert=True)
        elif state == "blacklisted":
            callback_query.answer(text("request_blacklisted", user_id=user_id), show_alert=True)
        else:
            callback_query.answer(text("already_allowed", user_id=user_id), show_alert=True)
        return

    if not _is_admin(user_id):
        callback_query.answer(text("admin_only", user_id=user_id), show_alert=True)
        return

    if action in {"approve", "reject", "blacklist"}:
        try:
            target_id = normalize_user_id(parts[2])
        except (IndexError, ValueError):
            callback_query.answer(text("invalid_request", user_id=user_id), show_alert=True)
            return
        store = get_private_user_store()
        if action == "approve":
            handled = store.approve(target_id, reviewed_by=user_id)
        elif action == "reject":
            handled = store.reject(target_id, reviewed_by=user_id)
        else:
            if target_id in {int(value) for value in Config.ADMIN}:
                callback_query.answer(text("cannot_blacklist_admin", user_id=user_id), show_alert=True)
                return
            handled = store.blacklist(target_id, reviewed_by=user_id, reason="application_abuse")
        if not handled:
            callback_query.answer(text("request_already_handled", user_id=user_id), show_alert=True)
            return
        if action == "approve":
            user_text = text("request_user_approved", user_id=target_id)
            admin_text = text("approved_admin", user_id=user_id, user_id_value=target_id).replace("{user_id}", str(target_id))
        elif action == "reject":
            user_text = text("request_user_rejected", user_id=target_id)
            admin_text = text("rejected_admin", user_id=user_id, user_id_value=target_id).replace("{user_id}", str(target_id))
        else:
            user_text = text("request_user_blocked", user_id=target_id)
            admin_text = text("blacklisted_admin", user_id=user_id, user_id_value=target_id).replace("{user_id}", str(target_id))
        safe_send_message(target_id, user_text)
        try:
            callback_query.edit_message_text(admin_text)
        except Exception:
            pass
        callback_query.answer(admin_text)
        return

    if action == "close":
        callback_query.message.delete()
        callback_query.answer()
        return
    if action == "list":
        callback_query.edit_message_text(_list_text(user_id), reply_markup=_menu_keyboard(user_id))
        callback_query.answer()
        return
    help_text = (
        text("add_user_help", user_id=user_id)
        if action == "add_help"
        else text("remove_user_help", user_id=user_id)
    )
    callback_query.answer(help_text, show_alert=True)
