import ast
import importlib.util
import pathlib
import tempfile
import types
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]

class CookieFallbackGuardTests(unittest.TestCase):
    def load(self):
        path=ROOT/'scripts/templates/cookie_fallback_guard.py'
        spec=importlib.util.spec_from_file_location('guard_under_test',path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_recursion_is_bounded_and_context_resets_after_failure(self):
        guard=self.load()
        calls=[]
        @guard.bounded_cookie_fallback
        def fallback(user_id,url):
            calls.append((user_id,url))
            self.assertIsNone(fallback(user_id,url))
            raise RuntimeError('failed source')
        for _ in range(2):
            with self.assertRaises(RuntimeError):fallback(1,'https://www.douyin.com/video/123')
        self.assertEqual(len(calls),2)

    def test_options_rotate_without_mutating_personal_cookie_file(self):
        guard=self.load()
        with tempfile.TemporaryDirectory() as td:
            cookie=pathlib.Path(td)/'cookie.txt';cookie.write_text('PERSONAL')
            opts={'cookiefile':'previous','format':'best'}
            def operation(candidate):
                self.assertNotEqual(candidate['cookiefile'],str(cookie))
                self.assertEqual(pathlib.Path(candidate['cookiefile']).read_text(),'PERSONAL')
                pathlib.Path(candidate['cookiefile']).write_text('anonymous update')
                return 42
            self.assertEqual(guard.call_with_cookie_source(operation,(opts,),str(cookie)),42)
            self.assertEqual(cookie.read_text(),'PERSONAL')
            self.assertEqual(opts['cookiefile'],'previous')
            result=guard.call_with_cookie_source(lambda candidate:candidate,(opts,),None)
            self.assertNotIn('cookiefile',result)
            self.assertEqual(opts['cookiefile'],'previous')

    def test_real_fallback_attempts_each_source_once(self):
        guard=self.load()
        source=(ROOT/'vendor/tg-ytdlp-bot/COMMANDS/cookies_cmd.py').read_text()
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='try_non_youtube_cookie_fallback')
        with tempfile.TemporaryDirectory() as td:
            import os
            # Absolute fixtures avoid changing the process working directory.
            user=pathlib.Path(td)/'users/1';user.mkdir(parents=True)
            (user/'cookie.txt').write_text('USER')
            global_cookie=pathlib.Path(td)/'global.txt';global_cookie.write_text('GLOBAL')
            fake_os=types.SimpleNamespace(path=types.SimpleNamespace(join=lambda *a:str(pathlib.Path(td).joinpath(*a)),exists=os.path.exists),remove=os.remove)
            env={'bounded_cookie_fallback':guard.bounded_cookie_fallback,'call_with_cookie_source':guard.call_with_cookie_source,
                 'Config':types.SimpleNamespace(COOKIE_FILE_PATH=str(global_cookie)),'os':fake_os,
                 'logger':types.SimpleNamespace(info=lambda *a:None,warning=lambda *a:None,error=lambda *a:None),
                 'cleanup_expired_tasks':lambda:None,'start_cookie_task':lambda *a:'task','finish_cookie_task':lambda *a:None,
                 'get_service_name_from_url':lambda u:None}
            with patch.dict(sys.modules,{'CONFIG.limits':types.SimpleNamespace(LimitsConfig=object)}):
                exec(compile(ast.Module(body=[node],type_ignores=[]),'fallback','exec'),env)
                attempts=[]
                def download(opts):
                    path=opts.get('cookiefile')
                    attempts.append(pathlib.Path(path).read_text() if path else None)
                    env['try_non_youtube_cookie_fallback'](1,'https://www.douyin.com/video/123',download,opts)
                    raise RuntimeError('fresh cookies needed')
                self.assertIsNone(env['try_non_youtube_cookie_fallback'](1,'https://www.douyin.com/video/123',download,{'cookiefile':'old'}))
                self.assertEqual(attempts,['USER','GLOBAL',None])

    def test_generated_douyin_probe_has_single_resolver_call(self):
        tree=ast.parse((ROOT/'vendor/tg-ytdlp-bot/DOWN_AND_UP/yt_dlp_hook.py').read_text())
        func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get_video_formats')
        calls=[n for n in ast.walk(func) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='fetch_douyin_video']
        self.assertEqual(len(calls),1)
