import importlib.util
from pathlib import Path
import tempfile
import unittest
import time
import os

spec = importlib.util.spec_from_file_location('cookie_store_test', Path(__file__).resolve().parents[1] / 'scripts/templates/cookie_store.py')
store = importlib.util.module_from_spec(spec);spec.loader.exec_module(store)

def export(*rows):
    return ('# Netscape HTTP Cookie File\n' + '\n'.join(rows) + '\n').encode()

def row(domain, name='session', value='fixture', expiry=0, http_only=False):
    return f'{"#HttpOnly_" if http_only else ""}{domain}\tTRUE\t/\tTRUE\t{expiry}\t{name}\t{value}'

class CookieStoreTest(unittest.TestCase):
    def test_merge_preserves_other_platforms_and_replaces_old_platform(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            store.import_cookies(1,export(row('.douyin.com',value='old')),root=root)
            store.import_cookies(1,export(row('.bilibili.com')),root=root)
            store.import_cookies(1,export(row('.douyin.com',name='new')),root=root)
            content=store.cookie_path(1,root).read_text()
            self.assertIn('.bilibili.com',content);self.assertIn('\tnew\t',content);self.assertNotIn('old',content)
            self.assertEqual(os.stat(store.cookie_path(1,root)).st_mode & 0o777,0o600)

    def test_http_only_yuanbao_extraction_and_user_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            store.import_cookies(1,export(row('.yuanbao.tencent.com',http_only=True),row('.douyin.com',name='douyin-secret')),root=root)
            self.assertEqual(store.yuanbao_cookie_header(1,root),'session=fixture')
            self.assertEqual(store.yuanbao_cookie_header(2,root),'')

    def test_invalid_upload_cannot_overwrite_good_file(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);store.import_cookies(1,export(row('.bilibili.com')),root=root);before=store.cookie_path(1,root).read_bytes()
            for raw,selected in [(b'invalid','auto'),(export(row('.douyin.com')),'bilibili'),(export(row('.bilibili.com',expiry=int(time.time())-1)),'auto'),(export(row('.evilbilibili.com')),'auto')]:
                with self.assertRaises(ValueError):store.import_cookies(1,raw,selected,root)
                self.assertEqual(store.cookie_path(1,root).read_bytes(),before)

    def test_multi_platform_auto_and_status(self):
        with tempfile.TemporaryDirectory() as d:
            result=store.import_cookies(7,export(row('.bilibili.com'),row('.xiaohongshu.com'),row('.yuanbao.tencent.com')),root=Path(d))
            self.assertEqual(set(result['platforms']),{'bilibili','xiaohongshu','yuanbao'})
            self.assertEqual(store.import_status(7,Path(d))['yuanbao']['count'],1)
