"""Bound cookie-source fallback and isolate yt-dlp's writable cookie jars."""
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
import shutil
import tempfile

_active = ContextVar('active_cookie_fallbacks', default=frozenset())


def bounded_cookie_fallback(function):
    @wraps(function)
    def guarded(user_id, url, *args, **kwargs):
        key = (user_id, url)
        active = _active.get()
        if key in active:
            return None
        token = _active.set(active | {key})
        try:
            return function(user_id, url, *args, **kwargs)
        finally:
            _active.reset(token)
    return guarded


def call_with_cookie_source(download_func, args, cookie_path):
    if not args or not isinstance(args[0], dict):
        return download_func(*args)
    options = dict(args[0])
    options.pop('cookiesfrombrowser', None)
    if cookie_path is None:
        options.pop('cookiefile', None)
        return download_func(options, *args[1:])
    # YoutubeDL writes its cookie jar on close. Never let an anonymous fallback
    # overwrite the uploaded personalized jar or the shared global jar.
    with tempfile.TemporaryDirectory(prefix='cookie-source-') as directory:
        temporary = Path(directory) / 'cookie.txt'
        shutil.copyfile(cookie_path, temporary)
        temporary.chmod(0o600)
        options['cookiefile'] = str(temporary)
        return download_func(options, *args[1:])
