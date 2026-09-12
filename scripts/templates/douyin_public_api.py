"""Small, cookie-free public Douyin detail resolver.

The fallback only requests public item metadata. It never loads or forwards
the bot user's Cookie. The signing shape follows Douyin's web X-Bogus flow.
"""

from __future__ import annotations

import base64
import hashlib
import random
import re
import string
import time
from urllib.parse import urlencode


def _md5_bytes(value: bytes) -> bytes:
    return hashlib.md5(value).digest()


def _double_md5_hex(value: bytes) -> bytes:
    return _md5_bytes(bytes.fromhex(hashlib.md5(value).hexdigest()))


def _rc4(key: bytes, data: bytes) -> bytes:
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) & 255
        state[i], state[j] = state[j], state[i]
    out = bytearray()
    i = j = 0
    for byte in data:
        i = (i + 1) & 255
        j = (j + state[i]) & 255
        state[i], state[j] = state[j], state[i]
        out.append(byte ^ state[(state[i] + state[j]) & 255])
    return bytes(out)


def build_x_bogus(url: str, user_agent: str) -> str:
    """Generate the short-lived X-Bogus query value for a GET request."""
    alphabet = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
    ua_digest = _md5_bytes(base64.b64encode(_rc4(b"\x00\x01\x0c", user_agent.encode())))
    empty_digest = _double_md5_hex(bytes.fromhex("d41d8cd98f00b204e9800998ecf8427e"))
    url_digest = _double_md5_hex(url.encode())
    now = int(time.time())
    values = [
        64, 0, 1, 12, url_digest[-2], url_digest[-1], empty_digest[-2], empty_digest[-1],
        ua_digest[-2], ua_digest[-1], (now >> 24) & 255, (now >> 16) & 255,
        (now >> 8) & 255, now & 255, 32, 0, 190, 144,
    ]
    checksum = 0
    for value in values:
        checksum ^= value
    values.append(checksum)
    first = values[::2]
    second = values[1::2]
    merged = first + second
    ordered = [
        merged[0], merged[10], merged[1], merged[11], merged[2], merged[12],
        merged[3], merged[13], merged[4], merged[14], merged[5], merged[15],
        merged[6], merged[16], merged[7], merged[17], merged[8], merged[18], merged[9],
    ]
    encrypted = _rc4(b"\xff", bytes(ordered))
    raw = b"\x02\xff" + encrypted
    encoded = "".join(
        alphabet[(raw[index] << 16 | raw[index + 1] << 8 | raw[index + 2]) >> shift & 63]
        for index in range(0, len(raw) - 2, 3)
        for shift in (18, 12, 6, 0)
    )
    return encoded


def random_ms_token() -> str:
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(182)) + "=="


def build_detail_url(aweme_id: str, user_agent: str, ms_token: str | None = None) -> str:
    params = {
        "device_platform": "webapp",
        "aid": "6383",
        "channel": "channel_pc_web",
        "update_version_code": "170400",
        "pc_client_type": "1",
        "version_code": "290100",
        "version_name": "29.1.0",
        "cookie_enabled": "true",
        "screen_width": "1536",
        "screen_height": "864",
        "browser_language": "zh-CN",
        "browser_platform": "Win32",
        "browser_name": "Chrome",
        "browser_version": "139.0.0.0",
        "platform": "PC",
        "downlink": "10",
        "effective_type": "4g",
        "round_trip_time": "200",
        "support_h265": "1",
        "support_dash": "1",
        "uifid": "",
        "msToken": ms_token or random_ms_token(),
        "aweme_id": aweme_id,
    }
    query = urlencode(params)
    endpoint = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?{query}"
    return f"{endpoint}&X-Bogus={build_x_bogus(endpoint, user_agent)}"


def extract_ms_token_from_response(response) -> str | None:
    try:
        token = response.cookies.get("msToken")
        if token:
            return str(token)
    except Exception:
        pass
    header = str(getattr(response, "headers", {}).get("set-cookie", ""))
    match = re.search(r'(?:^|[,; ])msToken=([^;," ]+)', header)
    return match.group(1) if match else None
