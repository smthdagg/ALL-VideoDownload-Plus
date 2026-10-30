import importlib.util
from pathlib import Path
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]

def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/templates'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

RAW=b'# Netscape HTTP Cookie File\n.bilibili.com\tTRUE\t/\tTRUE\t0\tSESSDATA\tfixture-only\n'

class CookieImportUITest(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        prior=os.getcwd();os.chdir(self.directory.name);self.addCleanup(os.chdir,prior)
        self.store=load('store_ui_test','cookie_store.py')
        self.cache=types.SimpleNamespace(clear_cookie_cache=Mock(),clear_youtube_cookie_cache=Mock(),reset_checked_cookie_sources=Mock())
        self.mods=patch.dict(sys.modules,{'HELPERS.cookie_store':self.store,'HELPERS.limitter':types.SimpleNamespace(is_private_user_allowed=lambda uid:uid==123),'HELPERS.private_i18n':types.SimpleNamespace(user_language=lambda _: 'zh'),'COMMANDS.cookies_cmd':self.cache,'pyrogram.types':types.SimpleNamespace(InlineKeyboardMarkup=lambda rows:rows,InlineKeyboardButton=lambda text,callback_data:types.SimpleNamespace(text=text,callback_data=callback_data))})
        self.mods.start();self.addCleanup(self.mods.stop)
        self.ui=load('ui_test','cookie_import_ui.py')
        self.app=Mock()
        self.app.download_media.side_effect=lambda message,file_name:Path(file_name).write_bytes(RAW)
        self.message=types.SimpleNamespace(chat=types.SimpleNamespace(id=123),from_user=types.SimpleNamespace(id=123),document=types.SimpleNamespace(file_name='../../cookies.txt',file_size=len(RAW)))

    def test_menu_selection_then_document_is_one_step(self):
        query=types.SimpleNamespace(from_user=self.message.from_user,message=self.message,data='cookie_import|bilibili',answer=Mock())
        self.ui.cookie_import_callback(self.app,query)
        self.assertTrue(self.ui.handle_cookie_document(self.app,self.message))
        self.assertIn('fixture-only',self.store.cookie_path(123).read_text())
        self.assertNotIn('fixture-only',str(self.app.send_message.call_args_list))
        self.assertFalse(Path('cookies.txt').exists())
        self.cache.clear_cookie_cache.assert_called_once_with(123)
        self.assertNotIn(123,self.ui._pending)

    def test_direct_txt_auto_detects_and_stores(self):
        self.ui.handle_cookie_document(self.app,self.message)
        self.assertEqual(self.store.import_status(123)['bilibili']['count'],1)

    def test_unauthorized_upload_is_not_downloaded(self):
        self.message.chat.id=999;self.message.from_user.id=999
        self.assertTrue(self.ui.handle_cookie_document(self.app,self.message))
        self.app.download_media.assert_not_called()

    def test_failed_file_preserves_pending_selection(self):
        self.ui._pending[123]=('douyin',self.ui.time.monotonic()+30)
        self.ui.handle_cookie_document(self.app,self.message)
        self.assertFalse(self.store.cookie_path(123).exists())
        self.assertIn(123,self.ui._pending)

    def test_expired_selection_requests_new_choice(self):
        self.ui._pending[123]=('douyin',self.ui.time.monotonic()-1)
        self.ui.handle_cookie_document(self.app,self.message)
        self.app.download_media.assert_not_called()
        self.assertNotIn(123,self.ui._pending)
