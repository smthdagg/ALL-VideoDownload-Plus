import json
import re
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlsplit

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError

_HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bilibili.com/'}


def dash_formats(dash):
    formats = []
    for stream_type in ('video', 'audio'):
        for index, stream in enumerate(dash.get(stream_type) or []):
            url = stream.get('baseUrl') or stream.get('base_url')
            if not url:
                continue
            item = {'url': url, 'format_id': f"{stream_type}-{stream.get('id', 'unknown')}-{index}",
                    'http_headers': _HEADERS, 'ext': 'mp4' if stream_type == 'video' else 'm4a'}
            if stream_type == 'video':
                item.update({'acodec': 'none', 'height': stream.get('height'), 'width': stream.get('width'),
                             'vcodec': stream.get('codecs')})
            else:
                item.update({'vcodec': 'none', 'acodec': stream.get('codecs')})
            if stream.get('bandwidth'):
                item['tbr' if stream_type == 'video' else 'abr'] = stream['bandwidth'] / 1000
            formats.append(item)
    return formats


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class BiliShareIE(InfoExtractor):
    IE_NAME = 'bilibili:share-api'
    _VALID_URL = r'https?://(?:(?:www\.|m\.)?bilibili\.com/video/|b23\.tv/)(?P<id>[A-Za-z0-9]+)(?:[/?#]|$)'

    def _real_extract(self, url):
        parsed = urlsplit(url)
        proxy = self.get_param('proxy')
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'https': proxy} if proxy else {}), _NoRedirect())
        if parsed.hostname == 'b23.tv':
            try:
                opener.open(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15)
            except urllib.error.HTTPError as exc:
                if exc.code not in (301, 302, 303, 307, 308):
                    raise ExtractorError('B站短链接无法解析', expected=True) from exc
                parsed = urlsplit(exc.headers.get('Location', ''))
            else:
                raise ExtractorError('B站短链接未返回跳转', expected=True)
        match = re.match(r'^/video/(BV[0-9A-Za-z]+|av[0-9]+)(?:/|$)', parsed.path)
        if parsed.scheme != 'https' or parsed.hostname not in ('www.bilibili.com', 'm.bilibili.com', 'bilibili.com') or not match:
            raise ExtractorError('B站链接目标无效', expected=True)
        video_id = match.group(1)

        def api(path, query):
            request = urllib.request.Request('https://api.bilibili.com' + path + '?' + urlencode(query),
                                             headers={'User-Agent': 'curl/8.0.1'})
            with opener.open(request, timeout=20) as response:
                return json.load(response)

        response = api('/x/web-interface/view',
                       {'aid': video_id[2:]} if video_id.startswith('av') else {'bvid': video_id})
        data = response.get('data') or {}
        bvid = data.get('bvid') or (video_id if video_id.startswith('BV') else None)
        if response.get('code') != 0 or not data.get('cid') or not bvid:
            raise ExtractorError('B站作品信息不可用', expected=True)
        page_text = parse_qs(parsed.query).get('p', ['1'])[0]
        if not page_text.isdigit() or int(page_text) < 1:
            raise ExtractorError('B站分P参数无效', expected=True)
        page_num = int(page_text)
        pages = data.get('pages') or []
        if page_num > max(len(pages), 1):
            raise ExtractorError('B站分P不存在', expected=True)
        page = pages[page_num - 1] if pages else {}
        play = api('/x/player/playurl', {'bvid': bvid, 'cid': page.get('cid') or data['cid'],
                                       'qn': 80, 'fnval': 16, 'fourk': 1})
        play_data = play.get('data') or {}
        formats = dash_formats(play_data.get('dash') or {})
        if not formats:
            streams = play_data.get('durl') or []
            if len(streams) == 1 and streams[0].get('url'):
                formats = [{'url': streams[0]['url'], 'format_id': 'combined', 'ext': 'mp4',
                            'http_headers': _HEADERS}]
        if play.get('code') != 0 or not formats:
            raise ExtractorError('B站视频地址不可用', expected=True)
        return {'id': f'{bvid}_p{page_num}' if page_num > 1 else bvid,
                'title': (page.get('part') if page_num > 1 else data.get('title')) or bvid,
                'duration': page.get('duration') or data.get('duration'), 'formats': formats}
