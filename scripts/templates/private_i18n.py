from pathlib import Path


SUPPORTED_LANGUAGES = ("zh", "en")


MESSAGES = {
    "zh": {
        "language_button": "中文 / English",
        "language_title": "请选择界面语言：",
        "language_changed": "界面语言已切换为中文。",
        "private_denied": "这是私人 Bot，你当前还没有使用权限。\n\n点击下方按钮提交申请，管理员批准后即可使用。",
        "private_blacklisted": "你的账号已被管理员永久禁止使用此 Bot。",
        "apply_access": "申请使用权限",
        "request_created": "申请已提交，请等待管理员审批。",
        "request_pending": "申请正在等待管理员审批，请勿重复提交。",
        "request_rejected": "申请刚被拒绝，请稍后再申请或联系管理员。",
        "request_blacklisted": "你的账号已被永久禁止申请。",
        "already_allowed": "你已经拥有使用权限。",
        "admin_only": "只有管理员可以管理用户。",
        "users_title": "用户管理",
        "add_user": "添加用户",
        "remove_user": "移除用户",
        "list_users": "查看已授权用户",
        "open_web_admin": "打开 Web 管理后台",
        "close": "关闭",
        "approve": "批准",
        "reject": "拒绝",
        "permanent_blacklist": "永久拉黑",
        "request_admin_notice": "收到新的 Bot 使用申请\n\n{label}\n\n批准后用户立即获得权限，无需重启。",
        "request_user_approved": "你的 Bot 使用申请已通过，现在可以直接发送视频链接。",
        "request_user_rejected": "你的 Bot 使用申请未通过。如有疑问，请联系管理员。",
        "request_user_blocked": "你的账号已被管理员永久禁止使用和申请此 Bot。",
        "request_already_handled": "该申请已由其他管理员处理。",
        "invalid_request": "申请数据无效。",
        "cannot_blacklist_admin": "不能拉黑管理员。",
        "approved_admin": "已批准用户 {user_id}，权限立即生效。",
        "rejected_admin": "已拒绝用户 {user_id} 的申请。",
        "blacklisted_admin": "已永久拉黑用户 {user_id}，原有权限和申请均已撤销。",
        "add_user_help": "发送 /add_user 用户ID，或回复/转发对方消息发送 /add_user。",
        "remove_user_help": "发送 /remove_user 用户ID。配置文件中的固定用户不能在菜单移除。",
        "missing_user_id": "缺少 Telegram 用户 ID。",
        "user_already_allowed": "用户 {user_id} 已经拥有使用权限。",
        "user_in_blacklist": "用户 {user_id} 在永久黑名单中，请先使用 /unblacklist_user {user_id}。",
        "user_added": "用户 {user_id} 已添加，立即生效，无需重启。",
        "user_already_dynamic": "用户 {user_id} 已经在动态白名单中。",
        "cannot_remove_admin": "不能移除管理员。",
        "static_user_remove": "用户 {user_id} 来自 PRIVATE_ALLOWED_USERS，请从配置文件移除并重启。",
        "user_removed": "用户 {user_id} 已移除。",
        "user_not_dynamic": "用户 {user_id} 不在动态白名单中。",
        "user_blacklisted": "用户 {user_id} 已永久拉黑，原有权限和申请已撤销。",
        "user_already_blacklisted": "用户 {user_id} 已经在永久黑名单中。",
        "user_unblacklisted": "用户 {user_id} 已解除永久拉黑，可以重新申请。",
        "user_not_blacklisted": "用户 {user_id} 不在永久黑名单中。",
        "yuanbao_menu": "更新视频号元宝 Cookie",
        "yuanbao_guide": (
            "更新视频号元宝 Cookie\n\n"
            "1. 打开 https://yuanbao.tencent.com/ 并登录。\n"
            "2. 浏览器按 F12 打开开发者工具，进入 Network/网络并刷新。\n"
            "3. 点开任意发往 yuanbao.tencent.com 的已登录请求，在 Request Headers/请求标头中复制完整 Cookie。\n"
            "4. 直接发送：/set_yuanbao_cookie Cookie: name=value; name2=value2\n"
            "5. Cookie 很长时，先发送文本或上传 cookies.txt，再回复该消息发送 /set_yuanbao_cookie。\n\n"
            "Cookie 等同登录凭证，请勿转发或提交到 GitHub。"
        ),
        "cookie_too_large": "Cookie 文件太大，请上传 1MB 以下的 cookies.txt。",
        "cookie_not_found": "没有识别到元宝 Cookie。\n\n请回复 cookies.txt 发送 /set_yuanbao_cookie，或发送 /set_yuanbao_cookie Cookie: name=value; name2=value2",
        "cookie_updated": "元宝 Cookie 已更新，识别到 {count} 个 Cookie；当前进程已刷新，重启后仍会保留。",
        "cookie_update_failed": "更新元宝 Cookie 失败，请检查 Cookie 格式后重试；详细错误已写入服务端日志。",
        "cookie_admin_only": "只有管理员可以更新元宝 Cookie。",
    },
    "en": {
        "language_button": "English / 中文",
        "language_title": "Choose your interface language:",
        "language_changed": "Interface language changed to English.",
        "private_denied": "This is a private Bot and your account does not have access yet.\n\nUse the button below to apply. You can start after an administrator approves the request.",
        "private_blacklisted": "Your account has been permanently blocked from using this Bot.",
        "apply_access": "Apply for access",
        "request_created": "Your request was submitted. Please wait for administrator approval.",
        "request_pending": "Your request is already awaiting approval. Please do not submit it repeatedly.",
        "request_rejected": "Your request was recently rejected. Try again later or contact the administrator.",
        "request_blacklisted": "Your account has been permanently blocked from applying.",
        "already_allowed": "You already have access.",
        "admin_only": "Only administrators can manage users.",
        "users_title": "User management",
        "add_user": "Add user",
        "remove_user": "Remove user",
        "list_users": "View authorized users",
        "open_web_admin": "Open Web administration",
        "close": "Close",
        "approve": "Approve",
        "reject": "Reject",
        "permanent_blacklist": "Permanently blacklist",
        "request_admin_notice": "New Bot access request\n\n{label}\n\nApproval grants access immediately; no restart is required.",
        "request_user_approved": "Your Bot access request was approved. You can now send a video link.",
        "request_user_rejected": "Your Bot access request was not approved. Contact the administrator if needed.",
        "request_user_blocked": "Your account has been permanently blocked from using or applying to this Bot.",
        "request_already_handled": "Another administrator already handled this request.",
        "invalid_request": "The request data is invalid.",
        "cannot_blacklist_admin": "An administrator cannot be blacklisted.",
        "approved_admin": "User {user_id} approved. Access is effective immediately.",
        "rejected_admin": "User {user_id}'s request was rejected.",
        "blacklisted_admin": "User {user_id} permanently blacklisted. Access and pending requests were removed.",
        "add_user_help": "Send /add_user USER_ID, or reply to the user's original/forwarded message with /add_user.",
        "remove_user_help": "Send /remove_user USER_ID. Configuration-managed users cannot be removed from this menu.",
        "missing_user_id": "A Telegram user ID is required.",
        "user_already_allowed": "User {user_id} already has access.",
        "user_in_blacklist": "User {user_id} is permanently blacklisted. Run /unblacklist_user {user_id} first.",
        "user_added": "User {user_id} added. Access is immediate and no restart is required.",
        "user_already_dynamic": "User {user_id} is already in the dynamic allowlist.",
        "cannot_remove_admin": "An administrator cannot be removed.",
        "static_user_remove": "User {user_id} comes from PRIVATE_ALLOWED_USERS. Remove the ID from config and restart.",
        "user_removed": "User {user_id} removed.",
        "user_not_dynamic": "User {user_id} is not in the dynamic allowlist.",
        "user_blacklisted": "User {user_id} permanently blacklisted. Access and pending requests were removed.",
        "user_already_blacklisted": "User {user_id} is already permanently blacklisted.",
        "user_unblacklisted": "User {user_id} was removed from the permanent blacklist and can apply again.",
        "user_not_blacklisted": "User {user_id} is not permanently blacklisted.",
        "yuanbao_menu": "Update WeChat Channels Yuanbao Cookie",
        "yuanbao_guide": (
            "Update the WeChat Channels Yuanbao Cookie\n\n"
            "1. Open https://yuanbao.tencent.com/ and sign in.\n"
            "2. Press F12, open Network, and refresh the page.\n"
            "3. Open an authenticated request to yuanbao.tencent.com and copy the complete Cookie request header.\n"
            "4. Send: /set_yuanbao_cookie Cookie: name=value; name2=value2\n"
            "5. For a long Cookie, send the text or upload cookies.txt first, then reply with /set_yuanbao_cookie.\n\n"
            "A Cookie is a login credential. Never forward it or commit it to GitHub."
        ),
        "cookie_too_large": "The Cookie file is too large. Upload a cookies.txt file smaller than 1 MB.",
        "cookie_not_found": "No Yuanbao Cookie was recognized.\n\nReply to cookies.txt with /set_yuanbao_cookie, or send /set_yuanbao_cookie Cookie: name=value; name2=value2",
        "cookie_updated": "Yuanbao Cookie updated. {count} Cookie entries were recognized; the current process was refreshed and the value will survive restarts.",
        "cookie_update_failed": "Could not update the Yuanbao Cookie. Check its format and try again; details were written to the server log.",
        "cookie_admin_only": "Only administrators can update the Yuanbao Cookie.",
    },
}


def normalize_language(value):
    normalized = str(value or "").strip().lower().replace("_", "-")
    return "zh" if normalized == "zh" or normalized.startswith("zh-") else "en"


def ensure_user_language(user_id, telegram_language_code=None, router=None, users_root=Path("users")):
    if router is None:
        from CONFIG.LANGUAGES.language_router import language_router as router

    language_file = Path(users_root) / str(int(user_id)) / "lang.txt"
    if language_file.exists():
        return normalize_language(router.get_user_language(user_id))
    language = normalize_language(telegram_language_code)
    router.set_user_language(user_id, language)
    return language


def user_language(user_id):
    from CONFIG.LANGUAGES.language_router import language_router

    return normalize_language(language_router.get_user_language(user_id))


def text(key, user_id=None, language=None, **values):
    selected = normalize_language(language) if language is not None else user_language(user_id)
    template = MESSAGES[selected][key]
    class SafeValues(dict):
        def __missing__(self, name):
            return "{" + name + "}"

    return template.format_map(SafeValues(values))
