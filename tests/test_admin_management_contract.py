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

    def test_runtime_dependencies_are_kept_on_supported_versions(self):
        patch = (ROOT / "scripts/apply-private-hardening.py").read_text(encoding="utf-8")
        self.assertIn("FROM python:3.12-slim", patch)
        self.assertIn("brainicism/bgutil-ytdlp-pot-provider:1.3.2", patch)
        self.assertIn('      - "80:80"', patch)
        self.assertIn('      - "8443:443"', patch)
        self.assertIn("bgutil-ytdlp-pot-provider==1.3.2", patch)
        self.assertIn("yt-dlp[default,curl-cffi]==2026.8.19", patch)
        self.assertIn('text.replace("--pre\\n", "", 1)', patch)
        self.assertIn('text.replace("moviepy==1.0.3\\n", "", 1)', patch)
        self.assertIn('text.replace("from moviepy.editor import VideoFileClip\\n", "", 1)', patch)
        self.assertIn(
            'text.replace("from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip\\n", "", 1)',
            patch,
        )

    def test_tiktok_challenge_failures_are_retried(self):
        patch = (ROOT / "scripts/apply-private-hardening.py").read_text(encoding="utf-8")
        retry = (ROOT / "scripts/templates/tiktok_retry.py").read_text(encoding="utf-8")
        self.assertIn("install_tiktok_retry", patch)
        self.assertIn("apply_tiktok_retry_patch", patch)
        self.assertIn("universal data for rehydration", retry)
        self.assertIn("unexpected response from webpage request", retry)
        self.assertIn("range(1, max_attempts + 1)", retry)
        self.assertIn("time.sleep(attempt)", retry)

    def test_docker_build_excludes_private_runtime_data(self):
        patch = (ROOT / "scripts/apply-private-hardening.py").read_text(encoding="utf-8")
        dockerignore = (ROOT / "scripts/templates/dockerignore").read_text(encoding="utf-8")
        self.assertIn("install_dockerignore", patch)
        for private_path in (".env", "*.session", "users/", "**/cookie.txt", "dump.json"):
            self.assertIn(private_path, dockerignore)


if __name__ == "__main__":
    unittest.main()
