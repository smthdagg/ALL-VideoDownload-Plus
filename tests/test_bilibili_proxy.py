import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hardening', ROOT / 'scripts/apply-private-hardening.py')
hardening = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hardening)


class BilibiliProxyTest(unittest.TestCase):
    def test_patch_is_idempotent_and_scoped_to_bilibili(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            helper = app / 'HELPERS/proxy_helper.py'
            helper.parent.mkdir()
            helper.write_text('def add_proxy_to_ytdl_opts(ytdl_opts: dict, url: str, user_id: int = None) -> dict:\n    return ytdl_opts\n')
            with patch.object(hardening, 'APP', app):
                hardening.patch_bilibili_proxy()
                hardening.patch_bilibili_proxy()
            source = helper.read_text()
            compile(source, str(helper), 'exec')
            ns = {'os': __import__('os')}
            exec(source, ns)
            with patch.dict('os.environ', {'BILIBILI_PROXY_URL': 'http://localhost:8888'}):
                self.assertEqual(ns['add_proxy_to_ytdl_opts']({}, 'https://b23.tv/abc')['proxy'], 'http://localhost:8888')
                self.assertEqual(ns['add_proxy_to_ytdl_opts']({}, 'https://www.bilibili.com/video/BV123')['proxy'], 'http://localhost:8888')
                self.assertEqual(ns['add_proxy_to_ytdl_opts']({}, 'https://b23.tv.evil.test/a'), {})


if __name__ == '__main__':
    unittest.main()
