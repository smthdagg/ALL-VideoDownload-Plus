from datetime import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CONFIG.config import Config
from HELPERS.app_instance import get_app
from HELPERS.decorators import background_handler
from HELPERS.private_users import (
    collect_allowed_user_ids,
    get_private_user_store,
    normalize_user_id,
)
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


def _request_label(user_id, metadata):
    name = " ".join(
        value for value in (metadata.get("first_name"), metadata.get("last_name")) if value
    ).strip() or "未提供姓名"
    username = f"@{metadata['username']}" if metadata.get("username") else "无用户名"
    return f"{name}（{username}，ID: {user_id}）"


def _approval_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("批准", callback_data=f"private_users|approve|{user_id}"),
            InlineKeyboardButton("拒绝", callback_data=f"private_users|reject|{user_id}"),
        ],
        [InlineKeyboardButton("永久拉黑", callback_data=f"private_users|blacklist|{user_id}")],
    ])


def _notify_admins(app, user_id, metadata):
    text = (
        "收到新的 Bot 使用申请\n\n"
        f"{_request_label(user_id, metadata)}\n\n"
        "批准后用户立即获得权限，无需重启。"
    )
    for admin_id in Config.ADMIN:
        safe_send_message(int(admin_id), text, reply_markup=_approval_keyboard(user_id))


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


def _menu_keyboard():
    rows = [
        [
            InlineKeyboardButton("添加用户", callback_data="private_users|add_help"),
            InlineKeyboardButton("移除用户", callback_data="private_users|remove_help"),
        ],
        [InlineKeyboardButton("查看已授权用户", callback_data="private_users|list")],
    ]
    for user_id in sorted(get_private_user_store().list_pending_requests())[:20]:
        rows.append([
            InlineKeyboardButton(f"批准 {user_id}", callback_data=f"private_users|approve|{user_id}"),
            InlineKeyboardButton("拒绝", callback_data=f"private_users|reject|{user_id}"),
        ])
        rows.append([
            InlineKeyboardButton("永久拉黑", callback_data=f"private_users|blacklist|{user_id}")
        ])
    rows.append([InlineKeyboardButton("关闭", callback_data="private_users|close")])
    return InlineKeyboardMarkup(rows)


def _list_text():
    store = get_private_user_store()
    dynamic_entries = store.list_entries()
    admin_ids = sorted({int(value) for value in Config.ADMIN})
    configured_ids = sorted(_configured_user_ids())

    lines = ["用户管理", "", f"管理员：{len(admin_ids)} 人"]
    lines.extend(f"- {user_id}" for user_id in admin_ids)
    lines.extend(["", f"配置文件授权：{len(configured_ids)} 人"])
    lines.extend(f"- {user_id}" for user_id in configured_ids)
    lines.extend(["", f"Bot 菜单动态授权：{len(dynamic_entries)} 人"])
    for user_id in sorted(dynamic_entries):
        metadata = dynamic_entries[user_id]
        added_at = metadata.get("added_at")
        try:
            date_text = datetime.fromtimestamp(int(added_at)).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError, OSError):
            date_text = "未知"
        lines.append(f"- {user_id}（添加于 {date_text}）")
    blacklisted = store.list_blacklisted()
    lines.extend(["", f"永久黑名单：{len(blacklisted)} 人"])
    lines.extend(f"- {user_id}" for user_id in sorted(blacklisted))
    lines.extend([
        "",
        f"待审批申请：{len(store.list_pending_requests())} 人",
        "",
        "添加：/add_user 用户ID，或回复/转发对方消息发送 /add_user",
        "移除：/remove_user 用户ID",
        "拉黑：/blacklist_user 用户ID",
        "解除：/unblacklist_user 用户ID",
        "日志：/log 用户ID",
    ])
    return "\n".join(lines)


def _deny(message_or_query):
    query_message = getattr(message_or_query, "message", None)
    chat_id = (
        getattr(getattr(query_message, "chat", None), "id", None)
        or getattr(getattr(message_or_query, "chat", None), "id", None)
    )
    if chat_id:
        safe_send_message(chat_id, "只有管理员可以管理用户。")


