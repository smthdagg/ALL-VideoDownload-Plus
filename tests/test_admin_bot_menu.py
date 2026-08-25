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

    def test_registers_yuanbao_cookie_command_only_for_admin_chats(self):
        module = load_module()

        app = FakeApp([FakeBotCommand("start", "Start the bot")])

        module.register_admin_bot_commands(app, [123, "456"])

        self.assertEqual(len(app.set_calls), 6)
        global_calls = [call for call in app.set_calls if call[1] is None]
        self.assertEqual(len(global_calls), 2)
        zh_commands = next(call[0] for call in global_calls if call[2] == "zh")
        self.assertEqual(zh_commands[0].description, "开始使用 Bot")

        admin_calls = [call for call in app.set_calls if call[1] is not None]
        for commands, scope, language_code in admin_calls:
            self.assertEqual(scope.chat_id in (123, 456), True)
            descriptions = dict((item.command, item.description) for item in commands)
            self.assertEqual(language_code in ("en", "zh"), True)
            expected = "Open user management" if language_code == "en" else "打开用户管理菜单"
            self.assertEqual(descriptions["users"], expected)

    def test_replaces_an_existing_yuanbao_command_without_duplicates(self):
        module = load_module()

        app = FakeApp(
            [
                FakeBotCommand("start", "Start the bot"),
                FakeBotCommand("set_yuanbao_cookie", "Old description"),
            ]
        )

        module.register_admin_bot_commands(app, [123])

        commands, _, language_code = next(
            call for call in app.set_calls if call[1] is not None
        )
        self.assertEqual(
            [item.command for item in commands].count("set_yuanbao_cookie"),
            1,
        )
        yuanbao = next(
            item for item in commands if item.command == "set_yuanbao_cookie"
        )
        expected = "Update WeChat Channels Cookie" if language_code == "en" else "更新视频号元宝 Cookie"
        self.assertEqual(yuanbao.description, expected)


if __name__ == "__main__":
    unittest.main()
