#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "vendor" / "tg-ytdlp-bot"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def install_platform_runtime() -> None:
    source = ROOT / "scripts" / "templates" / "platform_runtime.py"
    destination = APP / "URL_PARSERS" / "platform_runtime.py"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def install_bot_menu() -> None:
    source = ROOT / "scripts" / "templates" / "bot_menu.py"
    destination = APP / "HELPERS" / "bot_menu.py"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def install_private_users() -> None:
    templates = {
        ROOT / "scripts" / "templates" / "private_users.py": APP / "HELPERS" / "private_users.py",
        ROOT / "scripts" / "templates" / "private_users_cmd.py": APP / "COMMANDS" / "private_users_cmd.py",
        ROOT / "scripts" / "templates" / "private_i18n.py": APP / "HELPERS" / "private_i18n.py",
        ROOT / "scripts" / "templates" / "lang_cmd.py": APP / "COMMANDS" / "lang_cmd.py",
        ROOT / "scripts" / "templates" / "messages_ZH.py": APP / "CONFIG" / "LANGUAGES" / "messages_ZH.py",
        ROOT / "scripts" / "templates" / "private_users_web_service.py": APP / "services" / "private_users_web_service.py",
        ROOT / "scripts" / "templates" / "dashboard_security.py": APP / "HELPERS" / "dashboard_security.py",
        ROOT / "scripts" / "templates" / "private_users_admin.html": APP / "web" / "templates" / "private_users_admin.html",
        ROOT / "scripts" / "templates" / "dashboard_login.html": APP / "web" / "templates" / "login.html",
        ROOT / "scripts" / "templates" / "private-users.js": APP / "web" / "static" / "private-users.js",
        ROOT / "scripts" / "templates" / "private-users.css": APP / "web" / "static" / "private-users.css",
    }
    for source, destination in templates.items():
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def patch_bot_i18n() -> None:
    router_path = APP / "CONFIG" / "LANGUAGES" / "language_router.py"
    router_text = router_path.read_text(encoding="utf-8")
    start = router_text.index("    def get_available_languages(self) -> Dict[str, str]:")
    end = router_text.index("    def _load_messages_with_ast", start)
    router_block = '''    def get_available_languages(self) -> Dict[str, str]:
        """Return languages that have complete user-interface coverage."""
        return {
            'zh': '中文',
            'en': 'English',
        }

'''
    router_path.write_text(router_text[:start] + router_block + router_text[end:], encoding="utf-8")

    extractor_path = APP / "URL_PARSERS" / "url_extractor.py"
    extractor_text = extractor_path.read_text(encoding="utf-8")
    if "from HELPERS.private_i18n import ensure_user_language\n" not in extractor_text:
        extractor_text = extractor_text.replace(
            "from HELPERS.safe_messeger import fake_message\n",
            "from HELPERS.safe_messeger import fake_message\n"
            "from HELPERS.private_i18n import ensure_user_language\n",
            1,
        )
    language_marker = '''def url_distractor(app, message):
    user_id = message.chat.id
'''
    language_block = '''def url_distractor(app, message):
    user_id = message.chat.id
    ensure_user_language(
        user_id,
        getattr(getattr(message, "from_user", None), "language_code", None),
    )
'''
    if language_block not in extractor_text:
        extractor_text = extractor_text.replace(language_marker, language_block, 1)
    extractor_path.write_text(extractor_text, encoding="utf-8")

    limiter_path = APP / "HELPERS" / "limitter.py"
    limiter_text = limiter_path.read_text(encoding="utf-8")
    if "from HELPERS.private_i18n import ensure_user_language, text\n" not in limiter_text:
        limiter_text = limiter_text.replace(
            "from HELPERS.safe_messeger import safe_send_message\n",
            "from HELPERS.safe_messeger import safe_send_message\n"
            "from HELPERS.private_i18n import ensure_user_language, text\n",
            1,
        )
    limiter_text = limiter_text.replace(
        '                text="你的账号已被管理员永久禁止使用此 Bot。",\n',
        '                text=text("private_blacklisted", user_id=message.chat.id),\n',
    )
    limiter_text = limiter_text.replace(
        '''                text=(
                    "这是私人 Bot，你当前还没有使用权限。\n\n"
                    "点击下方按钮提交申请，管理员批准后即可使用。"
                ),
''',
        '                text=text("private_denied", user_id=message.chat.id),\n',
    )
    limiter_text = limiter_text.replace(
        "                reply_markup=build_access_request_markup(),\n",
        "                reply_markup=build_access_request_markup(message.chat.id),\n",
    )
    check_marker = '''def check_user(message):
    messages = safe_get_messages(message.chat.id)
'''
    check_block = '''def check_user(message):
    ensure_user_language(
        message.chat.id,
        getattr(getattr(message, "from_user", None), "language_code", None),
    )
    messages = safe_get_messages(message.chat.id)
'''
    if check_block not in limiter_text:
        limiter_text = limiter_text.replace(check_marker, check_block, 1)
    limiter_path.write_text(limiter_text, encoding="utf-8")


def patch_douyin_audio_download() -> None:
    path = APP / "DOWN_AND_UP" / "down_and_audio.py"
    replace_once(
        path,
        "from URL_PARSERS.tags import extract_url_range_tags\n",
        "from URL_PARSERS.tags import extract_url_range_tags\n"
        "from URL_PARSERS.douyin_api import fetch_douyin_video, is_douyin_url\n"
        "from URL_PARSERS.platform_runtime import resolve_direct_media, should_retry_non_youtube_cookie\n",
    )
    replace_once(
        path,
        '''    user_id = message.chat.id
    logger.info(f"down_and_audio called: url={url}, quality_key={quality_key}, video_count={video_count}, video_start_with={video_start_with}")
''',
        '''    user_id = message.chat.id
    logger.info(f"down_and_audio called: url={url}, quality_key={quality_key}, video_count={video_count}, video_start_with={video_start_with}")
    original_url = url
    if is_douyin_url(url):
        douyin_info = resolve_direct_media(url, cached_video_info, fetch_douyin_video)
        if douyin_info:
            cached_video_info = douyin_info
            url = douyin_info["url"]
            logger.info(f"Using Douyin API direct media URL for audio download: {original_url}")
''',
    )
    replace_once(
        path,
        """                    if any(keyword in error_str for keyword in ['cookie', 'auth', 'login', 'sign in', '403', '401', 'forbidden', 'unauthorized']):
                        logger.info(f"Error appears to be cookie-related for {url}, trying cookie fallback")
""",
        """                    if should_retry_non_youtube_cookie(error_str, did_cookie_retry):
                        logger.info(f"Error appears to be cookie-related for {url}, trying cookie fallback")
                        did_cookie_retry = True
""",
    )
    replace_once(
        path,
        """                        else:
                            logger.warning(f"Audio download retry with cookie fallback failed for user {user_id}")
                    else:
                        logger.info(f"Error appears to be non-cookie-related for {url}, skipping cookie fallback")
""",
        """                        else:
                            logger.warning(f"Audio download retry with cookie fallback failed for user {user_id}")
                    elif did_cookie_retry:
                        logger.info(f"Cookie fallback already attempted for {url}; stopping retry recursion")
                    else:
                        logger.info(f"Error appears to be non-cookie-related for {url}, skipping cookie fallback")
""",
    )


def patch_instagram_gallery_fallback() -> None:
    path = APP / "HELPERS" / "fallback_helper.py"
    replace_once(
        path,
        "    error_lower = error_message.lower()\n",
        '''    error_lower = error_message.lower()

    if "instagram.com" in url.lower():
        from URL_PARSERS.platform_runtime import should_use_instagram_gallery_fallback
        if should_use_instagram_gallery_fallback(error_message):
            return True
''',
    )


