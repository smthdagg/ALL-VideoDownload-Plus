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
    helper = '''
def is_private_mode_enabled():
    return bool(getattr(Config, "PRIVATE_MODE", False))


def get_private_allowed_users():
    allowed = set()
    for user_id in getattr(Config, "ADMIN", []):
        try:
            allowed.add(int(user_id))
        except Exception:
            pass
    for user_id in getattr(Config, "PRIVATE_ALLOWED_USERS", []):
        try:
            allowed.add(int(user_id))
        except Exception:
            pass
    return allowed


def is_private_user_allowed(user_id):
    if not is_private_mode_enabled():
        return True
    try:
        return int(user_id) in get_private_allowed_users()
    except Exception:
        return False


def deny_private_user(message):
    try:
        safe_send_message(
            chat_id=message.chat.id,
            text="This is a private bot. Access is restricted.",
            message=message,
        )
    except Exception:
        pass
    return False

'''
    replace_once(
        path,
        "def create_language_keyboard():\n",
        helper + "def create_language_keyboard():\n",
    )
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
    path = APP / "web" / "dashboard_app.py"
    replace_once(
        path,
        '        public_paths = ["/login", "/api/login", "/api/reset-lockdown", "/static", "/health"]\n',
        '        public_paths = ["/login", "/api/login", "/static", "/health"]\n',
    )
    replace_once(
        path,
        '    return templates.TemplateResponse("login.html", {"request": request})\n',
        '    return templates.TemplateResponse(request, "login.html")\n',
    )
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
    if "def set_yuanbao_cookie_command(app, message):" in text:
        return
    if "import tempfile\n" not in text:
        text = text.replace("import threading\n", "import threading\nimport tempfile\n", 1)
    block = (ROOT / "scripts" / "templates" / "yuanbao_cookie_admin_block.py").read_text(encoding="utf-8")
    marker = '@app.on_message(filters.command("reload_cache") & filters.private)\n'
    if marker not in text:
        raise RuntimeError(f"Expected reload_cache marker not found in {path}")
    path.write_text(text.replace(marker, block + "\n" + marker, 1), encoding="utf-8")


def patch_yuanbao_cookie_menus() -> None:
    settings_path = APP / "COMMANDS" / "settings_cmd.py"
    settings_text = settings_path.read_text(encoding="utf-8")
    if "from HELPERS.bot_menu import YUANBAO_COOKIE_HELP\n" not in settings_text:
        settings_text = settings_text.replace(
            "from HELPERS.decorators import background_handler\n",
            "from HELPERS.decorators import background_handler\n"
            "from HELPERS.bot_menu import YUANBAO_COOKIE_HELP\n",
            1,
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
                    "更新视频号元宝 Cookie",
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
            callback_query.answer("只有管理员可以更新元宝 Cookie。", show_alert=True)
            return
        safe_send_message(
            user_id,
            YUANBAO_COOKIE_HELP,
            reply_parameters=ReplyParameters(message_id=callback_query.message.id),
        )
        callback_query.answer(safe_get_messages(user_id).SETTINGS_HINT_SENT_MSG)
        return

    # For commands that are processed only via url_distractor, create a temporary Message
'''
        if callback_marker not in settings_text:
            raise RuntimeError(f"Expected settings callback marker not found in {settings_path}")
        settings_text = settings_text.replace(callback_marker, callback_block, 1)
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
    patch_limiter()
    patch_dashboard()
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
    patch_tiktok_telegram_safe_format()
    patch_x_multi_video_posts()
    patch_x_multi_video_format_probe()
    print("Private hardening applied.")


if __name__ == "__main__":
    main()
