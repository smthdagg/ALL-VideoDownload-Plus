# XiaoHongShu extractor plugin for yt-dlp (2026-10-23)
# 优先: 分享页 __INITIAL_STATE__ 解析(高画质, 需 iPhone UA + xsec_token)
# 兜底: XHS-Downloader API (compose 服务 xhs-downloader:5556, 无 cookie 低分辨率)
import json
import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError

_MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
_API = "http://xhs-downloader:5556/xhs/detail"


def video_urls(data):
    kind = data.get("作品类型")
    if kind and kind not in ("视频", "video"):
        raise ExtractorError("该小红书作品是图文，不是视频", expected=True)
    urls = data.get("下载地址") or []
    if not urls:
        raise ExtractorError("小红书没有返回视频地址", expected=True)
    # The service provides media items, not alternate qualities.
    return urls[:1]


class XiaoHongShuShareIE(InfoExtractor):
    IE_NAME = "xiaohongshu:share"
    _VALID_URL = r"https?://(?:(?:www\.)?xiaohongshu\.com/(?:discovery/item|explore)/|(?:www\.)?xhslink\.(?:cn|com)/(?:o|a)/)(?P<id>[a-zA-Z0-9]{5,32})"
    _TESTS = []

    def _real_extract(self, url):
        note_id = self._match_id(url)
        if re.match(r"https?://(?:www\.)?xhslink\.(?:cn|com)/", url):
            return self._from_api(url, note_id)
        try:
            return self._from_page(url, note_id)
        except Exception:
            self.to_screen("page parse failed, falling back to XHS-Downloader API")
        return self._from_api(url, note_id)

    def _from_page(self, url, note_id):
        webpage = self._download_webpage(url, note_id, headers={"User-Agent": _MOBILE_UA})
        m = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})</script>", webpage, re.S)
        if not m:
            self.raise_no_formats("page without __INITIAL_STATE__", expected=False)
        raw = re.sub(r":\s*undefined", ":null", m.group(1)).replace("\\u002F", "/")
        try:
            note = (json.loads(raw).get("noteData", {}).get("data", {}).get("noteData", {}) or {})
        except json.JSONDecodeError as e:
            self.raise_no_formats(f"state parse error: {e}", expected=False)
        if not note:
            self.raise_no_formats("note not found (token 过期或需登录)", expected=True)
        real_id = note.get("noteId", note_id)
        title = (note.get("title") or (note.get("desc") or "小红书")[:60]).strip() or "小红书"
        uploader = (note.get("user") or {}).get("nickname") or None
        formats = []
        media = ((note.get("video") or {}).get("media") or {})
        for variant in ("h264", "h265", "av1"):
            for st in ((media.get("stream") or {}).get(variant)) or []:
                u = st.get("masterUrl")
                if not u:
                    continue
                vm = st.get("videoMeta") or {}
                formats.append({"url": u, "ext": "mp4", "format_id": variant,
                                "height": vm.get("height"), "width": vm.get("width"),
                                "filesize": vm.get("size"), "protocol": "https",
                                "http_headers": {"User-Agent": _MOBILE_UA}})
        if not formats:
            raise ValueError("no formats on page")
        return {"id": real_id, "title": title, "formats": formats, "uploader": uploader}

    def _from_api(self, url, note_id):
        import urllib.request
        req = urllib.request.Request(
            _API, data=json.dumps({"url": url}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        data = (json.loads(urllib.request.urlopen(req, timeout=30).read().decode()) or {}).get("data") or {}
        urls = video_urls(data)
        title = (data.get("作品标题") or "小红书")[:80]
        formats = [{"url": u, "ext": "mp4", "format_id": f"api-{i}",
                    "protocol": "https", "http_headers": {"User-Agent": _MOBILE_UA}}
                   for i, u in enumerate(urls, 1)]
        return {"id": data.get("作品ID", note_id), "title": title, "formats": formats,
                "uploader": data.get("作者昵称") or None,
                "thumbnail": data.get("封面地址") or None}