def patch_limiter() -> None:
    path = APP / "HELPERS" / "limitter.py"
    text = path.read_text(encoding="utf-8")
    old_private_users_import = (
        "from HELPERS.private_users import collect_allowed_user_ids, get_private_user_store\n"
    )
    private_users_import = (
        "from HELPERS.private_users import (\n"
        "    build_access_request_markup,\n"
        "    collect_allowed_user_ids,\n"
        "    get_private_user_store,\n"
        ")\n"
    )
    if old_private_users_import in text:
        text = text.replace(old_private_users_import, private_users_import, 1)
        path.write_text(text, encoding="utf-8")
    elif private_users_import not in text:
        text = text.replace(
            "from CONFIG.config import Config\n",
            "from CONFIG.config import Config\n" + private_users_import,
            1,
        )
        path.write_text(text, encoding="utf-8")

    helper = r'''
def is_private_mode_enabled():
    return bool(getattr(Config, "PRIVATE_MODE", False))


def get_private_allowed_users():
    try:
        store = get_private_user_store()
        dynamic_users = store.list_ids()
        blacklisted_users = store.list_blacklisted_ids()
    except Exception as exc:
        logger.error(f"Could not read dynamic private users: {exc}")
        dynamic_users = set()
        blacklisted_users = set()
    admin_users = collect_allowed_user_ids(getattr(Config, "ADMIN", []), [], [])
    allowed_users = collect_allowed_user_ids(
        getattr(Config, "ADMIN", []),
        getattr(Config, "PRIVATE_ALLOWED_USERS", []),
        dynamic_users,
    )
    return (allowed_users - blacklisted_users) | admin_users


def is_private_user_allowed(user_id):
    if not is_private_mode_enabled():
        return True
    try:
        return int(user_id) in get_private_allowed_users()
    except Exception:
        return False


def deny_private_user(message):
    try:
        if get_private_user_store().is_blacklisted(message.chat.id):
            safe_send_message(
                chat_id=message.chat.id,
                text="你的账号已被管理员永久禁止使用此 Bot。",
                message=message,
            )
        else:
            safe_send_message(
                chat_id=message.chat.id,
                text=(
                    "这是私人 Bot，你当前还没有使用权限。\n\n"
                    "点击下方按钮提交申请，管理员批准后即可使用。"
                ),
                message=message,
                reply_markup=build_access_request_markup(),
            )
    except Exception:
        pass
    return False

'''
    text = path.read_text(encoding="utf-8")
    if "def is_private_mode_enabled():" not in text:
        replace_once(
            path,
            "def create_language_keyboard():\n",
            helper + "def create_language_keyboard():\n",
        )

    text = path.read_text(encoding="utf-8")
    start = text.index("def get_private_allowed_users():")
    end = text.index("def is_private_user_allowed", start)
    desired_get_allowed = helper[
        helper.index("def get_private_allowed_users():"):
        helper.index("def is_private_user_allowed")
    ]
    if text[start:end] != desired_get_allowed:
        path.write_text(text[:start] + desired_get_allowed + text[end:], encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    start = text.index("def deny_private_user(message):")
    end = text.index("def create_language_keyboard", start)
    desired_denial = helper[helper.index("def deny_private_user(message):"):]
    if text[start:end] != desired_denial:
        path.write_text(text[:start] + desired_denial + text[end:], encoding="utf-8")
    replace_once(
        path,
        """def is_user_in_channel(app, message):
    messages = safe_get_messages(message.chat.id)
    # Bypass subscription checks for explicitly allowed groups
""",
        """def is_user_in_channel(app, message):
    messages = safe_get_messages(message.chat.id)
    try:
        chat_type = getattr(getattr(message, "chat", None), "type", None)
        chat_id = int(getattr(message.chat, "id", 0))
        if str(chat_type).lower().endswith("private") and not is_private_user_allowed(chat_id):
            return deny_private_user(message)
    except Exception:
        pass
    # Bypass subscription checks for explicitly allowed groups
""",
    )
    replace_once(
        path,
        """    # Create The User Folder Inside The "Users" Directory
    user_dir = os.path.join("users", user_id_str)
""",
        """    try:
        chat_type = getattr(getattr(message, "chat", None), "type", None)
        if str(chat_type).lower().endswith("private") and not is_private_user_allowed(message.chat.id):
            return deny_private_user(message)
    except Exception:
        pass

    # Create The User Folder Inside The "Users" Directory
    user_dir = os.path.join("users", user_id_str)
""",
    )


def patch_dashboard() -> None:
    auth_path = APP / "services" / "auth_service.py"
    auth_text = auth_path.read_text(encoding="utf-8")
    if "import os\n" not in auth_text:
        auth_text = auth_text.replace("import json\n", "import json\nimport os\n", 1)
    auth_text = auth_text.replace(
        'self._password_hash = self._hash_password(str(password).strip() if password else "admin123")',
        'self._password_hash = self._hash_password(str(password) if password else "admin123")',
    )
    auth_text = auth_text.replace(
        "return self._hash_password(password) == self._password_hash",
        "return secrets.compare_digest(self._hash_password(password), self._password_hash)",
    )
    auth_text = auth_text.replace(
        '            password = str(password).strip() if password else ""\n',
        '            password = str(password) if password else ""\n',
    )
    auth_text = auth_text.replace(
        "            # Strip whitespace from inputs\n",
        "            # Normalize the username but preserve the password exactly.\n",
    )
    auth_text = auth_text.replace(
        '        password_clean = str(password).strip() if password else "admin123"\n',
        '        password_clean = str(password) if password else "admin123"\n',
    )
    auth_text = auth_text.replace(
        '        # Load username/password from config (strip whitespace)\n',
        '        # Normalize only the username; passwords are exact strings.\n',
    )
    auth_text = auth_text.replace(
        '        logger.info(f"[auth] Initialized with username=\'{self._username}\' (length={len(self._username)})")\n',
        '        logger.info("[auth] Dashboard authentication initialized")\n',
    )
    verbose_login_log = '''                    logger.warning(
                        f"[auth] Login failed for IP {ip}: "
                        f"username_match={username_match} "
                        f"(got='{username}' len={len(username)}, expected='{self._username}' len={len(self._username)}), "
                        f"password_match={password_match} "
                        f"(password_len={len(password)})"
                    )
'''
    auth_text = auth_text.replace(
        verbose_login_log,
        '                    logger.warning(f"[auth] Login failed for IP {ip}")\n',
    )
    session_write = '''            with open(self._sessions_file, "w", encoding="utf-8") as fh:
                json.dump(self._sessions, fh)
'''
    secure_session_write = session_write + "            os.chmod(self._sessions_file, 0o600)\n"
    if secure_session_write not in auth_text:
        auth_text = auth_text.replace(session_write, secure_session_write, 1)
    auth_path.write_text(auth_text, encoding="utf-8")

    path = APP / "web" / "dashboard_app.py"
    replace_once(
        path,
        "from fastapi.responses import HTMLResponse, RedirectResponse\n",
        "from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse\n",
    )
    text = path.read_text(encoding="utf-8")
    cors_import = "from fastapi.middleware.cors import CORSMiddleware\n"
    if cors_import in text:
        text = text.replace(cors_import, "", 1)
        path.write_text(text, encoding="utf-8")
    cors_block = '''# CORS for API requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


'''
    text = path.read_text(encoding="utf-8")
    if cors_block in text:
        path.write_text(text.replace(cors_block, "", 1), encoding="utf-8")
    old_imports = (
        "from services.auth_service import get_auth_service\n"
        "from services.private_users_web_service import PrivateUsersWebService\n"
        "from HELPERS.dashboard_security import is_allowed_browser_origin, use_secure_cookie\n"
        "from HELPERS.private_users import get_private_user_store\n"
    )
    new_imports = (
        "from services.auth_service import get_auth_service\n"
        "from services.private_users_web_service import PrivateUsersWebService\n"
        "from HELPERS.dashboard_security import (\n"
        "    is_allowed_browser_origin,\n"
        "    is_public_dashboard_path,\n"
        "    use_secure_cookie,\n"
        ")\n"
        "from HELPERS.private_users import get_private_user_store\n"
    )
    text = path.read_text(encoding="utf-8")
    if new_imports not in text:
        if old_imports in text:
            text = text.replace(old_imports, new_imports, 1)
        else:
            text = text.replace(
                "from services.auth_service import get_auth_service\n",
                new_imports,
                1,
            )
        path.write_text(text, encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '        public_paths = ["/login", "/api/login", "/api/reset-lockdown", "/static", "/health"]\n',
        '        public_paths = ["/login", "/api/login", "/static", "/health"]\n',
        1,
    )
    path.write_text(text, encoding="utf-8")
    replace_once(
        path,
        '''        public_paths = ["/login", "/api/login", "/static", "/health"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
''',
        '''        if is_public_dashboard_path(request.url.path):
            return await call_next(request)
''',
    )
    replace_once(
        path,
        '''            if request.url.path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="Unauthorized")
''',
        '''            if request.url.path.startswith("/api/"):
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
''',
    )
    replace_once(
        path,
        '''        # Read token from cookie
        token = request.cookies.get("auth_token")
''',
        '''        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            public_url = getattr(Config, "DASHBOARD_PUBLIC_URL", "")
            if not is_allowed_browser_origin(
                request.headers.get("origin"), public_url, str(request.base_url)
            ):
                return JSONResponse({"detail": "Cross-site request rejected"}, status_code=403)

        # Read token from cookie
        token = request.cookies.get("auth_token")
''',
    )
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "                secure=False,\n                samesite=\"lax\",\n",
        "                secure=use_secure_cookie(getattr(Config, \"DASHBOARD_PUBLIC_URL\", \"\")),\n                samesite=\"strict\",\n",
    )
    text = text.replace(
        "            secure=False,  # In production, set True when using HTTPS\n            samesite=\"lax\",\n",
        "            secure=use_secure_cookie(getattr(Config, \"DASHBOARD_PUBLIC_URL\", \"\")),\n            samesite=\"strict\",\n",
    )
    path.write_text(text, encoding="utf-8")
    replace_once(
        path,
        '    return templates.TemplateResponse("login.html", {"request": request})\n',
        '    return templates.TemplateResponse(request, "login.html")\n',
    )
    route_marker = '''@app.get("/api/active-users")
'''
    route_block = '''def _private_users_service():
    return PrivateUsersWebService(
        get_private_user_store(),
        getattr(Config, "ADMIN", []),
        getattr(Config, "PRIVATE_ALLOWED_USERS", []),
    )


@app.get("/admin/users", response_class=HTMLResponse)
async def private_users_page(request: Request):
    return templates.TemplateResponse(request, "private_users_admin.html")


@app.get("/api/private-users")
async def api_private_users():
    return _private_users_service().snapshot()


class PrivateUserActionRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=200)


PRIVATE_USER_ACTION_MESSAGES = {
    "added": "用户已授权，立即生效。",
    "already_allowed": "该用户已经拥有权限。",
    "blacklisted": "用户已永久拉黑。",
    "already_blacklisted": "该用户已经在永久黑名单中。",
    "unblacklisted": "永久拉黑已解除。",
    "not_blacklisted": "该用户不在永久黑名单中。",
    "removed": "用户权限已撤销。",
    "not_dynamic": "该用户不在动态授权名单中。",
    "approved": "申请已批准，权限立即生效。",
    "rejected": "申请已拒绝，24 小时内不能重复申请。",
    "not_pending": "这项申请已被处理或不存在。",
    "protected": "管理员或固定配置用户不能在这里移除或拉黑。",
}


@app.post("/api/private-users/{action}")
async def api_private_user_action(action: str, payload: PrivateUserActionRequest):
    service = _private_users_service()
    handlers = {
        "add": lambda: service.add(payload.user_id),
        "remove": lambda: service.remove(payload.user_id),
        "approve": lambda: service.approve(payload.user_id),
        "reject": lambda: service.reject(payload.user_id),
        "blacklist": lambda: service.blacklist(payload.user_id, payload.reason),
        "unblacklist": lambda: service.unblacklist(payload.user_id),
    }
    handler = handlers.get(action)
    if handler is None:
        raise HTTPException(status_code=404, detail="Unknown user action")
    try:
        result = handler()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result in {"protected", "blacklisted"} and action == "add":
        raise HTTPException(status_code=409, detail=PRIVATE_USER_ACTION_MESSAGES[result])
    return {"status": "ok", "result": result, "message": PRIVATE_USER_ACTION_MESSAGES[result]}


@app.get("/api/active-users")
'''
    replace_once(path, route_marker, route_block)

    dashboard_template = APP / "web" / "templates" / "dashboard.html"
    dashboard_html = dashboard_template.read_text(encoding="utf-8")
    if 'href="/admin/users"' not in dashboard_html:
        dashboard_html = dashboard_html.replace(
            '            <button class="logout-button" onclick="logout()" data-i18n="buttons.logout">Logout</button>\n',
            '            <a class="logout-button" href="/admin/users" data-i18n="buttons.user_access">User access</a>\n'
            '            <button class="logout-button" onclick="logout()" data-i18n="buttons.logout">Logout</button>\n',
            1,
        )
    old_language_switch = '''            <div class="lang-switch" role="group" aria-label="Language switch">
                <button type="button" data-lang-btn="en" class="active">EN</button>
                <span>|</span>
                <button type="button" data-lang-btn="ru">RU</button>
                <span>|</span>
                <button type="button" data-lang-btn="hi">HI</button>
                <span>|</span>
                <button type="button" data-lang-btn="ar">AR</button>
            </div>
'''
    bilingual_language_switch = '''            <div class="lang-switch" role="group" aria-label="Language switch">
                <button type="button" data-lang-btn="zh">中文</button>
                <span>|</span>
                <button type="button" data-lang-btn="en">EN</button>
            </div>
'''
    if old_language_switch in dashboard_html:
        dashboard_html = dashboard_html.replace(
            old_language_switch, bilingual_language_switch, 1
        )
    dashboard_html = dashboard_html.replace(
        '<a class="logout-button" href="/admin/users">User access</a>',
        '<a class="logout-button" href="/admin/users" data-i18n="buttons.user_access">User access</a>',
    )
    dashboard_html = dashboard_html.replace(
        'role="group" aria-label="Language switch"',
        'role="group" aria-label="Language switch" data-i18n-aria="aria.language"',
    )
    dashboard_html = dashboard_html.replace(
        'data-modal-close aria-label="Close"',
        'data-modal-close aria-label="Close" data-i18n-aria="aria.close"',
    )
    dashboard_html = dashboard_html.replace(
        'placeholder="Search..."',
        'placeholder="Search..." data-i18n-placeholder="misc.search"',
    )
    dashboard_html = dashboard_html.replace(
        'placeholder="Search by User ID, Name, or Username..."',
        'placeholder="Search by User ID, Name, or Username..." data-i18n-placeholder="history.search_placeholder"',
    )
    dashboard_html = dashboard_html.replace(
        '<p>Edit domain lists from CONFIG/domains.py</p>',
        '<p data-i18n="lists.domains_hint">Edit domain lists from CONFIG/domains.py</p>',
    )
    for minutes in (5, 15, 30, 60):
        dashboard_html = dashboard_html.replace(
            f'<option value="{minutes}">{minutes} min</option>',
            f'<option value="{minutes}" data-i18n="time.min_{minutes}">{minutes} min</option>',
        )
        dashboard_html = dashboard_html.replace(
            f'<option value="{minutes}" selected>{minutes} min</option>',
            f'<option value="{minutes}" selected data-i18n="time.min_{minutes}">{minutes} min</option>',
        )
    for attribute in (
        'data-i18n-aria="aria.language"',
        'data-i18n-aria="aria.close"',
        'data-i18n-placeholder="misc.search"',
        'data-i18n-placeholder="history.search_placeholder"',
    ):
        duplicate = f"{attribute} {attribute}"
        while duplicate in dashboard_html:
            dashboard_html = dashboard_html.replace(duplicate, attribute)
    dashboard_template.write_text(dashboard_html, encoding="utf-8")

    dashboard_script = APP / "web" / "static" / "dashboard.js"
    dashboard_js = dashboard_script.read_text(encoding="utf-8")
    zh_template = (
        ROOT / "scripts" / "templates" / "dashboard_zh_translations.js"
    ).read_text(encoding="utf-8")
    zh_start = "    // PRIVATE_ZH_TRANSLATIONS_START"
    zh_end = "    // PRIVATE_ZH_TRANSLATIONS_END"
    if zh_start in dashboard_js:
        start = dashboard_js.index(zh_start)
        end = dashboard_js.index(zh_end, start) + len(zh_end)
        dashboard_js = dashboard_js[:start] + zh_template.rstrip() + dashboard_js[end:]
    else:
        dashboard_js = dashboard_js.replace(
            "    translations.hi = {",
            zh_template.rstrip() + "\n\n    translations.hi = {",
            1,
        )
    while dashboard_js.count('            "buttons.user_access": "User access",\n') > 1:
        dashboard_js = dashboard_js.replace(
            '            "buttons.user_access": "User access",\n', "", 1
        )
    if '            "buttons.user_access": "User access",\n' not in dashboard_js:
        dashboard_js = dashboard_js.replace(
            '            "buttons.logout": "Logout",\n',
            '            "buttons.logout": "Logout",\n'
            '            "buttons.user_access": "User access",\n',
            1,
        )
    if '            "aria.language": "Language switch",\n' not in dashboard_js:
        dashboard_js = dashboard_js.replace(
            '            "buttons.user_access": "User access",\n',
            '            "buttons.user_access": "User access",\n'
            '            "aria.language": "Language switch",\n'
            '            "aria.close": "Close",\n',
            1,
        )
    english_dashboard_messages = '''            "misc.search": "Search...",
            "history.search_placeholder": "Search by User ID, name, or username...",
            "lists.domains_hint": "Edit domain lists from CONFIG/domains.py.",
            "time.min_5": "5 min",
            "time.min_15": "15 min",
            "time.min_30": "30 min",
            "time.min_60": "60 min",
            "confirm.rotate_ip": "Rotate IP address? This will restart WireGuard.",
            "confirm.restart": "Restart the tg-ytdlp-bot service?",
            "confirm.update_engines": "Update download engines? This may take several minutes.",
            "confirm.cleanup": "Delete all user files except system files? This cannot be undone.",
            "confirm.update_lists": "Update lists? This may take several minutes.",
            "result.ip_ok": "IP rotated successfully",
            "result.ip_failed": "Failed to rotate IP",
            "result.restart_ok": "Service restarted successfully",
            "result.restart_failed": "Failed to restart service",
            "result.engines_ok": "Download engines updated successfully",
            "result.engines_failed": "Failed to update download engines",
            "result.cleanup_ok": "User files cleaned up successfully",
            "result.cleanup_failed": "Failed to clean up user files",
            "result.lists_ok": "Lists updated successfully",
            "result.lists_failed": "Failed to update lists",
            "errors.operation": "Operation failed. Check the server log.",
            "errors.number": "Enter a number.",
            "errors.password_empty": "The password cannot be empty. Enter a new password.",
            "errors.layout_missing": "The page template is missing.",
            "result.password_updated": "Password updated. Log in again with the new password.",
            "result.username_updated": "Username updated. Log in again with the new username.",
            "result.saved": "Saved!",
            "lists.no_domains": "No domain lists.",
            "lists.add_item": "Add a new item...",
            "lists.add": "Add",
            "lists.save": "Save {name}",
            "lists.saved": "{name} saved. Restart the Bot to apply changes.",
            "lists.save_failed": "Failed to save {name}.",
'''
    if '            "misc.search": "Search...",\n' not in dashboard_js:
        dashboard_js = dashboard_js.replace(
            '            "aria.close": "Close",\n',
            '            "aria.close": "Close",\n' + english_dashboard_messages,
            1,
        )
    dashboard_js = dashboard_js.replace(
        '    let currentLang = localStorage.getItem("dashboardLang") || "en";',
        '    let currentLang = localStorage.getItem("adminLanguage") || '
        'localStorage.getItem("dashboardLang") || '
        '(navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en");',
        1,
    )
    duplicate_language_storage = (
        '        localStorage.setItem("adminLanguage", lang);\n'
        '        localStorage.setItem("adminLanguage", lang);\n'
    )
    dashboard_js = dashboard_js.replace(
        duplicate_language_storage,
        '        localStorage.setItem("adminLanguage", lang);\n',
    )
    if '        localStorage.setItem("adminLanguage", lang);\n' not in dashboard_js:
        dashboard_js = dashboard_js.replace(
            '        localStorage.setItem("dashboardLang", lang);\n',
            '        localStorage.setItem("dashboardLang", lang);\n'
            '        localStorage.setItem("adminLanguage", lang);\n',
            1,
        )
    aria_translation_block = '''        document.querySelectorAll("[data-i18n-aria]").forEach((el) => {
            el.setAttribute("aria-label", t(el.dataset.i18nAria));
        });
'''
    if aria_translation_block not in dashboard_js:
        dashboard_js = dashboard_js.replace(
            '        emptyStateText = t("misc.empty");\n',
            aria_translation_block + '        emptyStateText = t("misc.empty");\n',
            1,
        )
    placeholder_translation_block = '''        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            el.placeholder = t(el.dataset.i18nPlaceholder);
        });
'''
    if placeholder_translation_block not in dashboard_js:
        dashboard_js = dashboard_js.replace(
            aria_translation_block,
            aria_translation_block + placeholder_translation_block,
            1,
        )
    dashboard_replacements = {
        'confirm("Rotate IP address? This will restart WireGuard.")': 'confirm(t("confirm.rotate_ip"))',
        'data.message || (data.status === "ok" ? "IP rotated successfully" : "Failed to rotate IP")': 'data.status === "ok" ? t("result.ip_ok") : t("result.ip_failed")',
        'confirm("Restart tg-ytdlp-bot service?")': 'confirm(t("confirm.restart"))',
        'data.message || (data.status === "ok" ? "Service restarted successfully" : "Failed to restart service")': 'data.status === "ok" ? t("result.restart_ok") : t("result.restart_failed")',
        'confirm("Update engines? This may take several minutes.")': 'confirm(t("confirm.update_engines"))',
        'data.message || (data.status === "ok" ? "Engines updated successfully" : "Failed to update engines")': 'data.status === "ok" ? t("result.engines_ok") : t("result.engines_failed")',
        'confirm("Delete all user files (except system files)? This cannot be undone.")': 'confirm(t("confirm.cleanup"))',
        'data.message || (data.status === "ok" ? "Files cleaned up successfully" : "Failed to cleanup files")': 'data.status === "ok" ? t("result.cleanup_ok") : t("result.cleanup_failed")',
        'confirm("Update lists? This may take several minutes.")': 'confirm(t("confirm.update_lists"))',
        'data.message || (data.status === "ok" ? "Lists updated successfully" : "Failed to update lists")': 'data.status === "ok" ? t("result.lists_ok") : t("result.lists_failed")',
        'alert("Error: " + e.message);': 'alert(t("errors.operation"));',
        '`<div class="empty-state">Layout template missing</div>`': '`<div class="empty-state">${t("errors.layout_missing")}</div>`',
        'throw new Error("Value must be a number");': 'throw new Error(t("errors.number"));',
        'alert("Password cannot be empty. Please enter a new password.");': 'alert(t("errors.password_empty"));',
        'alert("Password updated successfully. Please log in again with the new password.");': 'alert(t("result.password_updated"));',
        'alert("Username updated successfully. Please log in again with the new username.");': 'alert(t("result.username_updated"));',
        'saveButton.textContent = "Saved!";': 'saveButton.textContent = t("result.saved");',
        '`<div class="empty-state">No domain lists</div>`': '`<div class="empty-state">${t("lists.no_domains")}</div>`',
        'placeholder="Search..."': 'placeholder="${t("misc.search")}"',
        'placeholder="Add new item..."': 'placeholder="${t("lists.add_item")}"',
        '<button onclick="addDomainItem(\'${listName}\')">Add</button>': '<button onclick="addDomainItem(\'${listName}\')">${t("lists.add")}</button>',
        '<button class="save-list-btn" onclick="saveDomainList(\'${listName}\')">Save ${listName}</button>': '<button class="save-list-btn" onclick="saveDomainList(\'${listName}\')">${replacePlaceholders(t("lists.save"), { name: listName })}</button>',
        'alert(`${listName} saved! Restart bot to apply changes.`);': 'alert(replacePlaceholders(t("lists.saved"), { name: listName }));',
        'alert(`Failed to save ${listName}`);': 'alert(replacePlaceholders(t("lists.save_failed"), { name: listName }));',
    }
    for old, new in dashboard_replacements.items():
        dashboard_js = dashboard_js.replace(old, new)
    dashboard_script.write_text(dashboard_js, encoding="utf-8")
    replace_once(
        path,
        """    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Bot statistics",
            "config": {
                "STATS_ACTIVE_TIMEOUT": getattr(Config, "STATS_ACTIVE_TIMEOUT", 900),
            },
        },
    )
""",
        """    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": "Bot statistics",
            "config": {
                "STATS_ACTIVE_TIMEOUT": getattr(Config, "STATS_ACTIVE_TIMEOUT", 900),
            },
        },
    )
""",
    )


