import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "bot_menu.py"


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

    def set_bot_commands(self, commands, scope=None):
        self.set_calls.append((commands, scope))


class AdminBotMenuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pyrogram = types.ModuleType("pyrogram")
        pyrogram_types = types.ModuleType("pyrogram.types")
        pyrogram_types.BotCommand = FakeBotCommand
        pyrogram_types.BotCommandScopeChat = FakeBotCommandScopeChat
        sys.modules.setdefault("pyrogram", pyrogram)
        sys.modules.setdefault("pyrogram.types", pyrogram_types)

    def test_registers_yuanbao_cookie_command_only_for_admin_chats(self):
        module = load_module()

        app = FakeApp([FakeBotCommand("start", "Start the bot")])

        module.register_admin_bot_commands(app, [123, "456"])

        self.assertEqual(len(app.set_calls), 2)
        for commands, scope in app.set_calls:
            self.assertEqual(scope.chat_id in (123, 456), True)
            self.assertEqual(
                [(item.command, item.description) for item in commands],
                [
                    ("start", "Start the bot"),
                    ("set_yuanbao_cookie", "更新视频号元宝 Cookie"),
                ],
            )

    def test_replaces_an_existing_yuanbao_command_without_duplicates(self):
        module = load_module()

        app = FakeApp(
            [
                FakeBotCommand("start", "Start the bot"),
                FakeBotCommand("set_yuanbao_cookie", "Old description"),
            ]
        )

        module.register_admin_bot_commands(app, [123])

        commands, _ = app.set_calls[0]
        self.assertEqual(
            [item.command for item in commands].count("set_yuanbao_cookie"),
            1,
        )
        self.assertEqual(commands[-1].description, "更新视频号元宝 Cookie")


if __name__ == "__main__":
    unittest.main()
