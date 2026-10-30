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
    module._mint_ttwid_original = module._mint_ttwid
    module._mint_ttwid = lambda: "TTWID-FIXTURE"
    module._anonymous_cookie_cache.clear()
    return module


class DouyinMobileResolverTest(unittest.TestCase):
    def test_dtk_v5_resolver_is_opt_in_and_extracts_structured_media(self):
        module = load_douyin_api_module()
        module.DOUYIN_DTK_V5_URL = "http://dtk-v5:8000"
        module.DOUYIN_DTK_V5_API_KEY = "fixture-key"
        module.requests.post = Mock(return_value=Mock(
            status_code=200,
            json=lambda: {"data": {"content": {"videos": [{"playUrl": "https://cdn.example/video.mp4"}]}}},
        ))
        result = module._fetch_dtk_v5("https://www.douyin.com/video/123")
        self.assertEqual(result["url"], "https://cdn.example/video.mp4")
        self.assertEqual(result["formats"][0]["format_id"], "dtk-v5")
        kwargs = module.requests.post.call_args.kwargs
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer fixture-key")

    def test_dtk_v5_resolver_is_disabled_by_default(self):
        module = load_douyin_api_module()
        module.DOUYIN_DTK_V5_URL = ""
        module.requests.post = Mock()
        self.assertIsNone(module._fetch_dtk_v5("https://www.douyin.com/video/123"))
        module.requests.post.assert_not_called()

    def test_remote_resolver_headers_keep_json_contract(self):
        module = load_douyin_api_module()
        module.DOUYIN_REMOTE_RESOLVER_HEADERS_JSON = '{"X-Test": "ok"}'
        self.assertEqual(module._remote_headers(), {"X-Test": "ok"})

    def test_mobile_resolver_sends_uploaded_cookie_and_anonymous_tokens_in_header(self):
        module = load_douyin_api_module()
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            cookie_path = Path(td) / "cookie.txt"
            cookie_path.write_text("# Netscape HTTP Cookie File\n.douyin.com\tTRUE\t/\tFALSE\t2147483647\tsessionid\tPERSONAL\n.bilibili.com\tTRUE\t/\tFALSE\t2147483647\tSESSDATA\tBILI-PRIVATE\n")
            response = Mock(url="https://www.iesdouyin.com/share/video/123")
            response.text = '<script>window._ROUTER_DATA = {"loaderData":{}}</script>'
            module.requests.get = Mock(return_value=response)
            before = cookie_path.read_bytes()
            with patch.object(module, "_generate_verify_fp", return_value="verify_fixture_fixed_token"):
                module._fetch_mobile_share_page("https://www.douyin.com/video/123", cookie_path=cookie_path)
            sent = module.requests.get.call_args_list[0].kwargs['headers']['Cookie']
            self.assertIn("sessionid=PERSONAL", sent)
            self.assertNotIn("BILI-PRIVATE", sent)
            self.assertNotIn("SESSDATA", sent)
            self.assertIn("ttwid=TTWID-FIXTURE", sent)
            self.assertIn("s_v_web_id=verify_fixture_fixed_token", sent)
            self.assertIn("msToken=", sent)
            self.assertEqual(cookie_path.read_bytes(), before)

    def test_anonymous_tokens_fill_gaps_when_no_cookie_uploaded(self):
        module = load_douyin_api_module()
        from unittest.mock import patch
        response = Mock(url="https://www.iesdouyin.com/share/video/123")
        response.text = '<script>window._ROUTER_DATA = {"loaderData":{}}</script>'
        module.requests.get = Mock(return_value=response)
        with patch.object(module, "_generate_verify_fp", return_value="verify_anon_token"):
            module._fetch_mobile_share_page("https://www.douyin.com/video/123")
        sent = module.requests.get.call_args_list[0].kwargs['headers']['Cookie']
        self.assertIn("ttwid=TTWID-FIXTURE", sent)
        self.assertIn("s_v_web_id=verify_anon_token", sent)
        self.assertNotIn("sessionid", sent)

    def test_mobile_proxy_env_is_applied_to_requests(self):
        module = load_douyin_api_module()
        from unittest.mock import patch
        response = Mock(url="https://www.iesdouyin.com/share/video/123")
        response.text = '<script>window._ROUTER_DATA = {"loaderData":{}}</script>'
        module.requests.get = Mock(return_value=response)
        module.DOUYIN_MOBILE_PROXY_URL = "http://proxy.example:8888"
        try:
            module._fetch_mobile_share_page("https://www.douyin.com/video/123")
        finally:
            module.DOUYIN_MOBILE_PROXY_URL = ""
        proxies = module.requests.get.call_args_list[0].kwargs['proxies']
        self.assertEqual(proxies, {"http": "http://proxy.example:8888", "https": "http://proxy.example:8888"})

    def test_generate_verify_fp_matches_douyin_shape(self):
        module = load_douyin_api_module()
        value = module._generate_verify_fp()
        self.assertTrue(value.startswith("verify_"))
        # verify_<base36 ms>_<36-char device id with "_" at 8/13/18/23 and "4" at 14>
        device = value[-36:]
        self.assertEqual(device[8], "_")
        self.assertEqual(device[13], "_")
        self.assertEqual(device[18], "_")
        self.assertEqual(device[23], "_")
        self.assertEqual(device[14], "4")
        middle = value[len("verify_"):-36].rstrip("_")
        self.assertTrue(middle)

    def test_mint_ttwid_parses_set_cookie_header(self):
        module = load_douyin_api_module()
        module._anonymous_cookie_cache.clear()
        from unittest.mock import patch

        class FakeHeaders:
            def __init__(self):
                self._items = [("set-cookie", "ttwid=1%7CMINTED%7C123; Path=/; Domain=bytedance.com")]

            def items(self):
                return self._items

        class FakeResponse:
            headers = FakeHeaders()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with patch.object(module, "_UrlOpen", return_value=FakeResponse()), \
                patch.object(module, "_UrlRequest", Mock()):
            ttwid = module._mint_ttwid_original()
        self.assertEqual(ttwid, "1%7CMINTED%7C123")
        self.assertEqual(module._anonymous_cookie_cache["ttwid"], "1%7CMINTED%7C123")

    def test_personalized_mobile_path_is_tried_before_anonymous_resolver(self):
        module = load_douyin_api_module()
        from unittest.mock import patch
        module._fetch_mobile_share_page = Mock(return_value={'id':'123','url':'https://media.example/video.mp4'})
        with patch.object(module, '_user_cookie_path', return_value=Path('/fixture/cookie.txt')):
            result = module.fetch_douyin_video('https://www.douyin.com/video/123', user_id=123)
        self.assertEqual(result['id'], '123')
        module._fetch_mobile_share_page.assert_called_once_with('https://www.douyin.com/video/123', cookie_path=Path('/fixture/cookie.txt'))

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
        self.assertNotIn("requested_formats", result)
        self.assertAlmostEqual(result["duration"], 1.234)
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
