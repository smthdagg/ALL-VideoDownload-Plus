import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "bot_menu.py"
I18N_PATH = ROOT / "scripts" / "templates" / "private_i18n.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bot_menu_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBotCommand:
    def __init__(self, command, description):
        self.command = command
        self.description = description


class FakeBotCommandScopeChat:
    def __init__(self, chat_id):
        self.chat_id = chat_id


class FakeApp:
    def __init__(self, commands):
        self.commands = commands
        self.set_calls = []

    def get_bot_commands(self):
        return self.commands

    def set_bot_commands(self, commands, scope=None, language_code=None):
        self.set_calls.append((commands, scope, language_code))


class AdminBotMenuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pyrogram = types.ModuleType("pyrogram")
        pyrogram_types = types.ModuleType("pyrogram.types")
        pyrogram_types.BotCommand = FakeBotCommand
        pyrogram_types.BotCommandScopeChat = FakeBotCommandScopeChat
        sys.modules.setdefault("pyrogram", pyrogram)
        sys.modules.setdefault("pyrogram.types", pyrogram_types)
        helpers = types.ModuleType("HELPERS")
        helpers.__path__ = []
        spec = importlib.util.spec_from_file_location("HELPERS.private_i18n", I18N_PATH)
        private_i18n = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(private_i18n)
        sys.modules.setdefault("HELPERS", helpers)
        sys.modules.setdefault("HELPERS.private_i18n", private_i18n)

    def test_registers_only_user_management_for_admin_chats(self):
        module = load_module()

        app = FakeApp([FakeBotCommand("start", "Start the bot")])

        module.register_admin_bot_commands(app, [123, "456"])

        self.assertEqual(len(app.set_calls), 9)
        global_calls = [call for call in app.set_calls if call[1] is None]
        self.assertEqual(len(global_calls), 3)
        zh_commands = next(call[0] for call in global_calls if call[2] == "zh")
        self.assertEqual(zh_commands[0].description, "开始使用 Bot")

        admin_calls = [call for call in app.set_calls if call[1] is not None]
        for commands, scope, language_code in admin_calls:
            self.assertEqual(scope.chat_id in (123, 456), True)
            descriptions = dict((item.command, item.description) for item in commands)
            self.assertEqual(language_code in (None, "en", "zh"), True)
            expected = "User management" if language_code == "en" else "用户管理"
            if language_code is None:
                expected = "User management"
            self.assertEqual(descriptions["users"], expected)

    def test_replaces_stale_commands_in_every_scope(self):
        module = load_module()
        app = FakeApp([FakeBotCommand('set_yuanbao_cookie', 'Old'), FakeBotCommand('add_user', 'Old'), FakeBotCommand('cookies_from_browser', 'Old')])
        module.register_admin_bot_commands(app, [123])
        for commands, scope, language in app.set_calls:
            names = [command.command for command in commands]
            self.assertEqual(names, ['start', 'settings', 'cookie', 'help'] + (['users'] if scope else []))
            self.assertNotIn('set_yuanbao_cookie', names)

    def test_builds_a_menu_when_telegram_has_no_existing_commands(self):
        module = load_module()
        app = FakeApp([])

        module.register_admin_bot_commands(app, [])

        default_commands = app.set_calls[0][0]
        self.assertIn("help", [item.command for item in default_commands])
        self.assertIn("settings", [item.command for item in default_commands])


if __name__ == "__main__":
    unittest.main()
