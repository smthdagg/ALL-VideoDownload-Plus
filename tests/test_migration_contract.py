import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MigrationContractTest(unittest.TestCase):
    def test_private_package_keeps_state_but_excludes_downloaded_media(self):
        script = (ROOT / "scripts/package-for-vps.sh").read_text(encoding="utf-8")
        self.assertIn("--include-private", script)
        self.assertIn("vendor/tg-ytdlp-bot/users/*/downloads", script)
        self.assertIn("vendor/tg-ytdlp-bot/docker/configuration-webserver/data", script)
        self.assertIn('grep -Eq "$forbidden" "$members_file"', script)
        self.assertIn("--exclude 'vendor/tg-ytdlp-bot'", script)
        self.assertIn("--exclude '.env'", script)
        self.assertNotRegex(
            script.split('if [ "$INCLUDE_PRIVATE" != "1" ]', 1)[0],
            re.escape("vendor/tg-ytdlp-bot/users'"),
        )

    def test_vps_migration_stops_and_restores_the_bot(self):
        script = (ROOT / "scripts/prepare-vps-migration.sh").read_text(encoding="utf-8")
        self.assertIn("docker compose stop", script)
        self.assertIn("trap restore_app", script)
        self.assertIn("systemctl stop video-download-watchdog.timer", script)
        self.assertIn("systemctl start video-download-watchdog.timer", script)
        self.assertIn(
            'tar -tzf "$archive" "video-download-bot/vendor/tg-ytdlp-bot/CONFIG/config.py"',
            script,
        )
        self.assertIn("--include-private", script)
        self.assertIn("chmod 600", script)

    def test_migrated_vendor_directory_can_rejoin_upstream_git(self):
        script = (ROOT / "scripts/bootstrap-upstream.sh").read_text(encoding="utf-8")
        self.assertIn("existing vendor directory without Git metadata", script)
        self.assertIn("rsync -a", script)

    def test_bootstrap_recovers_git_without_deleting_private_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            upstream = root / "upstream"
            migrated = root / "migrated-vendor"
            upstream.mkdir()
            migrated.mkdir()
            (upstream / "upstream.txt").write_text("upstream", encoding="utf-8")
            (migrated / "private-state.txt").write_text("private", encoding="utf-8")
            subprocess.run(["git", "init", "-b", "main"], cwd=upstream, check=True, capture_output=True)
            subprocess.run(["git", "add", "upstream.txt"], cwd=upstream, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Migration Test",
                    "-c",
                    "user.email=migration@example.invalid",
                    "commit",
                    "-m",
                    "fixture",
                ],
                cwd=upstream,
                check=True,
                capture_output=True,
            )

            subprocess.run(
                [str(ROOT / "scripts/bootstrap-upstream.sh")],
                env={
                    "PATH": __import__("os").environ["PATH"],
                    "UPSTREAM_REPO": str(upstream),
                    "UPSTREAM_DIR": str(migrated),
                },
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertTrue((migrated / ".git").is_dir())
            self.assertEqual((migrated / "upstream.txt").read_text(), "upstream")
            self.assertEqual((migrated / "private-state.txt").read_text(), "private")

    def test_public_files_require_deployment_specific_host_configuration(self):
        public_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (
                ROOT / "README.md",
                ROOT / "README.zh-CN.md",
                ROOT / "docs/DEPLOYMENT.md",
                ROOT / "scripts/configure-vps-dashboard.sh",
            )
        )
        self.assertNotIn("Current VPS Profile", public_text)
        self.assertIn('DASHBOARD_DOMAIN="${DASHBOARD_DOMAIN:-}"', public_text)
        self.assertIn("bot-admin.example.com", public_text)

    def test_private_users_bypass_optional_channel_subscription_check(self):
        hardening = (ROOT / "scripts/apply-private-hardening.py").read_text(encoding="utf-8")
        self.assertIn(
            "if str(chat_type).lower().endswith(\"private\") and not is_private_user_allowed(chat_id):",
            hardening,
        )
        self.assertIn(
            "if str(chat_type).lower().endswith(\"private\"):\n            return True",
            hardening,
        )


if __name__ == "__main__":
    unittest.main()
