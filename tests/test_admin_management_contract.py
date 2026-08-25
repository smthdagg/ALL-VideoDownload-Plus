import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AdminManagementContractTest(unittest.TestCase):
    def test_private_admin_commands_have_handlers(self):
        menu = (ROOT / "scripts/templates/bot_menu.py").read_text(encoding="utf-8")
        handlers = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (ROOT / "scripts/templates").glob("*.py")
        )
        admin_block = menu.split('"en": (', 1)[1].split('"zh": (', 1)[0]
        admin_commands = set(re.findall(r'\("([a-z_]+)",', admin_block))
        for command in admin_commands:
            if command in {"en", "zh"}:
                continue
            self.assertRegex(handlers, rf'command\("{re.escape(command)}"\)')

    def test_private_patch_handles_container_host_boundaries(self):
        patch = (ROOT / "scripts/apply-private-hardening.py").read_text(encoding="utf-8")
        self.assertIn("Path(__file__).resolve().parent.parent", patch)
        self.assertIn(' / "users"', patch)
        self.assertIn("Restart must be performed from the VPS host", patch)
        self.assertIn("IP rotation must be performed from the VPS host", patch)
        self.assertIn("List updates must be run from the deployment host", patch)

    def test_runtime_cleanup_and_dashboard_operations_are_documented(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("runtime", english.lower())
        self.assertIn("Restart", english)
        self.assertIn("IP", english)
        self.assertIn("自动清理", chinese)
        self.assertIn("重启服务", chinese)
        self.assertIn("切换 IP", chinese)


if __name__ == "__main__":
    unittest.main()
