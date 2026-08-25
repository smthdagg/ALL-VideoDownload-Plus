from __future__ import annotations


_COOKIE_ERROR_MARKERS = (
    "cookie",
    "auth",
    "login",
    "sign in",
    "403",
    "401",
    "forbidden",
    "unauthorized",
)

_INSTAGRAM_GALLERY_MARKERS = (
    "no video formats found",
    "no media found",
    "this content isn't available",
    "it can't be seen by certain audiences",
)


def should_retry_non_youtube_cookie(error_text: str, already_retried: bool) -> bool:
    """Allow one cookie rotation for authentication failures, never recursive retries."""
    if already_retried:
        return False
    lowered = (error_text or "").lower()
    return any(marker in lowered for marker in _COOKIE_ERROR_MARKERS)


def should_use_instagram_gallery_fallback(error_text: str) -> bool:
    """Identify Instagram extraction failures that gallery-dl may still handle."""
    lowered = (error_text or "").lower()
    return any(marker in lowered for marker in _INSTAGRAM_GALLERY_MARKERS)


def resolve_direct_media(source_url: str, cached_info: dict | None, resolver) -> dict | None:
    """Reuse format-probe metadata before making another resolver request."""
    if isinstance(cached_info, dict) and cached_info.get("url"):
        return cached_info
    result = resolver(source_url)
    return result if isinstance(result, dict) and result.get("url") else None
