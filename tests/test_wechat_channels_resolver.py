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

    spec = importlib.util.spec_from_file_location("wechat_channels_api_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WeChatChannelsResolverTest(unittest.TestCase):
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
