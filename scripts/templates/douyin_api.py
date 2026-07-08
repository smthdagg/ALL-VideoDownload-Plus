from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote, urlparse

import requests

from HELPERS.logger import logger
from URL_PARSERS.normalizer import normalize_douyin_url


DOUYIN_API_BASE_URL = os.getenv("DOUYIN_API_BASE_URL", "http://douyin-api")
DOUYIN_API_TIMEOUT = int(os.getenv("DOUYIN_API_TIMEOUT", "35"))
DOUYIN_REMOTE_RESOLVER_URL = os.getenv("DOUYIN_REMOTE_RESOLVER_URL", "").strip()
DOUYIN_REMOTE_RESOLVER_METHOD = os.getenv("DOUYIN_REMOTE_RESOLVER_METHOD", "GET").upper()
DOUYIN_REMOTE_RESOLVER_HEADERS_JSON = os.getenv("DOUYIN_REMOTE_RESOLVER_HEADERS_JSON", "").strip()
DOUYIN_REQABLE_CAPTURE_DIR = os.getenv("DOUYIN_REQABLE_CAPTURE_DIR", "/reqable-capture").strip()
DOUYIN_REQABLE_CAPTURE_MAX_AGE_SECONDS = int(os.getenv("DOUYIN_REQABLE_CAPTURE_MAX_AGE_SECONDS", "3600"))
DOUYIN_REQABLE_CAPTURE_ENABLED = os.getenv("DOUYIN_REQABLE_CAPTURE_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
DOUYIN_REQABLE_CAPTURE_FIRST = os.getenv("DOUYIN_REQABLE_CAPTURE_FIRST", "0").strip().lower() in {"1", "true", "yes", "on"}
DOUYIN_MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
}
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
    parsed = urlparse((_extract_first_url(url) or url).strip())
    host = parsed.netloc.lower()
    return host in DOUYIN_ALLOWED_HOSTS or host.endswith(".douyin.com") or host.endswith(".iesdouyin.com")


def extract_douyin_aweme_id(url: str) -> str | None:
    parsed = urlparse(_extract_first_url(url) or url)
    for pattern in (r"/video/(\d+)", r"/share/video/(\d+)"):
        match = re.search(pattern, parsed.path)
        if match:
            return match.group(1)
    return None


