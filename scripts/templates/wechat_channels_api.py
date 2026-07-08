from __future__ import annotations

import json
import os
import random
import re
import time
from urllib.parse import parse_qs, quote, urlparse

import requests

from HELPERS.logger import logger


WECHAT_CHANNELS_TIMEOUT = int(os.getenv("WECHAT_CHANNELS_TIMEOUT", "30"))
WECHAT_CHANNELS_YUANBAO_COOKIE = os.getenv("WECHAT_CHANNELS_YUANBAO_COOKIE", "").strip()
WECHAT_CHANNELS_ALLOWED_HOSTS = {
    "weixin.qq.com",
    "channels.weixin.qq.com",
}
WECHAT_CHANNELS_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://channels.weixin.qq.com",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    ),
}
YUANBAO_PARSE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "content-type": "application/json",
    "origin": "https://yuanbao.tencent.com",
    "referer": "https://yuanbao.tencent.com/",
    "user-agent": WECHAT_CHANNELS_HEADERS["User-Agent"],
    "x-requested-with": "XMLHttpRequest",
    "x-source": "web",
    "x-web-third-source": "main",
    "x-platform": "mac",
    "x-language": "zh-CN",
}


def _extract_first_url(text: str) -> str | None:
    if not isinstance(text, str):
        return None
    match = re.search(r"https?://[^\s\"'<>\\]+", text)
    if not match:
        return None
    return match.group(0).rstrip(").,;")


def is_wechat_channels_url(url: str) -> bool:
    first_url = _extract_first_url(url) or url
    parsed = urlparse(first_url.strip())
    host = parsed.netloc.lower()
    if host not in WECHAT_CHANNELS_ALLOWED_HOSTS:
        return False
    return "/sph/" in parsed.path or "/finder-preview/pages/sph" in parsed.path


def _extract_short_uri(url: str) -> str | None:
    first_url = _extract_first_url(url) or url
    parsed = urlparse(first_url)
    match = re.search(r"/sph/([A-Za-z0-9]+)", parsed.path)
    if match:
        return match.group(1)
    if parsed.path.endswith("/finder-preview/pages/sph"):
        query_match = re.search(r"(?:^|[?&])id=([A-Za-z0-9]+)", first_url)
        if query_match:
            return query_match.group(1)
    return None


def _rid() -> str:
    return f"{int(time.time()):x}-{random.randrange(16**8):08x}"


def _post_feed_info(payload: dict, referer: str) -> dict | None:
    endpoint = (
        "https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info"
        f"?_rid={_rid()}&_pageUrl=https:%2F%2Fchannels.weixin.qq.com%2Ffinder-preview%2Fpages%2Fsph"
    )
    headers = dict(WECHAT_CHANNELS_HEADERS)
    headers["Referer"] = referer
    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=WECHAT_CHANNELS_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning(f"WeChat Channels feed_info failed: {exc}")
        return None


def _find_video_url(feed: dict) -> str | None:
    candidates = [
        feed.get("videoUrl"),
        feed.get("originVideoUrl"),
    ]
    for key in ("h264VideoInfo", "h265VideoInfo"):
        value = feed.get(key)
        if isinstance(value, dict):
            candidates.append(value.get("videoUrl"))
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            return candidate
    return None


def _as_ytdlp_info(source_url: str, feed: dict, direct_url: str, source: str = "wechat-channels") -> dict:
    title = feed.get("description") or "wechat-channels-video"
    video_format = {
        "format_id": source,
        "format": source,
        "url": direct_url,
        "ext": "mp4",
        "protocol": "https",
        "vcodec": "h264",
        "acodec": "aac",
    }
    return {
        "id": _extract_short_uri(source_url) or "wechat-channels",
        "title": title,
        "description": feed.get("description"),
        "webpage_url": source_url,
        "original_url": source_url,
        "url": direct_url,
        "ext": "mp4",
        "thumbnail": feed.get("coverUrl"),
        "formats": [video_format],
        "requested_formats": [video_format],
    }


