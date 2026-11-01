import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "wechat_channels_api.py"


def load_module():
    logger = types.SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
    )
    sys.modules["HELPERS"] = types.ModuleType("HELPERS")
    sys.modules["HELPERS.logger"] = types.SimpleNamespace(logger=logger)
    sys.modules["requests"] = types.SimpleNamespace(post=lambda *args, **kwargs: None)

    store_spec = importlib.util.spec_from_file_location("HELPERS.cookie_store", ROOT / "scripts/templates/cookie_store.py")
    store = importlib.util.module_from_spec(store_spec)
    store_spec.loader.exec_module(store)
    sys.modules["HELPERS.cookie_store"] = store
    spec = importlib.util.spec_from_file_location("wechat_channels_api_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WeChatChannelsResolverTest(unittest.TestCase):
    def test_feed_page_url_resolves_export_id_and_token(self):
        module = load_module()
        module._post_feed_info = Mock(return_value={"data": {"feedInfo": {
            "description": "long page", "videoUrl": "https://example.com/video.mp4"
        }}})
        url = 'https://channels.weixin.qq.com/finder-preview/pages/feed?eid=example123&token=test-token'
        info = module.fetch_wechat_channels_video(url)
        self.assertEqual(info['title'], 'long page')
        self.assertEqual(info['id'], 'example123')
        self.assertEqual(module._post_feed_info.call_args.args[0], {
            'baseReq': {'generalToken': 'test-token'}, 'exportId': 'example123'
        })

    def test_feed_page_requires_trusted_host_and_export_id(self):
        module = load_module()
        self.assertFalse(module.is_wechat_channels_url('https://channels.weixin.qq.com.evil.test/finder-preview/pages/feed?eid=abc'))
        self.assertFalse(module.is_wechat_channels_url('https://channels.weixin.qq.com/finder-preview/pages/feed'))

    def test_public_short_uri_returns_ytdlp_info_when_video_url_exists(self):
        module = load_module()

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "errCode": 0,
            "data": {
                "feedInfo": {
                    "description": "sample video",
                    "coverUrl": "https://example.com/cover.jpg",
                    "videoUrl": "https://finder.video.qq.com/path/video.mp4?token=abc",
                },
            },
        }
        module.requests.post = Mock(return_value=response)

        info = module.fetch_wechat_channels_video("https://weixin.qq.com/sph/AqWPYD0Kzi")

        self.assertEqual(info["id"], "AqWPYD0Kzi")
        self.assertEqual(info["title"], "sample video")
        self.assertEqual(info["url"], "https://finder.video.qq.com/path/video.mp4?token=abc")
        self.assertEqual(info["formats"][0]["format_id"], "wechat-channels-public")

    def test_public_short_uri_returns_clear_error_when_only_preview_exists(self):
        module = load_module()

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "errCode": 0,
            "data": {
                "feedInfo": {
                    "description": "preview only",
                    "coverUrl": "https://example.com/cover.jpg",
                },
            },
        }
        module.requests.post = Mock(return_value=response)

        info = module.fetch_wechat_channels_video("https://weixin.qq.com/sph/AqWPYD0Kzi")

        self.assertEqual(info["error"], "WECHAT_CHANNELS_MEDIA_UNAVAILABLE")
        self.assertIn("预览信息", info["original_error"])


if __name__ == "__main__":
    unittest.main()

class WeChatChannelsAuthFailureTest(unittest.TestCase):
    def test_yuanbao_unauthorized_explains_refresh_without_secret(self):
        module = load_module()
        module.WECHAT_CHANNELS_YUANBAO_COOKIE = 'private-cookie'
        response = Mock(status_code=401)
        module.requests.post = Mock(return_value=response)
        info, error = module._fetch_yuanbao('https://weixin.qq.com/sph/Fixture123')
        self.assertIsNone(info)
        self.assertIn('登录态已失效', error)
        self.assertIn('/settings', error)
        self.assertNotIn('private-cookie', error)


class WeChatPersonalCookieTest(unittest.TestCase):
    def test_imported_cookie_is_used_immediately_and_isolated(self):
        import os
        import tempfile
        module = load_module()
        store = sys.modules['HELPERS.cookie_store']
        module.WECHAT_CHANNELS_YUANBAO_COOKIE = ''
        response = Mock(status_code=200)
        response.raise_for_status.return_value = None
        response.json.return_value = {'data': {}}
        module.requests.post = Mock(return_value=response)
        with tempfile.TemporaryDirectory() as directory:
            previous = os.getcwd()
            try:
                os.chdir(directory)
                for value in ['first-fixture', 'new-fixture']:
                    raw = ('# Netscape HTTP Cookie File\n.yuanbao.tencent.com\tTRUE\t/\tTRUE\t0\tlogin\t' + value + '\n').encode()
                    store.import_cookies(123, raw)
                    module._fetch_yuanbao('https://weixin.qq.com/sph/fixture', user_id=123)
                    self.assertEqual(module.requests.post.call_args.kwargs['headers']['cookie'], 'login=' + value)
                module.requests.post.reset_mock()
                module._fetch_yuanbao('https://weixin.qq.com/sph/fixture', user_id=456)
                module.requests.post.assert_not_called()
            finally:
                os.chdir(previous)
