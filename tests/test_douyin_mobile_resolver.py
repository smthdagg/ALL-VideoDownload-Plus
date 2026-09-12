import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "douyin_api.py"
PUBLIC_API_MODULE_PATH = ROOT / "scripts" / "templates" / "douyin_public_api.py"


def load_douyin_api_module():
    logger = types.SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
    )
    sys.modules["HELPERS"] = types.ModuleType("HELPERS")
    sys.modules["HELPERS.logger"] = types.SimpleNamespace(logger=logger)
    sys.modules["URL_PARSERS"] = types.ModuleType("URL_PARSERS")
    sys.modules["URL_PARSERS.normalizer"] = types.SimpleNamespace(normalize_douyin_url=lambda url: url)
    public_spec = importlib.util.spec_from_file_location("URL_PARSERS.douyin_public_api", PUBLIC_API_MODULE_PATH)
    public_module = importlib.util.module_from_spec(public_spec)
    public_spec.loader.exec_module(public_module)
    sys.modules["URL_PARSERS.douyin_public_api"] = public_module
    sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)

    spec = importlib.util.spec_from_file_location("douyin_api_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DouyinMobileResolverTest(unittest.TestCase):
    def test_fetches_no_watermark_link_from_iesdouyin_router_data(self):
        module = load_douyin_api_module()
        module.DOUYIN_PUBLIC_API_TOKEN_ENABLED = False

        item = {
            "desc": "sample title",
            "video": {
                "duration": 1234,
                "play_addr": {
                    "url_list": [
                        "https://aweme.snssdk.com/aweme/v1/playwm/?video_id=abc&ratio=720p",
                    ],
                },
            },
        }
        router_data = {
            "loaderData": {
                "video_(id)/page": {
                    "videoInfoRes": {
                        "item_list": [item],
                    },
                },
            },
        }
        html = f"<script>window._ROUTER_DATA = {json.dumps(router_data)}</script>"

        redirect_response = Mock()
        redirect_response.url = "https://www.iesdouyin.com/share/video/7629342687200274425/?from=share"
        redirect_response.raise_for_status.return_value = None

        page_response = Mock()
        page_response.text = html
        page_response.raise_for_status.return_value = None

        module.requests.get = Mock(side_effect=[redirect_response, page_response])

        result = module.fetch_douyin_video("2.84 复制打开抖音 https://v.douyin.com/example/ 09/14")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "7629342687200274425")
        self.assertEqual(result["title"], "sample title")
        self.assertEqual(result["formats"][0]["format_id"], "douyin-mobile")
        self.assertIn("/play/?", result["url"])
        self.assertNotIn("playwm", result["url"])

    def test_public_api_fallback_reads_aweme_detail_without_cookie(self):
        module = load_douyin_api_module()
        module.DOUYIN_PUBLIC_API_TOKEN_ENABLED = False
        payload = {
            "aweme_detail": {
                "aweme_id": "7629342687200274425",
                "desc": "public fallback",
                "video": {
                    "play_addr": {
                        "url_list": ["https://cdn.example/video.mp4?mime_type=video_mp4"]
                    }
                },
            }
        }
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        module.requests.get = Mock(return_value=response)

        result = module._fetch_public_api("https://www.douyin.com/video/7629342687200274425")

        self.assertEqual(result["formats"][0]["format_id"], "douyin-public-api")
        self.assertEqual(result["url"], "https://cdn.example/video.mp4?mime_type=video_mp4")
        request_headers = module.requests.get.call_args.kwargs["headers"]
        self.assertNotIn("Cookie", request_headers)


if __name__ == "__main__":
    unittest.main()
