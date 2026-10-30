# Reply-keyboard placeholder regression

## User journey

After a download or bot command finishes, the user should receive the actual
result without an additional invisible message whose only visible element is
Telegram's timestamp. The `/keyboard` command remains the explicit way to show
or change the reply keyboard.

## Root cause and change

The upstream `reply_with_keyboard` decorator called
`send_reply_keyboard_always()` after its handler. That helper sent U+2063, an
invisible character, solely to attach a persistent reply keyboard. Telegram
rendered the extra message as a blank bubble with a timestamp. VPS-HK monitor
senders were audited separately: the JP-AUTO monitor sends one Telegram
message per event/report (with report date and event times in the body), and
ArchiveBot health sends one message per transition. Neither has a standalone
time-only send. The extra bubble after VideoDownload handler replies and
downloads came from the handler decorator.

The versioned `scripts/apply-private-hardening.py` patch now keeps the legacy
decorator API but makes it a pass-through. Visible `/keyboard` configuration
and its existing reply-keyboard message are unchanged; handlers no longer
create or edit an invisible placeholder after every action.

## Evidence

- RED: `python3 tests/test_reply_keyboard_patch.py` failed before the patch
  because `patch_reply_keyboard_messages` did not yet exist.
- GREEN: `python3 tests/test_reply_keyboard_patch.py` passed (1 test), covering
  handler pass-through, placeholder removal, and idempotent patch application.
- `python3 -m py_compile scripts/apply-private-hardening.py tests/test_reply_keyboard_patch.py` passed.
- `python3 -m unittest discover -s tests` passed (59 tests).
- VPS-HK's focused test passed after deployment; the live `app` container uses
  the rebuilt image, the decorator AST check confirms pass-through behavior,
  and `http://127.0.0.1:5555/health` returned HTTP 200. All four VideoDownload
  stack containers are running.
- Only the `app` container was recreated. The exact source backup is
  `/root/ops/backups/videodownload-reply-keyboard-before-20260923-185312/`;
  rollback image: `tg-ytdlp-bot-app:rollback-reply-keyboard-20260923-185312`.
- No test Telegram message was sent, so verification does not add noise to the
  Bot chat. The next normal handler response exercises the live no-placeholder
  path.
