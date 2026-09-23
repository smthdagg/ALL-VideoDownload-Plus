import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCHER_PATH = ROOT / "scripts" / "apply-private-hardening.py"
SPEC = importlib.util.spec_from_file_location("private_hardening_under_test", PATCHER_PATH)
PATCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PATCHER)


class ReplyKeyboardPatchTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_app = PATCHER.APP
        PATCHER.APP = Path(self.temp_dir.name) / "vendor" / "tg-ytdlp-bot"
        decorators = PATCHER.APP / "HELPERS" / "decorators.py"
        decorators.parent.mkdir(parents=True)
        decorators.write_text(
            "def reply_with_keyboard(func):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        result = func(*args, **kwargs)\n"
            "        send_reply_keyboard_always(1)\n"
            "        return result\n"
            "    return wrapper\n\n\n"
            "def _extract_message_arg(args, kwargs):\n"
            "    return None\n",
            encoding="utf-8",
        )
        self.decorators = decorators

    def tearDown(self):
        PATCHER.APP = self.previous_app
        self.temp_dir.cleanup()

    def test_patch_removes_invisible_keyboard_send_and_is_idempotent(self):
        PATCHER.patch_reply_keyboard_messages()
        patched = self.decorators.read_text(encoding="utf-8")

        self.assertNotIn("send_reply_keyboard_always", patched)
        namespace = {}
        exec(compile(patched, str(self.decorators), "exec"), namespace)
        handler = lambda: "handled"
        self.assertIs(namespace["reply_with_keyboard"](handler), handler)

        PATCHER.patch_reply_keyboard_messages()
        self.assertEqual(self.decorators.read_text(encoding="utf-8"), patched)


if __name__ == "__main__":
    unittest.main()