def patch_storage_cleanup() -> None:
    path = APP / "services" / "system_service.py"
    text = path.read_text(encoding="utf-8")
    start = text.index("def cleanup_user_files() -> Dict[str, Any]:")
    end = text.index("\ndef update_lists()", start)
    replacement = '''def cleanup_user_files() -> Dict[str, Any]:
    """Delete generated media while preserving per-user settings and credentials."""
    try:
        users_dir = Path(__file__).resolve().parents[1] / "users"
        if not users_dir.is_dir():
            return {"status": "ok", "message": "User files cleaned up successfully", "removed": 0}

        protected = {
            "lang.txt", "args.txt", "keyboard.txt", "subs.txt", "subs_auto.txt",
            "mediainfo.txt", "split.txt", "tags.txt", "cookie.txt", "logs.txt",
            "format.txt", "nsfw.txt", "proxy.txt", "flood_wait.txt",
        }
        extensions = {
            ".part", ".ytdl", ".temp", ".tmp", ".mp3", ".mp4", ".mkv", ".avi",
            ".mov", ".wmv", ".flv", ".webm", ".m4a", ".aac", ".ogg", ".wav",
            ".jpg", ".jpeg", ".png",
        }
        removed = 0
        for file_path in users_dir.rglob("*"):
            if not file_path.is_file() or file_path.name in protected:
                continue
            if file_path.suffix.lower() not in extensions:
                continue
            try:
                file_path.unlink()
                removed += 1
            except FileNotFoundError:
                continue
            except OSError as exc:
                logger.warning("Could not remove runtime file %s: %s", file_path, exc)
        return {"status": "ok", "message": "User files cleaned up successfully", "removed": removed}
    except Exception as exc:
        logger.exception("Failed to clean user files")
        return {"status": "error", "message": str(exc)}

'''
    path.write_text(text[:start] + replacement + text[end + 1 :], encoding="utf-8")
