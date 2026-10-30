"""Validate and atomically merge per-user platform cookies without exposing values."""
import http.cookiejar
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import warnings

PLATFORMS = {
    'yuanbao': ('视频号（元宝）', ('yuanbao.tencent.com', 'tencent.com', 'qq.com')),
    'douyin': ('抖音', ('douyin.com', 'iesdouyin.com', 'bytedance.com')),
    'bilibili': ('B站', ('bilibili.com', 'biliapi.com', 'biliapi.net', 'bilivideo.com')),
    'xiaohongshu': ('小红书', ('xiaohongshu.com', 'xhslink.com')),
    'youtube': ('YouTube', ('youtube.com', 'google.com')),
    'tiktok': ('TikTok', ('tiktok.com',)),
    'instagram': ('Instagram', ('instagram.com',)),
    'twitter': ('X / Twitter', ('x.com', 'twitter.com')),
}
MAX_BYTES = 100 * 1024
_LOCK = threading.RLock()


def platform_for(domain):
    host = domain.lower().lstrip('.')
    for key, (_, domains) in PLATFORMS.items():
        if any(host == d or host.endswith('.' + d) for d in domains):
            return key
    return None


def parse_cookies(raw, selected='auto', now=None):
    if selected != 'auto' and selected not in PLATFORMS:
        raise ValueError('请选择菜单中的平台。')
    if len(raw) > MAX_BYTES:
        raise ValueError('文件超过100KB，请只导出需要的网站。')
    try:
        content = raw.decode('utf-8-sig')
    except UnicodeError:
        raise ValueError('请上传UTF-8编码的Cookie TXT文件。') from None
    jar = http.cookiejar.MozillaCookieJar()
    if not content.startswith(('# Netscape HTTP Cookie File', '# HTTP Cookie File')):
        raise ValueError('请导出Netscape格式的cookies.txt，不能上传普通文本或网页。')
    lines = []
    for line in content.splitlines():
        if line.startswith('#HttpOnly_'):
            line = line[len('#HttpOnly_'):]
        fields = line.split('\t')
        if len(fields) == 7 and fields[4] == '0':
            fields[4] = ''  # Browser exports use zero for session cookies.
            line = '\t'.join(fields)
        lines.append(line)
    content = '\n'.join(lines) + '\n'
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            jar._really_load(io.StringIO(content), 'uploaded.txt', True, True)
    except (http.cookiejar.LoadError, ValueError):
        raise ValueError('Cookie文件格式有误，请重新导出Netscape格式。') from None
    now = time.time() if now is None else now
    accepted, expired = [], 0
    for cookie in jar:
        key = platform_for(cookie.domain)
        if not key or (selected != 'auto' and key != selected):
            continue
        if cookie.expires is not None and cookie.expires <= now:
            expired += 1
            continue
        if not cookie.name or not cookie.value or any(c in cookie.name + cookie.value for c in '\r\n\t'):
            raise ValueError('Cookie记录无效，请重新导出。')
        accepted.append(cookie)
    if not accepted:
        raise ValueError('该平台Cookie均已过期，请登录后重新导出。' if expired else '文件没有所选平台的Cookie，请核对平台或选择自动识别。')
    return accepted, expired


def cookie_path(user_id, root=Path('users')):
    value = int(user_id)
    if value <= 0:
        raise ValueError('无效用户。')
    return Path(root) / str(value) / 'cookie.txt'


def import_cookies(user_id, raw, selected='auto', root=Path('users')):
    cookies, expired = parse_cookies(raw, selected)
    touched = {platform_for(c.domain) for c in cookies}
    path = cookie_path(user_id, root)
    with _LOCK:
        jar = http.cookiejar.MozillaCookieJar(str(path))
        if path.exists():
            try:
                jar.load(ignore_discard=True, ignore_expires=True)
            except (OSError, http.cookiejar.LoadError):
                raise ValueError('现有Cookie文件无法读取，已保留原文件，请管理员检查。') from None
        # Replace only imported platforms. Never retain stale auth alongside new auth.
        for c in list(jar):
            if platform_for(c.domain) in touched:
                jar.clear(c.domain, c.path, c.name)
        for c in cookies:
            jar.set_cookie(c)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, temporary = tempfile.mkstemp(prefix='.cookie-import-', dir=path.parent)
        os.close(fd)
        try:
            jar.save(temporary, ignore_discard=True, ignore_expires=True)
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        meta_path = path.with_name('cookie-import.json')
        try:
            metadata = json.loads(meta_path.read_text())
        except (OSError, ValueError):
            metadata = {}
        stamp = int(time.time())
        for key in touched:
            metadata[key] = {'updated_at': stamp, 'count': sum(platform_for(c.domain) == key for c in cookies)}
        fd, temp_meta = tempfile.mkstemp(prefix='.cookie-status-', dir=path.parent)
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(metadata, f)
            os.chmod(temp_meta, 0o600)
            os.replace(temp_meta, meta_path)
        finally:
            Path(temp_meta).unlink(missing_ok=True)
    return {'platforms': sorted(touched), 'count': len(cookies), 'expired_skipped': expired}


def yuanbao_cookie_header(user_id, root=Path('users')):
    if user_id is None:
        return ''
    path = cookie_path(user_id, root)
    jar = http.cookiejar.MozillaCookieJar(str(path))
    try:
        jar.load(ignore_discard=True, ignore_expires=False)
    except (OSError, http.cookiejar.LoadError):
        return ''
    return '; '.join(c.name + '=' + c.value for c in jar if platform_for(c.domain) == 'yuanbao')


def import_status(user_id, root=Path('users')):
    path = cookie_path(user_id, root).with_name('cookie-import.json')
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
