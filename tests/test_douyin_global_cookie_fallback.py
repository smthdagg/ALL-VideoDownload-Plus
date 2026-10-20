import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


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

    spec = importlib.util.spec_from_file_location("douyin_api_global_cookie_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RESULT = {"id": "123", "url": "https://media.example/video.mp4"}


class DouyinGlobalCookieFallbackTest(unittest.TestCase):
    def test_global_cookie_is_tried_when_user_cookie_is_missing(self):
        module = load_douyin_api_module()
        calls = []
        global_path = Path("/fixture/global-cookie.txt")

        def fake_fetch(source_url, cookie_path=None):
            calls.append(cookie_path)
            return RESULT if cookie_path == global_path else None

        with patch.object(module, "_fetch_mobile_share_page", side_effect=fake_fetch), \
                patch.object(module, "_user_cookie_path", return_value=None), \
                patch.object(module, "_global_cookie_path", return_value=global_path):
            result = module.fetch_douyin_video("https://www.douyin.com/video/123", user_id=123)
        self.assertEqual(result, RESULT)
        self.assertEqual(calls, [global_path])

    def test_anonymous_attempt_still_runs_when_global_cookie_is_absent(self):
        module = load_douyin_api_module()
        calls = []

        def fake_fetch(source_url, cookie_path=None):
            calls.append(cookie_path)
            return RESULT if cookie_path is None else None

        with patch.object(module, "_fetch_mobile_share_page", side_effect=fake_fetch), \
                patch.object(module, "_user_cookie_path", return_value=None), \
                patch.object(module, "_global_cookie_path", return_value=None):
            result = module.fetch_douyin_video("https://www.douyin.com/video/123", user_id=123)
        self.assertEqual(result, RESULT)
        self.assertEqual(calls, [None])

    def test_user_cookie_failure_falls_back_to_global_cookie(self):
        module = load_douyin_api_module()
        user_path = Path("/fixture/user-cookie.txt")
        global_path = Path("/fixture/global-cookie.txt")
        calls = []

        def fake_fetch(source_url, cookie_path=None):
            calls.append(cookie_path)
            return RESULT if cookie_path == global_path else None

        with patch.object(module, "_fetch_mobile_share_page", side_effect=fake_fetch), \
                patch.object(module, "_user_cookie_path", return_value=user_path), \
                patch.object(module, "_global_cookie_path", return_value=global_path):
            result = module.fetch_douyin_video("https://www.douyin.com/video/123", user_id=123)
        self.assertEqual(result, RESULT)
        self.assertEqual(calls, [user_path, global_path])

    def test_global_cookie_is_skipped_when_it_equals_user_cookie(self):
        module = load_douyin_api_module()
        same_path = Path("/fixture/cookie.txt")
        calls = []

        def fake_fetch(source_url, cookie_path=None):
            calls.append(cookie_path)
            return RESULT

        with patch.object(module, "_fetch_mobile_share_page", side_effect=fake_fetch), \
                patch.object(module, "_user_cookie_path", return_value=same_path), \
                patch.object(module, "_global_cookie_path", return_value=same_path):
            result = module.fetch_douyin_video("https://www.douyin.com/video/123", user_id=123)
        self.assertEqual(result, RESULT)
        self.assertEqual(calls, [same_path])

    def test_global_cookie_path_defaults_to_txt_cookie_file(self):
        module = load_douyin_api_module()
        with patch.object(Path, "is_file", return_value=False):
            self.assertIsNone(module._global_cookie_path())


if __name__ == "__main__":
    unittest.main()