def _extract_first_url(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    match = re.search(r"https?://[^\s\"'<>\\]+", text)
    if not match:
        return None
    return match.group(0).rstrip(").,;")


def _pick_url(*candidates):
    for candidate in candidates:
        if _looks_like_media_url(candidate):
            return candidate
    return None


def _looks_like_media_url(value) -> bool:
    if not isinstance(value, str) or not value.startswith(("http://", "https://")):
        return False
    lowered = value.lower()
    if "douyin.com/video/" in lowered or "iesdouyin.com/share/video/" in lowered:
        return False
    media_markers = (".mp4", ".m3u8", "video_id=", "play/?", "playwm/?", "mime_type=video")
    return any(marker in lowered for marker in media_markers)


def _first_cover(cover_data):
    if not isinstance(cover_data, dict):
        return None
    for key in ("cover", "origin_cover", "dynamic_cover", "thumbnail"):
        value = cover_data.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            url_list = value.get("url_list")
            if isinstance(url_list, list) and url_list:
                return url_list[0]
    return None


def _find_first_media_url(value):
    if _looks_like_media_url(value):
        return value
    if isinstance(value, dict):
        preferred_keys = (
            "nwm_video_url_HQ",
            "nwm_video_url",
            "no_watermark",
            "play",
            "play_addr",
            "video_url",
            "download_url",
            "url",
            "wm_video_url_HQ",
            "wm_video_url",
        )
        for key in preferred_keys:
            found = _find_first_media_url(value.get(key))
            if found:
                return found
        for nested in value.values():
            found = _find_first_media_url(nested)
            if found:
                return found
    if isinstance(value, list):
        for nested in value:
            found = _find_first_media_url(nested)
            if found:
                return found
    return None


def _find_first_media_url_in_text(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    for match in re.finditer(r"https?://[^\s\"'<>\\]+", text):
        candidate = match.group(0).rstrip(").,;")
        candidate = candidate.replace("\\/", "/")
        if _looks_like_media_url(candidate):
            return candidate
    return None


def _find_title(value):
    if isinstance(value, dict):
        for key in ("desc", "title", "text", "caption", "description"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for nested in value.values():
            found = _find_title(nested)
            if found:
                return found
    if isinstance(value, list):
        for nested in value:
            found = _find_title(nested)
            if found:
                return found
    return None


def _as_ytdlp_info(source_url: str, data: dict, direct_url: str, source: str = "douyin-api") -> dict:
    video_id = data.get("video_id") or data.get("aweme_id") or extract_douyin_aweme_id(source_url) or "douyin"
    title = data.get("desc") or data.get("title") or _find_title(data) or f"douyin-{video_id}"
    duration = data.get("duration")
    video_format = {
        "format_id": source,
        "format": source,
        "url": direct_url,
        "ext": "mp4",
        "protocol": "https",
        "vcodec": "h264",
        "acodec": "aac",
    }
    info = {
        "id": str(video_id),
        "title": title,
        "description": data.get("desc") or data.get("description"),
        "webpage_url": source_url,
        "original_url": source_url,
        "url": direct_url,
        "ext": "mp4",
        "duration": duration,
        "thumbnail": _first_cover(data.get("cover_data") or data.get("cover") or {}),
        "formats": [video_format],
        "requested_formats": [video_format],
    }
    return {key: value for key, value in info.items() if value is not None}


def _remote_headers() -> dict:
    if not DOUYIN_REMOTE_RESOLVER_HEADERS_JSON:
        return {}
    try:
        parsed = json.loads(DOUYIN_REMOTE_RESOLVER_HEADERS_JSON)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        logger.warning(f"Invalid DOUYIN_REMOTE_RESOLVER_HEADERS_JSON: {exc}")
        return {}


def _extract_router_data(html: str) -> dict | None:
    match = re.search(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", html, re.DOTALL)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1).strip())
    except Exception as exc:
        logger.warning(f"Could not parse Douyin mobile router data: {exc}")
        return None
    return payload if isinstance(payload, dict) else None


def _extract_mobile_video_info(router_data: dict) -> dict | None:
    loader_data = router_data.get("loaderData")
    if not isinstance(loader_data, dict):
        return None

    for page_key in ("video_(id)/page", "note_(id)/page"):
        page_data = loader_data.get(page_key)
        if not isinstance(page_data, dict):
            continue
        video_info = page_data.get("videoInfoRes")
        item_list = video_info.get("item_list") if isinstance(video_info, dict) else None
        if isinstance(item_list, list) and item_list:
            first_item = item_list[0]
            return first_item if isinstance(first_item, dict) else None
    return None


def _pick_mobile_video_url(item: dict) -> str | None:
    video = item.get("video")
    if not isinstance(video, dict):
        return None

    preferred = (
        video.get("play_addr"),
        video.get("download_addr"),
        video.get("play_addr_lowbr"),
    )
    for address in preferred:
        if not isinstance(address, dict):
            continue
        url_list = address.get("url_list")
        if not isinstance(url_list, list):
            continue
        for candidate in url_list:
            if not isinstance(candidate, str):
                continue
            direct_url = candidate.replace("playwm", "play")
            if _looks_like_media_url(direct_url):
                return direct_url
    return None


def _fetch_mobile_share_page(source_url: str) -> dict | None:
    first_url = _extract_first_url(source_url) or source_url
    try:
        response = requests.get(first_url, headers=DOUYIN_MOBILE_HEADERS, allow_redirects=True, timeout=DOUYIN_API_TIMEOUT)
        response.raise_for_status()
    except Exception as exc:
        logger.warning(f"Douyin mobile resolver could not resolve share URL {source_url}: {exc}")
        return None

    aweme_id = extract_douyin_aweme_id(response.url) or extract_douyin_aweme_id(first_url)
    if not aweme_id:
        logger.warning(f"Douyin mobile resolver could not find aweme id for {source_url}")
        return None

    page_url = f"https://www.iesdouyin.com/share/video/{aweme_id}"
    try:
        page_response = requests.get(page_url, headers=DOUYIN_MOBILE_HEADERS, timeout=DOUYIN_API_TIMEOUT)
        page_response.raise_for_status()
    except Exception as exc:
        logger.warning(f"Douyin mobile resolver could not fetch {page_url}: {exc}")
        return None

    router_data = _extract_router_data(page_response.text)
    if not router_data:
        logger.warning(f"Douyin mobile resolver did not find router data for {page_url}")
        return None

    item = _extract_mobile_video_info(router_data)
    if not item:
        logger.warning(f"Douyin mobile resolver did not find item data for {page_url}")
        return None

    direct_url = _pick_mobile_video_url(item)
    if not direct_url:
        logger.warning(f"Douyin mobile resolver did not find a video URL for {page_url}")
        return None

    data = {
        "video_id": aweme_id,
        "aweme_id": aweme_id,
        "desc": item.get("desc"),
        "duration": (item.get("video") or {}).get("duration"),
        "cover_data": item.get("video") or {},
        "mobile_item": item,
    }
    result = _as_ytdlp_info(source_url, data, direct_url, "douyin-mobile")
    result["douyin_mobile_data"] = data
    return result


def _fetch_local_sidecar(source_url: str) -> dict | None:
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
        logger.warning(f"Douyin local sidecar failed for {source_url}: {exc}")
        return None

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        logger.warning(f"Douyin local sidecar returned an unexpected response for {source_url}")
        return None

    if data.get("type") != "video":
        logger.warning(f"Douyin local sidecar returned non-video content for {source_url}: {data.get('type')}")
        return None

    video_data = data.get("video_data") or {}
    direct_url = _pick_url(
        video_data.get("nwm_video_url_HQ"),
        video_data.get("nwm_video_url"),
        video_data.get("wm_video_url_HQ"),
        video_data.get("wm_video_url"),
    )
    if not direct_url:
        logger.warning(f"Douyin local sidecar did not return a video URL for {source_url}")
        return None

    result = _as_ytdlp_info(source_url, data, direct_url, "douyin-api")
    result["douyin_api_data"] = data
    return result


def _fetch_remote_resolver(source_url: str) -> dict | None:
    if not DOUYIN_REMOTE_RESOLVER_URL:
        return None

    endpoint = DOUYIN_REMOTE_RESOLVER_URL
    headers = _remote_headers()
    try:
        if "{url}" in endpoint:
            response = requests.request(
                DOUYIN_REMOTE_RESOLVER_METHOD,
                endpoint.replace("{url}", quote(source_url, safe="")),
                headers=headers,
                timeout=DOUYIN_API_TIMEOUT,
            )
        elif DOUYIN_REMOTE_RESOLVER_METHOD == "POST":
            response = requests.post(endpoint, json={"url": source_url}, headers=headers, timeout=DOUYIN_API_TIMEOUT)
        else:
            response = requests.get(endpoint, params={"url": source_url}, headers=headers, timeout=DOUYIN_API_TIMEOUT)
        response.raise_for_status()
        response_text = response.text
        try:
            payload = response.json()
        except ValueError:
            payload = response_text
    except Exception as exc:
        logger.warning(f"Douyin remote resolver failed for {source_url}: {exc}")
        return None

    direct_url = _find_first_media_url(payload)
    if not direct_url and isinstance(payload, str):
        direct_url = _find_first_media_url_in_text(payload)
    if not direct_url:
        logger.warning(f"Douyin remote resolver did not return a media URL for {source_url}")
        return None

    data = payload if isinstance(payload, dict) else {"response": payload}
    result = _as_ytdlp_info(source_url, data, direct_url, "douyin-remote")
    result["douyin_remote_data"] = data
    return result


def _fetch_reqable_capture(source_url: str) -> dict | None:
    if not DOUYIN_REQABLE_CAPTURE_ENABLED:
        return None
    if not DOUYIN_REQABLE_CAPTURE_DIR:
        return None

    capture_dir = Path(DOUYIN_REQABLE_CAPTURE_DIR)
    if not capture_dir.exists():
        return None

    now = time.time()
    try:
        files = sorted(
            capture_dir.glob("*-res-extract-body.reqable"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except Exception as exc:
        logger.warning(f"Could not scan Reqable capture dir {capture_dir}: {exc}")
        return None

    for path in files[:200]:
        try:
            if DOUYIN_REQABLE_CAPTURE_MAX_AGE_SECONDS > 0 and now - path.stat().st_mtime > DOUYIN_REQABLE_CAPTURE_MAX_AGE_SECONDS:
                continue
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        if not isinstance(payload, dict) or str(payload.get("code")) != "100":
            continue
        data = payload.get("data")
        if not isinstance(data, dict):
            continue
        direct_url = _pick_url(data.get("downurl"), data.get("url2")) or _find_first_media_url(data)
        if not direct_url:
            continue

        logger.info(f"Using Reqable capture fallback from {path.name} for {source_url}")
        result = _as_ytdlp_info(source_url, data, direct_url, "douyin-reqable")
        result["douyin_reqable_data"] = data
        return result

    return None


def fetch_douyin_video(url: str) -> dict | None:
    if not is_douyin_url(url):
        return None

    source_url = normalize_douyin_url(_extract_first_url(url) or url)
    if not is_douyin_url(source_url):
        logger.warning(f"Douyin API rejected non-Douyin URL after normalization: {source_url}")
        return None

    if DOUYIN_REQABLE_CAPTURE_ENABLED and DOUYIN_REQABLE_CAPTURE_FIRST:
        return _fetch_reqable_capture(source_url) or _fetch_local_sidecar(source_url) or _fetch_remote_resolver(source_url)
    return _fetch_mobile_share_page(source_url) or _fetch_local_sidecar(source_url) or _fetch_remote_resolver(source_url) or _fetch_reqable_capture(source_url)
