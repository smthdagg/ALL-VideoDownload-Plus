import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_USERS_PATH = ROOT / "scripts" / "templates" / "private_users.py"
SERVICE_PATH = ROOT / "scripts" / "templates" / "private_users_web_service.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrivateUsersWebServiceTest(unittest.TestCase):
    def setUp(self):
        self.private_users = load_module("private_users_for_web_test", PRIVATE_USERS_PATH)
        helpers = types.ModuleType("HELPERS")
        self.previous_helpers = sys.modules.get("HELPERS")
        self.previous_private_users = sys.modules.get("HELPERS.private_users")
        sys.modules["HELPERS"] = helpers
        sys.modules["HELPERS.private_users"] = self.private_users
        self.service_module = load_module("private_users_web_service_under_test", SERVICE_PATH)
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = self.private_users.PrivateUserStore(
            Path(self.tempdir.name) / "private_users.json"
        )
        self.service = self.service_module.PrivateUsersWebService(
            store=self.store,
            admin_ids=[9001],
            static_user_ids=[8001],
        )

    def tearDown(self):
        self.tempdir.cleanup()
        if self.previous_helpers is None:
            sys.modules.pop("HELPERS", None)
        else:
            sys.modules["HELPERS"] = self.previous_helpers
        if self.previous_private_users is None:
            sys.modules.pop("HELPERS.private_users", None)
        else:
            sys.modules["HELPERS.private_users"] = self.previous_private_users

    def test_snapshot_combines_every_access_state(self):
        self.store.add(7001, added_by=9001)
        self.store.submit_request(
            7002,
            {"first_name": "Pending", "username": "pending_user"},
        )
        self.store.blacklist(7003, reviewed_by=9001, reason="spam")

        snapshot = self.service.snapshot()

        self.assertEqual(snapshot["counts"], {
            "admins": 1,
            "static": 1,
            "allowed": 1,
            "pending": 1,
            "blacklisted": 1,
        })
        self.assertEqual(snapshot["admins"][0]["user_id"], 9001)
        self.assertEqual(snapshot["static_users"][0]["user_id"], 8001)
        self.assertEqual(snapshot["allowed_users"][0]["user_id"], 7001)
        self.assertEqual(snapshot["pending_requests"][0]["username"], "pending_user")
        self.assertEqual(snapshot["blacklisted_users"][0]["reason"], "spam")

    def test_add_remove_and_blacklist_dynamic_user(self):
        self.assertEqual(self.service.add(7001), "added")
        self.assertEqual(self.service.add(7001), "already_allowed")
        self.assertEqual(self.service.remove(7001), "removed")
        self.assertEqual(self.service.remove(7001), "not_dynamic")

        self.assertEqual(self.service.blacklist(7001, "abuse"), "blacklisted")
        self.assertEqual(self.service.add(7001), "blacklisted")
        self.assertEqual(self.service.unblacklist(7001), "unblacklisted")

    def test_approve_and_reject_pending_requests(self):
        self.store.submit_request(7001, {"first_name": "Allowed"})
        self.store.submit_request(7002, {"first_name": "Rejected"})

        self.assertEqual(self.service.approve(7001), "approved")
        self.assertEqual(self.service.reject(7002), "rejected")
        self.assertEqual(self.service.approve(7002), "not_pending")

    def test_admins_are_protected_from_removal_and_blacklisting(self):
        self.assertEqual(self.service.remove(9001), "protected")
        self.assertEqual(self.service.blacklist(9001), "protected")

    def test_static_users_cannot_be_removed_but_blacklist_overrides_access(self):
        self.assertEqual(self.service.remove(8001), "protected")
        self.assertEqual(self.service.blacklist(8001), "blacklisted")

        snapshot = self.service.snapshot()
        self.assertEqual(snapshot["static_users"], [])
        self.assertEqual(snapshot["blacklisted_users"][0]["user_id"], 8001)

        self.assertEqual(self.service.unblacklist(8001), "unblacklisted")
        self.assertEqual(self.service.snapshot()["static_users"][0]["user_id"], 8001)

    def test_rejects_invalid_ids_and_long_reasons(self):
        with self.assertRaises(ValueError):
            self.service.add("not-an-id")
        with self.assertRaises(ValueError):
            self.service.blacklist(7001, "x" * 201)


if __name__ == "__main__":
    unittest.main()
