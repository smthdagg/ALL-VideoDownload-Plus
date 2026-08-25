from __future__ import annotations

import time
from urllib.parse import urlparse

import yt_dlp


_PATCHED = False
_RETRYABLE_ERRORS = (
    "universal data for rehydration",
    "unable to extract webpage video data",
    "unexpected response from webpage request",
)


def _is_tiktok_url(url: object) -> bool:
    if not isinstance(url, str):
        return False
    host = (urlparse(url).hostname or "").lower()
    return host == "tiktok.com" or host.endswith(".tiktok.com")


def _is_retryable(error: Exception) -> bool:
    message = str(error).lower()
    return any(fragment in message for fragment in _RETRYABLE_ERRORS)


def apply_tiktok_retry_patch(max_attempts: int = 4) -> None:
    global _PATCHED
    if _PATCHED:
        return

    original_extract_info = yt_dlp.YoutubeDL.extract_info

    def extract_info_with_tiktok_retry(self, url, *args, **kwargs):
        if not _is_tiktok_url(url):
            return original_extract_info(self, url, *args, **kwargs)

        for attempt in range(1, max_attempts + 1):
            try:
                return original_extract_info(self, url, *args, **kwargs)
            except yt_dlp.utils.DownloadError as error:
                if attempt >= max_attempts or not _is_retryable(error):
                    raise
                self.write_debug(
                    f"TikTok challenge failed on attempt {attempt}; retrying extraction"
                )
                time.sleep(attempt)

        raise RuntimeError("Unreachable TikTok retry state")

    yt_dlp.YoutubeDL.extract_info = extract_info_with_tiktok_retry
    _PATCHED = True
