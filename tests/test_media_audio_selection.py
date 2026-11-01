import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'scripts/templates/truthful_format_menu.py'
spec = importlib.util.spec_from_file_location('audio_format_contract', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MediaAudioSelectionTest(unittest.TestCase):
    def test_default_audio_accepts_muxed_video(self):
        for value in (None, '', 'ba', 'bestaudio'):
            self.assertEqual(module.audio_format_selector(value), 'ba/b')

    def test_explicit_audio_format_is_preserved(self):
        self.assertEqual(module.audio_format_selector('140'), '140')
        self.assertEqual(module.audio_format_selector('bestaudio[ext=m4a]'), 'bestaudio[ext=m4a]')
