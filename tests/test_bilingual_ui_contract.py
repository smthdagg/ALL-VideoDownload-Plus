import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "scripts" / "templates"


class BilingualUiContractTest(unittest.TestCase):
    def test_web_surfaces_expose_chinese_and_english_switches(self):
        login = (TEMPLATES / "dashboard_login.html").read_text(encoding="utf-8")
        users = (TEMPLATES / "private_users_admin.html").read_text(encoding="utf-8")
        users_js = (TEMPLATES / "private-users.js").read_text(encoding="utf-8")
        dashboard_zh = (TEMPLATES / "dashboard_zh_translations.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('data-login-language="zh"', login)
        self.assertIn('data-login-language="en"', login)
        self.assertIn('data-ui-language="zh"', users)
        self.assertIn('data-ui-language="en"', users)
        self.assertIn('localStorage.getItem("adminLanguage")', users_js)
        self.assertIn('"errors.operation": "操作失败', dashboard_zh)

    def test_bot_surfaces_include_language_and_cookie_guides(self):
        private_i18n = (TEMPLATES / "private_i18n.py").read_text(encoding="utf-8")
        chinese_messages = (TEMPLATES / "messages_ZH.py").read_text(encoding="utf-8")
        bot_menu = (TEMPLATES / "bot_menu.py").read_text(encoding="utf-8")

        self.assertIn('"language_changed": "界面语言已切换为中文。"', private_i18n)
        self.assertIn("https://yuanbao.tencent.com/", private_i18n)
        self.assertIn("ALL VideoDownload Plus 使用向导", chinese_messages)
        self.assertIn("ALL VideoDownload Plus", (TEMPLATES / "messages_EN_overrides.py").read_text(encoding="utf-8"))
        self.assertIn("COMMON_COMMAND_DESCRIPTIONS_ZH", bot_menu)


if __name__ == "__main__":
    unittest.main()