def patch_compose() -> None:
    path = APP / "docker-compose.yml"
    replace_once(
        path,
        '      - "5555:5555"  # Dashboard (change port via Config.DASHBOARD_PORT in CONFIG/config.py)\n',
        '      - "127.0.0.1:5555:5555"  # Dashboard: local host only; use SSH tunnel on VPS.\n',
    )
    replace_once(
        path,
        """    volumes:
      - .:/app
""",
        """    volumes:
      - .:/app
      - ${REQABLE_CAPTURE_DIR:-./docker/reqable-capture-empty}:/reqable-capture:ro
""",
    )
    replace_once(
        path,
        """    depends_on:
      - bgutil-provider
      - configuration-webserver
""",
        """    depends_on:
      - bgutil-provider
      - configuration-webserver
      - douyin-api
""",
    )
    replace_once(
        path,
        """  configuration-webserver:
    image: caddy:2-alpine
""",
        """  douyin-api:
    image: evil0ctal/douyin_tiktok_download_api:latest
    restart: unless-stopped
    logging: *default-logging
    expose:
      - "80"
    environment:
      TZ: "${TZ}"
    volumes:
      - ./docker/douyin-api/douyin_web/config.yaml:/app/crawlers/douyin/web/config.yaml:ro

  configuration-webserver:
    image: caddy:2-alpine
""",
    )


