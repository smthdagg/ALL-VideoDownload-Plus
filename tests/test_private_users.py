import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "private_users.py"


def load_module():
    spec = importlib.util.spec_from_file_location("private_users_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrivateUserStoreTest(unittest.TestCase):
    def test_dashboard_url_requires_clean_https_url(self):
        module = load_module()

        self.assertEqual(
            module.build_dashboard_admin_url("https://bot.example.com"),
            "https://bot.example.com/admin/users",
        )
        self.assertEqual(
            module.build_dashboard_admin_url("https://bot.example.com/base/"),
            "https://bot.example.com/base/admin/users",
        )
        for value in (
            "",
            "http://bot.example.com",
            "https://user:pass@bot.example.com",
            "https://bot.example.com?token=secret",
            "javascript:alert(1)",
        ):
            with self.subTest(value=value):
                self.assertIsNone(module.build_dashboard_admin_url(value))

    def test_add_remove_and_reload_users(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "private_users.json"
            store = module.PrivateUserStore(path)

            self.assertTrue(store.add(123, added_by=999))
            self.assertFalse(store.add("123", added_by=999))
            self.assertEqual(store.list_ids(), {123})

            reloaded = module.PrivateUserStore(path)
            self.assertEqual(reloaded.list_ids(), {123})
            self.assertTrue(reloaded.remove(123))
            self.assertFalse(reloaded.remove(123))
            self.assertEqual(reloaded.list_ids(), set())

    def test_rejects_invalid_telegram_user_ids(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")

            for value in (None, "", "abc", 0, -1, True):
                with self.assertRaises(ValueError):
                    store.add(value, added_by=999)

    def test_persists_valid_json_with_metadata(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "private_users.json"
            store = module.PrivateUserStore(path)

            store.add(456, added_by=999)

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["users"]["456"]["added_by"], 999)
            self.assertIn("added_at", payload["users"]["456"])

    def test_combines_admin_static_and_dynamic_users(self):
        module = load_module()

        allowed = module.collect_allowed_user_ids(
            admin_ids=[1, "2"],
            static_user_ids=[3, "bad"],
            dynamic_user_ids={4},
        )

        self.assertEqual(allowed, {1, 2, 3, 4})

    def test_access_request_can_be_approved(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")

            state = store.submit_request(
                123,
                {"first_name": "Henry", "username": "henry"},
            )

            self.assertEqual(state, "created")
            self.assertEqual(store.submit_request(123, {}), "pending")
            self.assertEqual(store.list_pending_requests()[123]["username"], "henry")
            self.assertTrue(store.approve(123, reviewed_by=999))
            self.assertEqual(store.list_ids(), {123})
            self.assertEqual(store.list_pending_requests(), {})

    def test_rejected_request_cannot_immediately_spam_admin_again(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")

            store.submit_request(456, {"first_name": "Rejected"})
            self.assertTrue(store.reject(456, reviewed_by=999))

            self.assertEqual(store.submit_request(456, {}), "rejected")
            self.assertEqual(store.list_pending_requests(), {})

    def test_manual_add_clears_a_pending_request(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")
            store.submit_request(789, {"first_name": "Pending"})

            store.add(789, added_by=999)

            self.assertEqual(store.list_ids(), {789})
            self.assertEqual(store.list_pending_requests(), {})

    def test_permanent_blacklist_revokes_access_and_blocks_requests(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")
            store.add(321, added_by=999)

            self.assertTrue(store.blacklist(321, reviewed_by=999, reason="abuse"))

            self.assertNotIn(321, store.list_ids())
            self.assertTrue(store.is_blacklisted(321))
            self.assertEqual(store.submit_request(321, {}), "blacklisted")
            self.assertEqual(store.list_pending_requests(), {})

    def test_unblacklist_allows_a_new_request(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")
            store.blacklist(654, reviewed_by=999)

            self.assertTrue(store.unblacklist(654))

            self.assertFalse(store.is_blacklisted(654))
            self.assertEqual(store.submit_request(654, {}), "created")

    def test_blacklisting_a_pending_request_removes_it(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = module.PrivateUserStore(Path(tmpdir) / "private_users.json")
            store.submit_request(987, {"first_name": "Abusive"})

            store.blacklist(987, reviewed_by=999)

            self.assertEqual(store.list_pending_requests(), {})
            self.assertFalse(store.approve(987, reviewed_by=999))

    def test_access_request_button_uses_the_expected_callback(self):
        module = load_module()

        class Button:
            def __init__(self, text, callback_data):
                self.text = text
                self.callback_data = callback_data

        class Markup:
            def __init__(self, rows):
                self.inline_keyboard = rows

        import sys
        import types

        pyrogram = types.ModuleType("pyrogram")
        pyrogram_types = types.ModuleType("pyrogram.types")
        pyrogram_types.InlineKeyboardButton = Button
        pyrogram_types.InlineKeyboardMarkup = Markup
        previous_pyrogram = sys.modules.get("pyrogram")
        previous_types = sys.modules.get("pyrogram.types")
        sys.modules["pyrogram"] = pyrogram
        sys.modules["pyrogram.types"] = pyrogram_types
        try:
            markup = module.build_access_request_markup()
        finally:
            if previous_pyrogram is None:
                sys.modules.pop("pyrogram", None)
            else:
                sys.modules["pyrogram"] = previous_pyrogram
            if previous_types is None:
                sys.modules.pop("pyrogram.types", None)
            else:
                sys.modules["pyrogram.types"] = previous_types

        button = markup.inline_keyboard[0][0]
        self.assertEqual(button.text, "Apply for access")
        self.assertEqual(button.callback_data, "private_users|request")


if __name__ == "__main__":
    unittest.main()
