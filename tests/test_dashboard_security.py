import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "dashboard_security.py"


def load_module():
    spec = importlib.util.spec_from_file_location("dashboard_security_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DashboardSecurityTest(unittest.TestCase):
    def test_only_exact_public_routes_and_static_files_bypass_login(self):
        module = load_module()

        for path in ("/login", "/api/login", "/health", "/static/app.css"):
            self.assertTrue(module.is_public_dashboard_path(path))
        for path in ("/", "/admin/users", "/login-extra", "/static-private"):
            self.assertFalse(module.is_public_dashboard_path(path))

    def test_cookie_is_secure_only_for_https_public_dashboard(self):
        module = load_module()

        self.assertTrue(module.use_secure_cookie("https://bot.example.com"))
        self.assertFalse(module.use_secure_cookie("http://127.0.0.1:5555"))
        self.assertFalse(module.use_secure_cookie(""))

    def test_same_origin_accepts_matching_browser_origin(self):
        module = load_module()

        self.assertTrue(
            module.is_allowed_browser_origin(
                "https://bot.example.com",
                "https://bot.example.com",
                "http://app:5555",
            )
        )
        self.assertTrue(
            module.is_allowed_browser_origin(
                None,
                "",
                "http://127.0.0.1:5555",
            )
        )

    def test_same_origin_rejects_cross_site_and_malformed_origins(self):
        module = load_module()

        self.assertFalse(
            module.is_allowed_browser_origin(
                "https://attacker.example",
                "https://bot.example.com",
                "http://app:5555",
            )
        )
        self.assertFalse(
            module.is_allowed_browser_origin(
                "not-a-url",
                "https://bot.example.com",
                "http://app:5555",
            )
        )


if __name__ == "__main__":
    unittest.main()