def _fetch_public_short_uri(source_url: str) -> tuple[dict | None, str | None]:
    short_uri = _extract_short_uri(source_url)
    if not short_uri:
        return None, "无法识别视频号 shortUri"

    referer = f"https://channels.weixin.qq.com/finder-preview/pages/sph?id={quote(short_uri)}"
    payload = {"baseReq": {"generalToken": ""}, "shortUri": short_uri}
    result = _post_feed_info(payload, referer)
    if not isinstance(result, dict):
        return None, "视频号公开接口没有返回有效 JSON"

    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    feed = data.get("feedInfo") if isinstance(data.get("feedInfo"), dict) else {}
    direct_url = _find_video_url(feed)
    if direct_url:
        info = _as_ytdlp_info(source_url, feed, direct_url, "wechat-channels-public")
        info["wechat_channels_data"] = data
        return info, None

    title = feed.get("description")
    if title:
        return None, "公开接口只返回了预览信息，没有返回 videoUrl"
    err_msg = data.get("errMsg") if isinstance(data.get("errMsg"), dict) else {}
    if err_msg.get("title"):
        return None, str(err_msg.get("title"))
    return None, "公开接口没有返回视频媒体地址"


def _fetch_yuanbao(source_url: str) -> tuple[dict | None, str | None]:
    if not WECHAT_CHANNELS_YUANBAO_COOKIE:
        return None, "未配置 WECHAT_CHANNELS_YUANBAO_COOKIE"

    payload = {
        "type": "video_channel_url",
        "url": source_url,
        "scene": 1,
    }
    headers = dict(YUANBAO_PARSE_HEADERS)
    headers["cookie"] = WECHAT_CHANNELS_YUANBAO_COOKIE
    try:
        response = requests.post(
            "https://yuanbao.tencent.com/api/weixin/get_parse_result",
            headers=headers,
            data=json.dumps(payload),
            timeout=WECHAT_CHANNELS_TIMEOUT,
        )
        response.raise_for_status()
        parse_result = response.json()
    except Exception as exc:
        logger.warning(f"WeChat Channels Yuanbao parse failed: {exc}")
        return None, "元宝解析接口请求失败"

    parse_data = parse_result.get("data") if isinstance(parse_result, dict) else None
    if not isinstance(parse_data, dict):
        return None, "元宝解析接口没有返回 data"

    playable_url = parse_data.get("playable_url") or ""
    export_id = parse_data.get("wx_export_id") or ""
    token = ""
    if playable_url:
        parsed = urlparse(playable_url)
        query = parse_qs(parsed.query)
        token = query.get("token", [""])[0]
        export_id = query.get("eid", [export_id])[0]

    if not export_id:
        return None, "元宝解析接口没有返回 exportId"

    referer = (
        "https://channels.weixin.qq.com/finder-preview/pages/feed"
        f"?entry_card_type=48&comment_scene=39&appid=0&token={quote(token)}&entry_scene=0&eid={quote(export_id)}"
    )
    result = _post_feed_info({"baseReq": {"generalToken": token}, "exportId": export_id}, referer)
    if not isinstance(result, dict):
        return None, "视频号 feed_info 没有返回有效 JSON"

    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    feed = data.get("feedInfo") if isinstance(data.get("feedInfo"), dict) else {}
    direct_url = _find_video_url(feed)
    if not direct_url:
        return None, "元宝增强解析后仍没有返回 videoUrl"

    info = _as_ytdlp_info(source_url, feed, direct_url, "wechat-channels-yuanbao")
    info["wechat_channels_data"] = data
    info["wechat_channels_yuanbao_data"] = parse_data
    return info, None


def fetch_wechat_channels_video(url: str) -> dict | None:
    if not is_wechat_channels_url(url):
        return None

    source_url = _extract_first_url(url) or url
    info, error = _fetch_public_short_uri(source_url)
    if info:
        return info

    yuanbao_info, yuanbao_error = _fetch_yuanbao(source_url)
    if yuanbao_info:
        return yuanbao_info

    logger.warning(f"WeChat Channels resolver did not return media for {source_url}: {error}; {yuanbao_error}")
    return {
        "error": "WECHAT_CHANNELS_MEDIA_UNAVAILABLE",
        "original_error": (
            f"{error or '视频号没有返回可下载媒体地址'}。"
            f"{yuanbao_error or '元宝增强解析不可用'}。"
            "该链接可能需要微信/腾讯登录态。"
        ),
    }