def patch_dockerfile() -> None:
    path = APP / "Dockerfile"
    replace_once(
        path,
        """    git \\
    ffmpeg \\
""",
        """    git \\
    gcc \\
    python3-dev \\
    ffmpeg \\
""",
    )


def patch_firebase_local_mode() -> None:
    path = APP / "DATABASE" / "download_firebase.py"
    replace_once(
        path,
        """OUTPUT_FILE = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')

if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
    print(safe_get_messages().DB_NOT_ALL_PARAMETERS_SET_MSG)
    sys.exit(1)
""",
        """OUTPUT_FILE = getattr(Config, 'FIREBASE_CACHE_FILE', 'firebase_cache.json')
USE_FIREBASE = getattr(Config, 'USE_FIREBASE', True)

if USE_FIREBASE and (not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD):
    print(safe_get_messages().DB_NOT_ALL_PARAMETERS_SET_MSG)
    sys.exit(1)
""",
    )
    replace_once(
        path,
        """    # Check config
    if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
        print(safe_get_messages().DB_NOT_ALL_PARAMETERS_SET_MSG)
        return False
""",
        """    # Check config
    if not USE_FIREBASE:
        print("Firebase disabled; using local cache only.")
        return True
    if not FIREBASE_CONFIG or not FIREBASE_USER or not FIREBASE_PASSWORD:
        print(safe_get_messages().DB_NOT_ALL_PARAMETERS_SET_MSG)
        return False
""",
    )


def patch_douyin_normalization() -> None:
    normalizer_path = APP / "URL_PARSERS" / "normalizer.py"
    replace_once(
        normalizer_path,
        "import re\nfrom urllib.parse import urlparse, parse_qs, urlunparse, urlencode, unquote\n",
        "import re\nfrom urllib.parse import urlparse, parse_qs, urlunparse, urlencode, unquote\nimport requests\n",
    )
    replace_once(
        normalizer_path,
        """

def get_clean_playlist_url(url: str) -> str:
""",
        """

def normalize_douyin_url(url: str) -> str:
    \"\"\"Convert Douyin share redirect URLs to the canonical video URL yt-dlp expects.\"\"\"
    if not isinstance(url, str):
        return url

    parsed = urlparse(url.strip())
    domain = parsed.netloc.lower()
    path = parsed.path

    if domain == \"v.douyin.com\":
        try:
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=10,
                headers={\"User-Agent\": \"Mozilla/5.0\"},
            )
            final_url = response.url
            if final_url and final_url != url:
                return normalize_douyin_url(final_url)
        except Exception as exc:
            logger.warning(f\"normalize_douyin_url: failed to resolve short URL '{url}': {exc}\")

    match = re.search(r\"/share/video/(\\d+)\", path)
    if match and (domain == \"iesdouyin.com\" or domain.endswith(\".iesdouyin.com\")):
        result = f\"https://www.douyin.com/video/{match.group(1)}\"
        logger.info(f\"normalize_douyin_url: '{url}' -> '{result}'\")
        return result

    return url


def get_clean_playlist_url(url: str) -> str:
""",
    )

    yt_hook_path = APP / "DOWN_AND_UP" / "yt_dlp_hook.py"
    yt_hook_text = yt_hook_path.read_text(encoding="utf-8")
    if "from URL_PARSERS.normalizer import normalize_douyin_url\n" not in yt_hook_text:
        replace_once(
            yt_hook_path,
            "from HELPERS.fallback_helper import should_fallback_to_gallery_dl\n",
            "from HELPERS.fallback_helper import should_fallback_to_gallery_dl\nfrom URL_PARSERS.normalizer import normalize_douyin_url\n",
        )
    replace_once(
        yt_hook_path,
        "def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False, playlist_end_index=None):\n",
        "def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False, playlist_end_index=None):\n    url = normalize_douyin_url(url)\n",
    )

    link_cmd_path = APP / "COMMANDS" / "link_cmd.py"
    link_cmd_text = link_cmd_path.read_text(encoding="utf-8")
    if "from URL_PARSERS.normalizer import normalize_douyin_url\n" not in link_cmd_text:
        replace_once(
            link_cmd_path,
            "from COMMANDS.cookies_cmd import ensure_working_youtube_cookies\n",
            "from COMMANDS.cookies_cmd import ensure_working_youtube_cookies\nfrom URL_PARSERS.normalizer import normalize_douyin_url\n",
        )
    replace_once(
        link_cmd_path,
        "def get_direct_link(url, user_id, quality_arg=None, cookies_already_checked=False, use_proxy=False):\n",
        "def get_direct_link(url, user_id, quality_arg=None, cookies_already_checked=False, use_proxy=False):\n    url = normalize_douyin_url(url)\n",
    )


