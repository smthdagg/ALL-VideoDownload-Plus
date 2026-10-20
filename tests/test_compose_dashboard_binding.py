import importlib.util
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "apply-private-hardening.py"
GENERATED_COMPOSE = ROOT / "vendor" / "tg-ytdlp-bot" / "docker-compose.yml"


def load_generator_module():
    spec = importlib.util.spec_from_file_location("apply_private_hardening_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ComposeDashboardBindingTest(unittest.TestCase):
    def setUp(self):
        if not GENERATED_COMPOSE.is_file():
            self.skipTest("vendor compose has not been generated yet")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app_dir = Path(self.tmp.name)
        shutil.copyfile(GENERATED_COMPOSE, self.app_dir / "docker-compose.yml")

    def read_compose(self):
        return (self.app_dir / "docker-compose.yml").read_text(encoding="utf-8")

    def test_default_run_keeps_standard_binding_and_is_idempotent(self):
        module = load_generator_module()
        with patch.object(module, "APP", self.app_dir):
            module.patch_compose()
            first = self.read_compose()
            self.assertIn('      - "80:80"', first)
            module.patch_compose()
            self.assertEqual(self.read_compose(), first)

    def test_custom_binding_drift_is_normalized_not_fatal(self):
        module = load_generator_module()
        customized = self.read_compose().replace('      - "80:80"', '      - "127.0.0.1:8880:80"')
        (self.app_dir / "docker-compose.yml").write_text(customized, encoding="utf-8")
        env = {"VPS_DASHBOARD_HTTP_BINDING": "127.0.0.1:8880:80"}
        with patch.object(module, "APP", self.app_dir), patch.dict(os.environ, env):
            module.patch_compose()
        result = self.read_compose()
        self.assertIn('      - "127.0.0.1:8880:80"', result)
        self.assertIn('      - "8443:443"', result)
        self.assertEqual(result, customized)
        with patch.object(module, "APP", self.app_dir), patch.dict(os.environ, env):
            module.patch_compose()
        self.assertEqual(self.read_compose(), customized)

    def test_binding_change_is_reapplied_on_rerun(self):
        module = load_generator_module()
        customized = self.read_compose().replace('      - "80:80"', '      - "127.0.0.1:8880:80"')
        (self.app_dir / "docker-compose.yml").write_text(customized, encoding="utf-8")
        with patch.object(module, "APP", self.app_dir), patch.dict(os.environ, {"VPS_DASHBOARD_HTTP_BINDING": "127.0.0.1:7777:80"}):
            module.patch_compose()
        self.assertIn('      - "127.0.0.1:7777:80"', self.read_compose())
        self.assertNotIn('      - "127.0.0.1:8880:80"', self.read_compose())


if __name__ == "__main__":
    unittest.main()