@app.on_message(filters.command("users") & filters.private)
@background_handler(label="private_users_menu")
def private_users_menu(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    safe_send_message(message.chat.id, _list_text(), reply_markup=_menu_keyboard(), message=message)


@app.on_message(filters.command("list_users") & filters.private)
@background_handler(label="list_private_users")
def list_private_users(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    safe_send_message(message.chat.id, _list_text(), reply_markup=_menu_keyboard(), message=message)


@app.on_message(filters.command("add_user") & filters.private)
@background_handler(label="add_private_user")
def add_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(
            message.chat.id,
            "用法：/add_user 用户ID，或回复/转发对方消息发送 /add_user。",
            message=message,
        )
        return

    if target_id in {int(value) for value in Config.ADMIN} or target_id in _configured_user_ids():
        safe_send_message(message.chat.id, f"用户 {target_id} 已经拥有使用权限。", message=message)
        return
    store = get_private_user_store()
    if store.is_blacklisted(target_id):
        safe_send_message(
            message.chat.id,
            f"用户 {target_id} 在永久黑名单中，请先使用 /unblacklist_user {target_id}。",
            message=message,
        )
        return
    added = store.add(target_id, added_by=message.chat.id)
    result = "已添加" if added else "已经在动态白名单中"
    safe_send_message(message.chat.id, f"用户 {target_id} {result}，无需重启。", message=message)


@app.on_message(filters.command("remove_user") & filters.private)
@background_handler(label="remove_private_user")
def remove_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, "用法：/remove_user 用户ID。", message=message)
        return

    if target_id in {int(value) for value in Config.ADMIN}:
        safe_send_message(message.chat.id, "不能移除管理员。", message=message)
        return
    if target_id in _configured_user_ids():
        safe_send_message(
            message.chat.id,
            f"用户 {target_id} 来自 PRIVATE_ALLOWED_USERS，请从配置文件移除并重启。",
            message=message,
        )
        return
    removed = get_private_user_store().remove(target_id)
    result = "已移除" if removed else "不在动态白名单中"
    safe_send_message(message.chat.id, f"用户 {target_id} {result}。", message=message)


@app.on_message(filters.command("blacklist_user") & filters.private)
@background_handler(label="blacklist_private_user")
def blacklist_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, "用法：/blacklist_user 用户ID。", message=message)
        return
    if target_id in {int(value) for value in Config.ADMIN}:
        safe_send_message(message.chat.id, "不能拉黑管理员。", message=message)
        return
    blocked = get_private_user_store().blacklist(
        target_id,
        reviewed_by=message.chat.id,
        reason="manual",
    )
    result = "已永久拉黑，原有权限和申请已撤销" if blocked else "已经在永久黑名单中"
    safe_send_message(message.chat.id, f"用户 {target_id} {result}。", message=message)


@app.on_message(filters.command("unblacklist_user") & filters.private)
@background_handler(label="unblacklist_private_user")
def unblacklist_private_user(app, message):
    if not _is_admin(message.chat.id):
        _deny(message)
        return
    try:
        target_id = _target_user_id(message)
    except ValueError:
        safe_send_message(message.chat.id, "用法：/unblacklist_user 用户ID。", message=message)
        return
    removed = get_private_user_store().unblacklist(target_id)
    result = "已解除永久拉黑，可以重新申请" if removed else "不在永久黑名单中"
    safe_send_message(message.chat.id, f"用户 {target_id} {result}。", message=message)


@app.on_callback_query(filters.regex(r"^private_users\|"))
def private_users_callback(app, callback_query):
    user_id = callback_query.from_user.id
    parts = callback_query.data.split("|")
    action = parts[1] if len(parts) > 1 else ""

    if action == "request":
        if user_id in _all_allowed_user_ids():
            callback_query.answer("你已经拥有使用权限。", show_alert=True)
            return
        profile = _profile(callback_query.from_user)
        state = get_private_user_store().submit_request(user_id, profile)
        if state == "created":
            _notify_admins(app, user_id, profile)
            callback_query.answer("申请已提交，请等待管理员审批。", show_alert=True)
        elif state == "pending":
            callback_query.answer("申请正在等待管理员审批，请勿重复提交。", show_alert=True)
        elif state == "rejected":
            callback_query.answer("申请刚被拒绝，请稍后再申请或联系管理员。", show_alert=True)
        elif state == "blacklisted":
            callback_query.answer("你的账号已被永久禁止申请。", show_alert=True)
        else:
            callback_query.answer("你已经拥有使用权限。", show_alert=True)
        return

    if not _is_admin(user_id):
        callback_query.answer("只有管理员可以管理用户。", show_alert=True)
        return

    if action in {"approve", "reject", "blacklist"}:
        try:
            target_id = normalize_user_id(parts[2])
        except (IndexError, ValueError):
            callback_query.answer("申请数据无效。", show_alert=True)
            return
        store = get_private_user_store()
        if action == "approve":
            handled = store.approve(target_id, reviewed_by=user_id)
        elif action == "reject":
            handled = store.reject(target_id, reviewed_by=user_id)
        else:
            if target_id in {int(value) for value in Config.ADMIN}:
                callback_query.answer("不能拉黑管理员。", show_alert=True)
                return
            handled = store.blacklist(target_id, reviewed_by=user_id, reason="application_abuse")
        if not handled:
            callback_query.answer("该申请已由其他管理员处理。", show_alert=True)
            return
        if action == "approve":
            user_text = "你的 Bot 使用申请已通过，现在可以直接发送视频链接。"
            admin_text = f"已批准用户 {target_id}，权限立即生效。"
        elif action == "reject":
            user_text = "你的 Bot 使用申请未通过。如有疑问，请联系管理员。"
            admin_text = f"已拒绝用户 {target_id} 的申请。"
        else:
            user_text = "你的账号已被管理员永久禁止使用和申请此 Bot。"
            admin_text = f"已永久拉黑用户 {target_id}，原有权限和申请均已撤销。"
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
        callback_query.edit_message_text(_list_text(), reply_markup=_menu_keyboard())
        callback_query.answer()
        return
    help_text = (
        "发送 /add_user 用户ID，或回复/转发对方消息发送 /add_user。"
        if action == "add_help"
        else "发送 /remove_user 用户ID。配置文件中的固定用户不能在菜单移除。"
    )
    callback_query.answer(help_text, show_alert=True)
