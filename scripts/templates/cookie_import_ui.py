"""One-step menu/document Cookie import; values never appear in messages or logs."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import time

from HELPERS.cookie_store import PLATFORMS, MAX_BYTES, import_cookies, import_status

_pending = {}


def _allowed(message, actor):
    from HELPERS.limitter import is_private_user_allowed
    return message.chat.id == actor and is_private_user_allowed(actor)


def _text(user_id, zh, en):
    from HELPERS.private_i18n import user_language
    return zh if user_language(user_id) == 'zh' else en


def _send(app, message, body, **kwargs):
    return app.send_message(message.chat.id, body, **kwargs)


def show_cookie_import_menu(app, message, user_id):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if not _allowed(message, user_id):
        return
    metadata = import_status(user_id)
    lines = [_text(user_id, '导入 Cookie TXT：选平台后发送文件，也可直接发送文件自动识别。\n只更新文件包含的平台，保留其他平台。', 'Import Cookie TXT: choose a platform, then send the file, or send a file for automatic detection. Other platforms are preserved.')]
    buttons = [[InlineKeyboardButton(_text(user_id, '自动识别 / 多平台', 'Auto-detect / multiple sites'), callback_data='cookie_import|auto')]]
    items = list(PLATFORMS.items())
    for index in range(0, len(items), 2):
        buttons.append([InlineKeyboardButton(label, callback_data='cookie_import|' + key) for key, (label, _) in items[index:index+2]])
    for key, (label, _) in items:
        item = metadata.get(key)
        if item:
            updated = datetime.fromtimestamp(item['updated_at'], timezone.utc).strftime('%m-%d %H:%M UTC')
            lines.append(f'{label}: {item["count"]} · {updated}')
    lines.append(_text(user_id, '支持浏览器导出的 Netscape cookies.txt，最多100KB。导入成功仅代表已保存，不代表登录态仍有效。', 'Use a browser-exported Netscape cookies.txt, up to 100KB. Import confirms storage, not a valid login.'))
    buttons.append([InlineKeyboardButton(_text(user_id, '返回设置', 'Back to Settings'), callback_data='nav|settings')])
    buttons.append([InlineKeyboardButton(_text(user_id, '取消导入', 'Cancel import'), callback_data='cookie_import|cancel')])
    _send(app, message, '\n\n'.join(lines), reply_markup=InlineKeyboardMarkup(buttons))


def cookie_import_callback(app, query):
    actor = query.from_user.id
    if not _allowed(query.message, actor):
        query.answer('请在自己的私聊中操作。', show_alert=True)
        return
    selected = query.data.split('|', 1)[1]
    query.answer()
    if selected == 'menu':
        show_cookie_import_menu(app, query.message, actor)
    elif selected == 'cancel':
        _pending.pop(actor, None)
        _send(app, query.message, _text(actor, '已取消。', 'Cancelled.'))
    elif selected == 'auto' or selected in PLATFORMS:
        _pending[actor] = (selected, time.monotonic() + 600)
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        _send(app, query.message, _text(actor, '请直接发送 Cookie .txt 文件。收到后会自动校验、保存并生效，无需再回复命令。', 'Send the Cookie .txt file now. It will be checked, saved and used automatically; no follow-up command is needed.'), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(_text(actor, '取消导入', 'Cancel import'), callback_data='cookie_import|cancel')]]))


def handle_cookie_document(app, message):
    if not getattr(message, 'from_user', None) or message.chat.id != message.from_user.id:
        return False
    user_id = message.from_user.id
    if not _allowed(message, user_id):
        return True
    document = message.document
    if not (document.file_name or '').lower().endswith('.txt') or (document.file_size or 0) > MAX_BYTES:
        _send(app, message, _text(user_id, '请上传不超过100KB的Cookie TXT文件。', 'Upload a Cookie TXT file of at most 100KB.'))
        return True
    selected, expiry = _pending.get(user_id, ('auto', 0))
    if expiry and expiry < time.monotonic():
        _pending.pop(user_id, None)
        _send(app, message, _text(user_id, '选择已超时，请重新打开Cookie导入菜单选择平台。', 'Selection expired. Open Cookie import and choose a platform again.'))
        return True
    try:
        with tempfile.TemporaryDirectory(prefix='cookie-upload-') as directory:
            # Fixed filename: never use a Telegram-supplied path on the server.
            path = Path(directory) / 'cookies.txt'
            app.download_media(message, file_name=str(path))
            with path.open('rb') as f:
                raw = f.read(MAX_BYTES + 1)
            result = import_cookies(user_id, raw, selected)
    except ValueError as exc:
        _send(app, message, str(exc))
        return True
    except Exception:
        _send(app, message, _text(user_id, '导入失败，请稍后重试；不要发送Cookie正文。', 'Import failed. Retry later; do not send Cookie values as text.'))
        return True
    _pending.pop(user_id, None)
    from COMMANDS.cookies_cmd import clear_cookie_cache, clear_youtube_cookie_cache, reset_checked_cookie_sources
    clear_cookie_cache(user_id)
    clear_youtube_cookie_cache(user_id)
    reset_checked_cookie_sources(user_id)
    labels = '、'.join(PLATFORMS[key][0] for key in result['platforms'])
    _send(app, message, _text(user_id, f'已导入并保存：{labels}，共{result["count"]}条。后续下载自动使用，无需重启。其他平台Cookie已保留。', f'Imported and saved: {labels}, {result["count"]} cookies. Future downloads use them immediately; no restart needed. Other sites are preserved.'))
    return True


def register_cookie_import(app):
    from pyrogram import filters
    app.on_callback_query(filters.regex(r'^cookie_import\|'))(cookie_import_callback)