def patch_douyin_api_sidecar() -> None:
    douyin_api_path = APP / "URL_PARSERS" / "douyin_api.py"
    douyin_api_path.write_text(
        '''import os
import re
from urllib.parse import urlparse

import requests

from HELPERS.logger import logger
from URL_PARSERS.normalizer import normalize_douyin_url


DOUYIN_API_BASE_URL = os.getenv("DOUYIN_API_BASE_URL", "http://douyin-api")
DOUYIN_API_TIMEOUT = int(os.getenv("DOUYIN_API_TIMEOUT", "35"))
DOUYIN_ALLOWED_HOSTS = {
    "douyin.com",
    "www.douyin.com",
    "v.douyin.com",
    "iesdouyin.com",
    "www.iesdouyin.com",
}


def is_douyin_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    return host in DOUYIN_ALLOWED_HOSTS or host.endswith(".douyin.com") or host.endswith(".iesdouyin.com")


def extract_douyin_aweme_id(url: str) -> str | None:
    parsed = urlparse(url)
    for pattern in (r"/video/(\\d+)", r"/share/video/(\\d+)"):
        match = re.search(pattern, parsed.path)
        if match:
            return match.group(1)
    return None


def _pick_url(*candidates):
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            return candidate
    return None


def _first_cover(cover_data):
    if not isinstance(cover_data, dict):
        return None
    for key in ("cover", "origin_cover", "dynamic_cover"):
        value = cover_data.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            url_list = value.get("url_list")
            if isinstance(url_list, list) and url_list:
                return url_list[0]
    return None


def _as_ytdlp_info(source_url: str, data: dict, direct_url: str) -> dict:
    video_id = data.get("video_id") or extract_douyin_aweme_id(source_url) or "douyin"
    title = data.get("desc") or f"douyin-{video_id}"
    duration = data.get("duration")
    video_format = {
        "format_id": "douyin-api",
        "format": "douyin-api",
        "url": direct_url,
        "ext": "mp4",
        "protocol": "https",
        "vcodec": "h264",
        "acodec": "aac",
    }
    info = {
        "id": str(video_id),
        "title": title,
        "description": data.get("desc"),
        "webpage_url": source_url,
        "original_url": source_url,
        "url": direct_url,
        "ext": "mp4",
        "duration": duration,
        "thumbnail": _first_cover(data.get("cover_data")),
        "formats": [video_format],
        "requested_formats": [video_format],
    }
    return {key: value for key, value in info.items() if value is not None}


def fetch_douyin_video(url: str) -> dict | None:
    if not is_douyin_url(url):
        return None

    source_url = normalize_douyin_url(url)
    if not is_douyin_url(source_url):
        logger.warning(f"Douyin API rejected non-Douyin URL after normalization: {source_url}")
        return None

    endpoint = f"{DOUYIN_API_BASE_URL.rstrip('/')}/api/hybrid/video_data"
    try:
        response = requests.get(
            endpoint,
            params={"url": source_url, "minimal": "true"},
            timeout=DOUYIN_API_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.warning(f"Douyin API fallback failed for {source_url}: {exc}")
        return None

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        logger.warning(f"Douyin API returned an unexpected response for {source_url}")
        return None

    if data.get("type") != "video":
        logger.warning(f"Douyin API returned non-video content for {source_url}: {data.get('type')}")
        return None

    video_data = data.get("video_data") or {}
    direct_url = _pick_url(
        video_data.get("nwm_video_url_HQ"),
        video_data.get("nwm_video_url"),
        video_data.get("wm_video_url_HQ"),
        video_data.get("wm_video_url"),
    )
    if not direct_url:
        logger.warning(f"Douyin API did not return a video URL for {source_url}")
        return None

    result = _as_ytdlp_info(source_url, data, direct_url)
    result["douyin_api_data"] = data
    return result
''',
        encoding="utf-8",
    )

    yt_hook_path = APP / "DOWN_AND_UP" / "yt_dlp_hook.py"
    replace_once(
        yt_hook_path,
        "from HELPERS.fallback_helper import should_fallback_to_gallery_dl\n",
        "from HELPERS.fallback_helper import should_fallback_to_gallery_dl\nfrom URL_PARSERS.douyin_api import fetch_douyin_video, is_douyin_url\n",
    )
    replace_once(
        yt_hook_path,
        "def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False, playlist_end_index=None):\n    url = normalize_douyin_url(url)\n",
        "def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False, playlist_end_index=None):\n    url = normalize_douyin_url(url)\n    douyin_info = fetch_douyin_video(url)\n    if douyin_info:\n        logger.info(f\"Douyin API returned metadata for {url}\")\n        return douyin_info\n    if is_douyin_url(url):\n        logger.warning(f\"Douyin resolver did not return media metadata for {url}; skipping yt-dlp fallback\")\n        return {\n            \"error\": \"DOUYIN_RESOLVER_UNAVAILABLE\",\n            \"original_error\": (\n                \"Douyin local sidecar and remote resolver did not return a media URL. \"\n                \"Configure DOUYIN_REMOTE_RESOLVER_URL or try another resolver.\"\n            ),\n        }\n",
    )

    link_cmd_path = APP / "COMMANDS" / "link_cmd.py"
    replace_once(
        link_cmd_path,
        "from COMMANDS.cookies_cmd import ensure_working_youtube_cookies\n",
        "from COMMANDS.cookies_cmd import ensure_working_youtube_cookies\nfrom URL_PARSERS.douyin_api import fetch_douyin_video\n",
    )
    replace_once(
        link_cmd_path,
        "def get_direct_link(url, user_id, quality_arg=None, cookies_already_checked=False, use_proxy=False):\n    url = normalize_douyin_url(url)\n",
        "def get_direct_link(url, user_id, quality_arg=None, cookies_already_checked=False, use_proxy=False):\n    url = normalize_douyin_url(url)\n    douyin_info = fetch_douyin_video(url)\n    if douyin_info:\n        video_url = douyin_info.get(\"url\")\n        return {\n            \"success\": True,\n            \"title\": douyin_info.get(\"title\", \"Douyin video\"),\n            \"duration\": douyin_info.get(\"duration\", 0),\n            \"video_url\": video_url,\n            \"audio_url\": None,\n            \"format\": \"douyin-api\",\n            \"player_urls\": [video_url] if video_url else [],\n        }\n",
    )

    down_and_up_path = APP / "DOWN_AND_UP" / "down_and_up.py"
    replace_once(
        down_and_up_path,
        "from HELPERS.fallback_helper import should_fallback_to_gallery_dl\n",
        "from HELPERS.fallback_helper import should_fallback_to_gallery_dl\nfrom URL_PARSERS.douyin_api import fetch_douyin_video, is_douyin_url\n",
    )
    down_and_up_text = down_and_up_path.read_text(encoding="utf-8")
    if "Using Douyin API direct media URL" not in down_and_up_text:
        replace_once(
            down_and_up_path,
            """    user_id = message.chat.id
    # Ensure fresh subtitle state at the start of a task even for direct calls (bypassing Always Ask)
""",
            """    user_id = message.chat.id
    original_url = url
    if is_douyin_url(url):
        douyin_info = cached_video_info if cached_video_info and cached_video_info.get("url") else fetch_douyin_video(url)
        if douyin_info and douyin_info.get("url"):
            cached_video_info = douyin_info
            url = douyin_info["url"]
            force_no_title = True
            logger.info(f"Using Douyin API direct media URL for {original_url}")
    # Ensure fresh subtitle state at the start of a task even for direct calls (bypassing Always Ask)
""",
        )

    template_path = ROOT / "scripts" / "templates" / "douyin_api.py"
    if template_path.exists():
        douyin_api_path.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")


def patch_share_text_tag_parser() -> None:
    path = APP / "URL_PARSERS" / "tags.py"
    replace_once(
        path,
        """    # New way: Looking for everything #tags throughout the text (multi -line)
    tags = []
    tags_text = ''
    error_tag = None
    error_tag_example = None
    # We collect everything #tags from the whole text (multi -line)
    for raw in re.finditer(r'#([^#\\s]+)', text, re.UNICODE):
        tag = raw.group(1)
        if not re.fullmatch(r'[\\w\\d_]+', tag, re.UNICODE):
            error_tag = tag
            example = re.sub(r'[^\\w\\d_]', '_', tag, flags=re.UNICODE)
            error_tag_example = f'#{example}'
            break
        tags.append(f'#{tag}')
""",
        """    # User tags are parsed only from the part after the URL/range/playlist.
    # Platform share text before the URL often contains native hashtags like
    # "#..." or punctuation-heavy topics; treating those as bot tags blocks
    # otherwise valid shared links.
    tags = []
    tags_text = ''
    error_tag = None
    error_tag_example = None
    for raw in re.finditer(r'#([^#\\s]+)', after_range, re.UNICODE):
        tag = raw.group(1)
        if not re.search(r'[\\w\\d_]', tag, re.UNICODE):
            continue
        if not re.fullmatch(r'[\\w\\d_]+', tag, re.UNICODE):
            error_tag = tag
            example = re.sub(r'[^\\w\\d_]', '_', tag, flags=re.UNICODE)
            error_tag_example = f'#{example}'
            break
        tags.append(f'#{tag}')
""",
    )


def patch_douyin_always_ask_error() -> None:
    path = APP / "DOWN_AND_UP" / "always_ask_menu.py"
    if "info.get('error') == 'DOUYIN_RESOLVER_UNAVAILABLE'" in path.read_text(encoding="utf-8"):
        return
    replace_once(
        path,
        """                send_error_to_user(message, tiktok_message)
                return
            
            # Check for fallback to gallery-dl recommendation
""",
        """                send_error_to_user(message, tiktok_message)
                return

            # Check for Douyin resolver failures before yt-dlp fallback can loop on cookies
            if isinstance(info, dict) and info.get('error') == 'DOUYIN_RESOLVER_UNAVAILABLE':
                logger.info(f"Douyin resolver unavailable in ask_quality_menu for user {user_id}: {url}")
                delete_processing_message(app, user_id, proc_msg)
                original_error = info.get('original_error', 'Douyin resolver unavailable')
                douyin_message = (
                    "抖音解析失败：本地 sidecar 和远程解析器都没有返回视频直链。\\n\\n"
                    f"<code>{original_error}</code>\\n\\n"
                    "现在 Bot 已经不会继续卡在处理中。要真正下载抖音，需要配置可用的 "
                    "<code>DOUYIN_REMOTE_RESOLVER_URL</code>，或者换一个可返回直链的抖音解析接口。"
                )
                send_error_to_user(message, douyin_message)
                return
            
            # Check for fallback to gallery-dl recommendation
""",
    )


