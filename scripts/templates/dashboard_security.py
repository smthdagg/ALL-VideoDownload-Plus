from urllib.parse import urlsplit


def is_public_dashboard_path(path):
    path = str(path or "")
    return path in {"/login", "/api/login", "/health"} or path.startswith("/static/")


def _origin(value):
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    default_port = 443 if parsed.scheme == "https" else 80
    try:
        port = parsed.port or default_port
    except ValueError:
        return None
    return parsed.scheme, parsed.hostname.lower(), port


def use_secure_cookie(public_url):
    parsed = _origin(public_url)
    return bool(parsed and parsed[0] == "https")


def is_allowed_browser_origin(origin, public_url, request_base_url):
    if not origin:
        return True
    supplied = _origin(origin)
    if not supplied:
        return False
    allowed = {
        candidate
        for candidate in (_origin(public_url), _origin(request_base_url))
        if candidate
    }
    return supplied in allowed
