import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "platform_runtime.py"


def load_platform_runtime():
    spec = importlib.util.spec_from_file_location("platform_runtime_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlatformRuntimeTest(unittest.TestCase):
    def test_non_youtube_cookie_retry_is_single_shot(self):
        module = load_platform_runtime()

        self.assertTrue(module.should_retry_non_youtube_cookie("HTTP Error 401 Unauthorized", False))
        self.assertFalse(module.should_retry_non_youtube_cookie("HTTP Error 401 Unauthorized", True))
        self.assertFalse(module.should_retry_non_youtube_cookie("Unsupported URL", False))

    def test_instagram_extraction_errors_use_gallery_fallback(self):
        module = load_platform_runtime()

        self.assertTrue(module.should_use_instagram_gallery_fallback("No video formats found"))
        self.assertTrue(
            module.should_use_instagram_gallery_fallback(
                "This content isn't available to everyone: It can't be seen by certain audiences."
            )
        )
        self.assertFalse(module.should_use_instagram_gallery_fallback("Network timeout"))

    def test_direct_media_resolver_reuses_cached_result(self):
        module = load_platform_runtime()
        calls = []
        cached = {"url": "https://cdn.example/video.mp4", "title": "cached"}

        result = module.resolve_direct_media(
            "https://v.douyin.com/example/",
            cached,
            lambda url: calls.append(url),
        )

        self.assertEqual(result, cached)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
