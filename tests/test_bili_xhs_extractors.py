import importlib.util
import sys
import types
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXTRACTORS = ROOT / 'patches/tg-ytdlp-bot/yt_dlp_plugins/extractor'


class ExtractorError(Exception):
    def __init__(self, message, **kwargs):
        super().__init__(message)


def load(name):
    common = types.ModuleType('yt_dlp.extractor.common')
    common.InfoExtractor = type('InfoExtractor', (), {})
    utils = types.ModuleType('yt_dlp.utils')
    utils.ExtractorError = ExtractorError
    modules = {'yt_dlp': types.ModuleType('yt_dlp'), 'yt_dlp.extractor': types.ModuleType('yt_dlp.extractor'),
               'yt_dlp.extractor.common': common, 'yt_dlp.utils': utils}
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(name, EXTRACTORS / f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class ExtractorTest(unittest.TestCase):
    def test_bili_short_and_web_urls_and_untrusted_domains(self):
        import re
        pattern = load('bili_share').BiliShareIE._VALID_URL
        for url in ('https://b23.tv/abc123', 'https://www.bilibili.com/video/BV1abcdefgh2?p=2',
                    'https://m.bilibili.com/video/BV1abcdefgh2', 'https://www.bilibili.com/video/av123456'):
            self.assertIsNotNone(re.match(pattern, url), url)
        self.assertIsNone(re.match(pattern, 'https://b23.tv.evil.test/abc123'))

    def test_dash_formats_are_separate_real_streams(self):
        module = load('bili_share')
        formats = module.dash_formats({'video': [{'id': 32, 'baseUrl': 'https://cdn.example/v', 'height': 480}],
                                       'audio': [{'id': 30280, 'baseUrl': 'https://cdn.example/a'}]})
        self.assertEqual([(item['format_id'], item.get('height'), item.get('acodec'), item.get('vcodec'))
                          for item in formats], [('video-32-0', 480, 'none', None), ('audio-30280-0', None, None, 'none')])

    def test_rejects_short_link_redirect_to_other_hosts(self):
        module = load('bili_share')
        extractor = module.BiliShareIE()
        extractor.get_param = lambda _: None
        opener = types.SimpleNamespace(open=lambda *args, **kwargs: (_ for _ in ()).throw(
            urllib.error.HTTPError('https://b23.tv/test', 302, 'redirect',
                                   {'Location': 'https://bilibili.com.evil.test/video/BVabcdef'}, None)))
        with patch.object(module.urllib.request, 'build_opener', return_value=opener):
            with self.assertRaises(ExtractorError):
                extractor._real_extract('https://b23.tv/test')

    def test_xhs_short_links_and_image_posts_not_video_formats(self):
        import re
        module = load('xhs_share')
        for url in ('https://xhslink.cn/o/abc123', 'https://xhslink.com/a/abc123',
                    'https://www.xiaohongshu.com/explore/abcdef0123456789abcdef01'):
            self.assertIsNotNone(re.match(module.XiaoHongShuShareIE._VALID_URL, url))
        self.assertIsNone(re.match(module.XiaoHongShuShareIE._VALID_URL, 'https://xhslink.cn.evil.test/o/abc123'))
        with self.assertRaises(ExtractorError):
            module.video_urls({'作品类型': '图文', '下载地址': ['https://example.com/image.jpg']})
        self.assertEqual(module.video_urls({'作品类型': '视频', '下载地址': ['https://example.com/video.mp4']}),
                         ['https://example.com/video.mp4'])
        with self.assertRaises(ExtractorError):
            module.video_urls({'作品类型': '视频', '下载地址': []})


if __name__ == '__main__':
    unittest.main()
