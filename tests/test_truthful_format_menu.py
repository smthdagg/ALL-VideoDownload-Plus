import importlib.util
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'scripts/templates/truthful_format_menu.py'
spec = importlib.util.spec_from_file_location('truthful_format_menu', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TruthfulFormatMenuTest(unittest.TestCase):
    def test_target_sites_do_not_offer_unverified_manual_qualities(self):
        for url in ('https://v.douyin.com/a/', 'https://b23.tv/a',
                    'https://www.bilibili.com/video/BVabc', 'https://xhslink.cn/o/a',
                    'https://www.xiaohongshu.com/explore/a',
                    'https://weixin.qq.com/sph/a'):
            with self.subTest(url=url):
                self.assertFalse(module.allow_manual_qualities(url))

    def test_exact_hostname_matching(self):
        self.assertTrue(module.allow_manual_qualities('https://b23.tv.evil.test/x'))
        self.assertTrue(module.allow_manual_qualities('https://example.com/x'))
        self.assertTrue(module.allow_manual_qualities('not a URL'))

    def test_patch_hides_both_unverified_manual_quality_entries(self):
        path = PATH.parents[1] / 'apply-private-hardening.py'
        loader = importlib.util.spec_from_file_location('hardening_quality', path)
        hardening = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(hardening)
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            (app / 'HELPERS').mkdir()
            (app / 'DOWN_AND_UP').mkdir()
            menu = app / 'DOWN_AND_UP/always_ask_menu.py'
            audio = app / 'DOWN_AND_UP/down_and_audio.py'
            (app / 'DOWN_AND_UP/down_and_up.py').write_text(
                'def download(url, quality_key, format_override):\n'
                '    # Reset the checked cookie-source cache for a new download task\n'
                '    pass\n')
            audio.write_text('def test(url, cached_video_info, user_id, original_url, format_override):\n'
                '    if url:\n'
                '        if url:\n'
                '            logger.info(f"Using Douyin API direct media URL for audio download: {original_url}")\n'
                "    download_format = format_override if format_override else 'ba'\n"
                "    download_format = format_override if format_override else 'ba'\n")
            menu.write_text('def test(url, buttons, user_id, other_label):\n'
                '        buttons.append(InlineKeyboardButton(other_label, callback_data=f"askq|other_qualities"))\n'
                '        buttons.append(InlineKeyboardButton(safe_get_messages(user_id).ALWAYS_ASK_OTHER_LABEL_MSG, callback_data=f"askq|other_qualities"))\n'
                '        # --- Forming caption ---\n'
                '        cap = f"<b>{title}</b>\\n"\n'
                '        for quality_key in quality_order:\n'
                '            if quality_key in cached_qualities:\n'
                '                pass\n'
                'def download():\n'
                '    if True:\n'
                '            cmd.append(url)\n'
                '            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)\n'
                '    fmt = f"{video_format_id}+{audio_format_id}/bv+ba/best"\n'
                '    fmt = f"{selected_format.get(\'format_id\', \'\')}+bestaudio/bv+ba/best"\n'
                '    down_and_up(app, message, url, playlist_name, video_count, video_start_with, tags_text, force_no_title=is_tiktok, format_override=fmt, quality_key=quality_key, cookies_already_checked=True, cached_video_info=info)\n')
            with patch.object(hardening, 'APP', app):
                hardening.patch_truthful_format_menu()
                hardening.patch_truthful_format_menu()
            result = menu.read_text()
            self.assertEqual(result.count('callback_data=f"askq|other_qualities"'), 2)
            self.assertIn('quality_key == "mp3" or allow_manual_qualities(url)', result)
            self.assertEqual(result.count('fmt = strict_quality_selector(url, quality_key, fmt)'), 1)
            self.assertIn('video_format_id if not allow_manual_qualities(url)', result)
            self.assertIn('add_proxy_to_ytdl_opts({}, url, user_id)', result)
            compile(result, str(menu), 'exec')
            self.assertEqual(audio.read_text().count('audio_format_selector(format_override)'), 2)
            self.assertIn('if is_wechat_channels_url(url):', audio.read_text())
            compile(audio.read_text(), str(audio), 'exec')

    def test_quality_selection_must_not_fall_back_to_another_quality(self):
        url = 'https://b23.tv/example'
        self.assertEqual(module.strict_quality_selector(url, '480p', 'video480+audio/best'), 'video480+audio')
        self.assertEqual(module.strict_quality_selector(url, 'best', 'video+audio/best'), 'video+audio/best')
        self.assertEqual(module.strict_quality_selector('https://example.com', '480p', 'video480+audio/best'), 'video480+audio/best')
