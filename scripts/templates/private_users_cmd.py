from datetime import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CONFIG.config import Config
from HELPERS.app_instance import get_app
from HELPERS.decorators import background_handler
from HELPERS.private_users import get_private_user_store, normalize_user_id
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
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("添加用户", callback_data="private_users|add_help"),
            InlineKeyboardButton("移除用户", callback_data="private_users|remove_help"),
        ],
        [InlineKeyboardButton("查看已授权用户", callback_data="private_users|list")],
        [InlineKeyboardButton("关闭", callback_data="private_users|close")],
    ])


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
    lines.extend([
        "",
        "添加：/add_user 用户ID，或回复/转发对方消息发送 /add_user",
        "移除：/remove_user 用户ID",
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
    added = get_private_user_store().add(target_id, added_by=message.chat.id)
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


@app.on_callback_query(filters.regex(r"^private_users\|"))
def private_users_callback(app, callback_query):
    user_id = callback_query.from_user.id
    if not _is_admin(user_id):
        callback_query.answer("只有管理员可以管理用户。", show_alert=True)
        return

    action = callback_query.data.split("|", 1)[1]
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
