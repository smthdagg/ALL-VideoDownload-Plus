import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "private_i18n.py"


def load_module():
    spec = importlib.util.spec_from_file_location("private_i18n_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRouter:
    def __init__(self, language=None):
        self.language = language
        self.set_calls = []

    def get_user_language(self, user_id):
        return self.language or "en"

    def set_user_language(self, user_id, language):
        self.language = language
        self.set_calls.append((user_id, language))
        return True


class PrivateI18nTest(unittest.TestCase):
    def test_normalizes_telegram_language_codes_to_english_or_chinese(self):
        module = load_module()

        for value in ("zh", "zh-cn", "zh-Hans", "ZH_TW"):
            self.assertEqual(module.normalize_language(value), "zh")
        for value in (None, "", "en", "en-US", "de"):
            self.assertEqual(module.normalize_language(value), "en")

    def test_first_contact_uses_telegram_language_and_persists_it(self):
        module = load_module()
        router = FakeRouter()
        with tempfile.TemporaryDirectory() as tmpdir:
            language = module.ensure_user_language(
                123,
                "zh-CN",
                router=router,
                users_root=Path(tmpdir),
            )

        self.assertEqual(language, "zh")
        self.assertEqual(router.set_calls, [(123, "zh")])

    def test_existing_language_choice_is_not_overwritten(self):
        module = load_module()
        router = FakeRouter("en")
        with tempfile.TemporaryDirectory() as tmpdir:
            user_dir = Path(tmpdir) / "123"
            user_dir.mkdir()
            (user_dir / "lang.txt").write_text("en", encoding="utf-8")

            language = module.ensure_user_language(
                123,
                "zh-CN",
                router=router,
                users_root=Path(tmpdir),
            )

        self.assertEqual(language, "en")
        self.assertEqual(router.set_calls, [])

    def test_custom_messages_are_available_in_both_languages(self):
        module = load_module()

        self.assertEqual(module.text("language_button", language="zh"), "中文 / English")
        self.assertEqual(module.text("language_button", language="en"), "English / 中文")
        self.assertIn("视频号", module.text("yuanbao_guide", language="zh"))
        self.assertIn("WeChat Channels", module.text("yuanbao_guide", language="en"))
        self.assertEqual(
            module.text("cookie_updated", language="zh", count=3),
            "元宝 Cookie 已更新，识别到 3 个 Cookie；当前进程已刷新，重启后仍会保留。",
        )
        self.assertIn("/cookie", module.text("request_user_approved", language="zh"))
        self.assertIn("Telegram 数字 ID", module.text("request_user_approved", language="zh"))
        self.assertIn("/cookies_from_browser", module.text("request_user_approved", language="en"))
        self.assertIn("not shared", module.text("request_user_approved", language="en").lower())
        self.assertIn("磁盘", module.text("disk_warning", language="zh"))
        self.assertIn("disk", module.text("disk_warning", language="en").lower())

    def test_missing_translation_key_is_rejected_during_development(self):
        module = load_module()

        with self.assertRaises(KeyError):
            module.text("missing_key", language="en")


if __name__ == "__main__":
    unittest.main()
