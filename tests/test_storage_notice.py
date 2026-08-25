import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "templates" / "storage_notice.py"


def load_module():
    spec = importlib.util.spec_from_file_location("storage_notice_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StorageNoticeTest(unittest.TestCase):
    def test_classifies_warning_before_cleanup_threshold(self):
        module = load_module()

        self.assertEqual(module.classify_disk_usage(74, 75, 80), "ok")
        self.assertEqual(module.classify_disk_usage(75, 75, 80), "warning")
        self.assertEqual(module.classify_disk_usage(79.9, 75, 80), "warning")
        self.assertEqual(module.classify_disk_usage(80, 75, 80), "high")

    def test_formats_bytes_for_user_facing_messages(self):
        module = load_module()

        self.assertEqual(module.format_bytes(0), "0 B")
        self.assertEqual(module.format_bytes(1024**3), "1.0 GiB")


if __name__ == "__main__":
    unittest.main()
