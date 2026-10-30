import ast
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]

class WechatDownloadGuardTest(unittest.TestCase):
    def run_guard(self, info):
        tree = ast.parse((ROOT / 'vendor/tg-ytdlp-bot/DOWN_AND_UP/down_and_up.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'down_and_up')
        branch = next(n for n in fn.body if isinstance(n, ast.If) and ast.unparse(n.test) == 'is_wechat_channels_url(url)')
        test_fn = ast.FunctionDef(name='check', args=ast.parse('def check(url, cached_video_info, force_no_title): pass').body[0].args, body=[branch, ast.Return(ast.Constant('engine_reached'))], decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[test_fn], type_ignores=[]))
        send = Mock()
        env = dict(user_id=1, url='https://weixin.qq.com/sph/fixture', original_url='fixture', cached_video_info=None, is_wechat_channels_url=lambda _: True, fetch_wechat_channels_video=Mock(return_value=info), send_error_to_user=send, message=object(), logger=Mock())
        exec(compile(module, '<guard>', 'exec'), env)
        return env['check']('https://weixin.qq.com/sph/fixture', None, False), send

    def test_error_stops_before_download_and_escapes_message(self):
        result, send = self.run_guard({'error': 'WECHAT_CHANNELS_MEDIA_UNAVAILABLE', 'original_error': '<expired>'})
        self.assertIsNone(result)
        self.assertIn('&lt;expired&gt;', send.call_args.args[1])

    def test_missing_metadata_stops_before_download(self):
        result, send = self.run_guard(None)
        self.assertIsNone(result)
        send.assert_called_once()

    def test_valid_media_continues_to_download(self):
        result, send = self.run_guard({'url':'https://example.com/video.mp4'})
        self.assertEqual(result, 'engine_reached')
        send.assert_not_called()