def patch_yuanbao_cookie_command() -> None:
    path = APP / "COMMANDS" / "admin_cmd.py"
    text = path.read_text(encoding="utf-8")
    if "import tempfile\n" not in text:
        text = text.replace("import threading\n", "import threading\nimport tempfile\n", 1)
    text = text.replace(
        "from HELPERS.bot_menu import YUANBAO_COOKIE_HELP\n", ""
    ).replace(
        "from HELPERS.bot_menu import get_yuanbao_cookie_help\n", ""
    ).replace(
        "from HELPERS.private_i18n import text\n", ""
    )
    imports = (
        "from HELPERS.bot_menu import get_yuanbao_cookie_help\n"
        "from HELPERS.private_i18n import text\n"
    )
    text = text.replace(
        "from HELPERS.decorators import background_handler\n",
        "from HELPERS.decorators import background_handler\n" + imports,
        1,
    )
    block = (ROOT / "scripts" / "templates" / "yuanbao_cookie_admin_block.py").read_text(encoding="utf-8")
    block = block.split("\n\n", 1)[1]
    marker = '@app.on_message(filters.command("reload_cache") & filters.private)\n'
    if marker not in text:
        raise RuntimeError(f"Expected reload_cache marker not found in {path}")
    block_start = "def _extract_yuanbao_cookie_header(raw_text: str) -> tuple[str, int]:\n"
    if block_start in text:
        start = text.index(block_start)
        end = text.index(marker, start)
        text = text[:start] + block.rstrip() + "\n\n" + text[end:]
    else:
        text = text.replace(marker, block.rstrip() + "\n\n" + marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_yuanbao_cookie_menus() -> None:
    settings_path = APP / "COMMANDS" / "settings_cmd.py"
    settings_text = settings_path.read_text(encoding="utf-8")
    if "from HELPERS.bot_menu import get_yuanbao_cookie_help\n" not in settings_text:
        settings_text = settings_text.replace(
            "from HELPERS.decorators import background_handler\n",
            "from HELPERS.decorators import background_handler\n"
            "from HELPERS.bot_menu import get_yuanbao_cookie_help\n"
            "from HELPERS.private_i18n import text\n",
            1,
        )
    settings_text = settings_text.replace(
        "from HELPERS.bot_menu import YUANBAO_COOKIE_HELP\n",
        "from HELPERS.bot_menu import get_yuanbao_cookie_help\n"
        "from HELPERS.private_i18n import text\n",
    )

    if 'callback_data="settings__cmd__yuanbao_cookie"' not in settings_text:
        old_cookie_menu = '''    if data == "cookies":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_DOWNLOAD_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_COOKIES_FROM_BROWSER_BUTTON_MSG,
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_CHECK_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_SAVE_AS_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__save_as_cookie")],
            [InlineKeyboardButton(safe_get_messages(user_id).SUBS_BACK_BUTTON_MSG, callback_data="settings__menu__back")]
        ])
'''
        new_cookie_menu = '''    if data == "cookies":
        cookie_buttons = [
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_DOWNLOAD_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__download_cookie")],
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_COOKIES_FROM_BROWSER_BUTTON_MSG,
                                  callback_data="settings__cmd__cookies_from_browser")],
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_CHECK_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__check_cookie")],
            [InlineKeyboardButton(safe_get_messages(user_id).SETTINGS_SAVE_AS_COOKIE_BUTTON_MSG,
                                  callback_data="settings__cmd__save_as_cookie")],
        ]
        if int(user_id) in Config.ADMIN:
            cookie_buttons.append([
                InlineKeyboardButton(
                    text("yuanbao_menu", user_id=user_id),
                    callback_data="settings__cmd__yuanbao_cookie",
                )
            ])
        cookie_buttons.append([
            InlineKeyboardButton(
                safe_get_messages(user_id).SUBS_BACK_BUTTON_MSG,
                callback_data="settings__menu__back",
            )
        ])
        keyboard = InlineKeyboardMarkup(cookie_buttons)
'''
        if old_cookie_menu not in settings_text:
            raise RuntimeError(f"Expected cookie settings menu not found in {settings_path}")
        settings_text = settings_text.replace(old_cookie_menu, new_cookie_menu, 1)

    if 'if data == "yuanbao_cookie":' not in settings_text:
        callback_marker = '''    data = callback_query.data.split("__")[2]

    # For commands that are processed only via url_distractor, create a temporary Message
'''
        callback_block = '''    data = callback_query.data.split("__")[2]

    if data == "yuanbao_cookie":
        if int(user_id) not in Config.ADMIN:
            callback_query.answer(text("cookie_admin_only", user_id=user_id), show_alert=True)
            return
        safe_send_message(
            user_id,
            get_yuanbao_cookie_help(user_id),
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
        )
        callback_query.answer(safe_get_messages(user_id).SETTINGS_HINT_SENT_MSG)
        return

    # For commands that are processed only via url_distractor, create a temporary Message
'''
        if callback_marker not in settings_text:
            raise RuntimeError(f"Expected settings callback marker not found in {settings_path}")
        settings_text = settings_text.replace(callback_marker, callback_block, 1)
    settings_text = settings_text.replace(
        '                    "更新视频号元宝 Cookie",\n',
        '                    text("yuanbao_menu", user_id=user_id),\n',
    )
    settings_text = settings_text.replace(
        '            callback_query.answer("只有管理员可以更新元宝 Cookie。", show_alert=True)\n',
        '            callback_query.answer(text("cookie_admin_only", user_id=user_id), show_alert=True)\n',
    )
    settings_text = settings_text.replace(
        "            YUANBAO_COOKIE_HELP,\n",
        "            get_yuanbao_cookie_help(user_id),\n",
    )
    settings_path.write_text(settings_text, encoding="utf-8")

    magic_path = APP / "magic.py"
    magic_text = magic_path.read_text(encoding="utf-8")
    if "from HELPERS.bot_menu import register_admin_bot_commands\n" not in magic_text:
        magic_text = magic_text.replace(
            "from HELPERS.safe_messeger import *\n",
            "from HELPERS.safe_messeger import *\n"
            "from HELPERS.bot_menu import register_admin_bot_commands\n",
            1,
        )
    if "    register_admin_bot_commands(app, Config.ADMIN)\n" not in magic_text:
        magic_text = magic_text.replace(
            'if __name__ == "__main__":\n    app.start()\n',
            'if __name__ == "__main__":\n    app.start()\n'
            "    register_admin_bot_commands(app, Config.ADMIN)\n",
            1,
        )
    magic_path.write_text(magic_text, encoding="utf-8")

    commands_path = APP / "TXT" / "commands.txt"
    commands_text = commands_path.read_text(encoding="utf-8")
    menu_line = "set_yuanbao_cookie - Update WeChat Channels Yuanbao cookie (admin only)\n"
    if menu_line not in commands_text:
        commands_path.write_text(commands_text.rstrip() + "\n" + menu_line, encoding="utf-8")


def patch_private_user_commands() -> None:
    magic_path = APP / "magic.py"
    magic_text = magic_path.read_text(encoding="utf-8")
    import_line = "from COMMANDS.private_users_cmd import *\n"
    if import_line not in magic_text:
        marker = "from COMMANDS.admin_cmd import *\n"
        if marker not in magic_text:
            raise RuntimeError(f"Expected admin command import not found in {magic_path}")
        magic_path.write_text(
            magic_text.replace(marker, marker + import_line, 1),
            encoding="utf-8",
        )

    commands_path = APP / "TXT" / "commands.txt"
    commands_text = commands_path.read_text(encoding="utf-8").rstrip()
    lines = (
        "users - Open the private user management menu (admin only)",
        "add_user - Add a Telegram user ID (admin only)",
        "remove_user - Remove a Telegram user ID (admin only)",
        "list_users - List authorized users (admin only)",
        "blacklist_user - Permanently blacklist a Telegram user ID (admin only)",
        "unblacklist_user - Remove a Telegram user ID from the permanent blacklist (admin only)",
    )
    for line in lines:
        if line not in commands_text.splitlines():
            commands_text += "\n" + line
    commands_path.write_text(commands_text + "\n", encoding="utf-8")


def patch_tiktok_telegram_safe_format() -> None:
    path = APP / "DOWN_AND_UP" / "down_and_up.py"
    text = path.read_text(encoding="utf-8")
    if "TIKTOK_TELEGRAM_SAFE_FORMAT" not in text:
        replace_once(
            path,
            "# Get app instance for decorators\napp = get_app()\n\n",
            '''# Get app instance for decorators
app = get_app()

TIKTOK_TELEGRAM_SAFE_FORMAT = (
    "best[vcodec*=h264][acodec!=none][ext=mp4]/"
    "best[vcodec*=avc1][acodec!=none][ext=mp4]/"
    "best[vcodec!=none][acodec!=none][ext=mp4]/"
    "bv*[vcodec*=h264]+ba[acodec*=mp4a]/"
    "bv*[vcodec*=avc1]+ba[acodec*=mp4a]/"
    "bv*[vcodec*=h264]+ba/"
    "bv*[vcodec*=avc1]+ba/"
    "best"
)


def _is_tiktok_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host == "tiktok.com" or host.endswith(".tiktok.com")

''',
        )

    text = path.read_text(encoding="utf-8")
    if "{'format': TIKTOK_TELEGRAM_SAFE_FORMAT" in text:
        return
    needle = """        if format_override:
            attempts = [{'format': format_override, 'prefer_ffmpeg': True, 'merge_output_format': user_merge_format}]
        else:
            # if use_default_format is True, then do not take from format.txt, but use default ones
            if use_default_format:
"""
    replacement = """        if format_override:
            attempts = [{'format': format_override, 'prefer_ffmpeg': True, 'merge_output_format': user_merge_format}]
        else:
            # TikTok may expose high-quality H.265/bytevc1 formats that Telegram
            # plays unreliably. Prefer H.264 + AAC MP4 for bot uploads.
            if _is_tiktok_url(original_url) or _is_tiktok_url(url):
                attempts = [
                    {'format': TIKTOK_TELEGRAM_SAFE_FORMAT, 'prefer_ffmpeg': True, 'merge_output_format': user_merge_format, 'extract_flat': False},
                    {'format': 'best[vcodec!=none][acodec!=none][ext=mp4]/best', 'prefer_ffmpeg': False, 'extract_flat': False}
                ]
            elif use_default_format:
"""
    if replacement not in text:
        if needle not in text:
            raise RuntimeError(f"Expected TikTok format insertion point not found in {path}")
        path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")


def patch_x_multi_video_posts() -> None:
    path = APP / "DOWN_AND_UP" / "down_and_up.py"
    text = path.read_text(encoding="utf-8")

    if "def _is_x_twitter_url(url: str) -> bool:" not in text:
        replace_once(
            path,
            '''def _is_tiktok_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host == "tiktok.com" or host.endswith(".tiktok.com")


''',
            '''def _is_tiktok_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host == "tiktok.com" or host.endswith(".tiktok.com")


def _is_x_twitter_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host in {"x.com", "twitter.com"} or host.endswith(".x.com") or host.endswith(".twitter.com")


def _get_multi_video_entries(info) -> list:
    if not isinstance(info, dict):
        return []

    entries = info.get("_playlist_entries") or info.get("entries")
    if not isinstance(entries, list):
        return []

    video_entries = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("formats") or entry.get("url") or entry.get("webpage_url"):
            video_entries.append(entry)
    return video_entries


''',
        )

    text = path.read_text(encoding="utf-8")
    marker = '''    user_id = message.chat.id
    original_url = url
'''
    insertion = '''    user_id = message.chat.id
    original_url = url
    x_multi_video_entries = _get_multi_video_entries(cached_video_info) if _is_x_twitter_url(url) else []
    if _is_x_twitter_url(url) and not x_multi_video_entries and video_count == 1:
        try:
            from DOWN_AND_UP.yt_dlp_hook import get_video_formats
            probed_info = get_video_formats(url, user_id, 1, cookies_already_checked, use_proxy)
            probed_entries = _get_multi_video_entries(probed_info)
            if len(probed_entries) > 1:
                cached_video_info = probed_info
                x_multi_video_entries = probed_entries
        except Exception as exc:
            logger.warning(f"Could not pre-detect X/Twitter multi-video entries for {url}: {exc}")
    if x_multi_video_entries and len(x_multi_video_entries) > 1:
        video_count = len(x_multi_video_entries)
        video_start_with = 1
        logger.info(f"X/Twitter multi-video post detected: {video_count} media entries will be downloaded")
'''
    if "x_multi_video_entries = _get_multi_video_entries" not in text:
        if marker not in text:
            raise RuntimeError(f"Expected X multi-video insertion point not found in {path}")
        path.write_text(text.replace(marker, insertion, 1), encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    old = '''                    elif len(entries) > 1:  # If the video in the playlist is more than one
                        if current_index and current_index < len(entries):
                            info_dict = entries[current_index]
                        else:
                            raise Exception(f"Video index {current_index} out of range (total {len(entries)})")
'''
    new = '''                    elif len(entries) > 1:  # If the video in the playlist is more than one
                        entry_index = int(current_index) - 1 if current_index else 0
                        if 0 <= entry_index < len(entries):
                            info_dict = entries[entry_index]
                        else:
                            raise Exception(f"Video index {current_index} out of range (total {len(entries)})")
'''
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_x_multi_video_format_probe() -> None:
    path = APP / "DOWN_AND_UP" / "yt_dlp_hook.py"
    text = path.read_text(encoding="utf-8")

    if "def _is_x_twitter_url(url: str) -> bool:" not in text:
        if "from urllib.parse import urlparse\n" not in text:
            text = text.replace(
                "from URL_PARSERS.normalizer import normalize_douyin_url\n",
                "from URL_PARSERS.normalizer import normalize_douyin_url\nfrom urllib.parse import urlparse\n",
                1,
            )
        marker = "def get_video_formats(url, user_id=None, playlist_start_index=1, cookies_already_checked=False, use_proxy=False, playlist_end_index=None):\n"
        helper = '''def _is_x_twitter_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return host in {"x.com", "twitter.com"} or host.endswith(".x.com") or host.endswith(".twitter.com")

'''
        if marker not in text:
            raise RuntimeError(f"Expected get_video_formats marker not found in {path}")
        text = text.replace(marker, helper + "\n" + marker, 1)
        path.write_text(text, encoding="utf-8")

    text = path.read_text(encoding="utf-8")
    if "should_probe_all_x_media = _is_x_twitter_url(url)" not in text:
        text = text.replace("        'playlist_items': playlist_items_str,    \n", "        'playlist_items': playlist_items_str,\n")
        text = text.replace("    \n    ytdl_opts = {\n", "\n    ytdl_opts = {\n")
        text = text.replace("    }\n    \n    # Add match_filter only if domain is not in NO_FILTER_DOMAINS\n", "    }\n\n    # Add match_filter only if domain is not in NO_FILTER_DOMAINS\n")
        old = '''    else:
        # Single item
        playlist_items_str = str(playlist_start_index)

    ytdl_opts = {
'''
        new = '''    else:
        # Single item
        playlist_items_str = str(playlist_start_index)
    should_probe_all_x_media = _is_x_twitter_url(url) and playlist_end_index is None and playlist_start_index == 1

    ytdl_opts = {
'''
        if old not in text:
            raise RuntimeError(f"Expected playlist_items insertion point not found in {path}")
        text = text.replace(old, new, 1)

        old = '''        'extract_flat': False,
        'simulate': True,
        'playlist_items': playlist_items_str,
        'extractor_args': {
'''
        new = '''        'extract_flat': False,
        'simulate': True,
        'extractor_args': {
'''
        if old not in text:
            raise RuntimeError(f"Expected ytdl_opts playlist_items entry not found in {path}")
        text = text.replace(old, new, 1)

        old = '''        'check_certificate': False,
        'live_from_start': True
    }

    # Add match_filter only if domain is not in NO_FILTER_DOMAINS
'''
        new = '''        'check_certificate': False,
        'live_from_start': True
    }
    if should_probe_all_x_media:
        logger.info("X/Twitter URL detected without explicit range; probing all media entries")
    else:
        ytdl_opts['playlist_items'] = playlist_items_str

    # Add match_filter only if domain is not in NO_FILTER_DOMAINS
'''
        if old not in text:
            raise RuntimeError(f"Expected ytdl_opts post block not found in {path}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    install_platform_runtime()
    install_bot_menu()
    install_private_users()
    patch_limiter()
    patch_bot_i18n()
    patch_dashboard()
    patch_storage_cleanup()
    patch_compose()
    patch_dockerfile()
    patch_firebase_local_mode()
    patch_douyin_normalization()
    patch_douyin_api_sidecar()
    patch_douyin_audio_download()
    patch_instagram_gallery_fallback()
    patch_share_text_tag_parser()
    patch_douyin_always_ask_error()
    patch_yuanbao_cookie_command()
    patch_yuanbao_cookie_menus()
    patch_private_user_commands()
    patch_tiktok_telegram_safe_format()
    patch_x_multi_video_posts()
    patch_x_multi_video_format_probe()
    print("Private hardening applied.")


if __name__ == "__main__":
    main()
