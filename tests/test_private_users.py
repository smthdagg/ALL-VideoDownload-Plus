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


if __name__ == "__main__":
    unittest.main()
