import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "tg-ytdlp-bot"
MODULE_PATH = ROOT / "scripts" / "templates" / "messages_ZH.py"


class ChineseMessagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(VENDOR))
        spec = importlib.util.spec_from_file_location(
            "CONFIG.LANGUAGES.messages_ZH_template", MODULE_PATH
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        if sys.path and sys.path[0] == str(VENDOR):
            sys.path.pop(0)

    def test_critical_user_flows_are_chinese(self):
        messages = self.module.Messages()

        for key in (
            "URL_EXTRACTOR_WELCOME_MSG",
            "HELP_MSG",
            "PROCESSING_MSG",
            "DOWNLOADING_MSG",
            "ERROR_OCCURRED_MSG",
            "SETTINGS_TITLE_MSG",
            "FORMAT_BEST_UPDATED_MSG",
            "COOKIES_ERROR_READING_MSG",
            "LANG_SELECTION_MSG",
        ):
            value = getattr(messages, key)
            self.assertTrue(any("\u4e00" <= char <= "\u9fff" for char in value), key)

    def test_inherits_complete_english_key_surface_as_fallback(self):
        from CONFIG.LANGUAGES.messages_EN import Messages as EnglishMessages

        english_keys = {
            key for key in dir(EnglishMessages()) if key.isupper() and not key.startswith("_")
        }
        chinese_keys = {
            key for key in dir(self.module.Messages()) if key.isupper() and not key.startswith("_")
        }

        self.assertEqual(english_keys - chinese_keys, set())


if __name__ == "__main__":
    unittest.main()
