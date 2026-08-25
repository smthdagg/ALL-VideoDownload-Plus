# Platform Regression TDD Evidence

## User journeys

- A private user can request Douyin audio/video without recursive cookie errors after direct media resolution succeeds.
- Instagram extraction failures that yt-dlp cannot handle are routed to gallery-dl.
- The VPS watchdog does not lose the Telegram startup signal when download logs become noisy.

## Test specification

| Guarantee | Evidence | Result |
|---|---|---|
| Non-YouTube cookie fallback runs at most once | `tests/test_platform_runtime.py` | PASS |
| Known Instagram extraction failures request gallery-dl fallback | `tests/test_platform_runtime.py` | PASS |
| Cached direct-media metadata avoids an unnecessary resolver call | `tests/test_platform_runtime.py` | PASS |
| Existing Douyin and WeChat resolver behavior remains intact | `python3 -m unittest discover -s tests -v` | PASS, 6 tests |
| Patch application is repeatable | `python3 scripts/apply-private-hardening.py` run twice | PASS |
| Python and watchdog syntax remain valid | `python3 -m py_compile ...` and `bash -n scripts/vps-watchdog.sh` | PASS |

## RED/GREEN evidence

- RED: the three new tests failed because `scripts/templates/platform_runtime.py` did not exist.
- GREEN: all six project tests passed after adding the runtime guards and patch integration.
- VPS: the bot reported `Session started` and `Started 6 HandlerTasks`; the live Douyin resolver returned a CDN media host.

## Known external-state gap

WeChat Channels Yuanbao fallback returns HTTP 401 when the private Yuanbao login cookie expires. Code cannot renew that third-party login session; an administrator must provide a fresh cookie with `/set_yuanbao_cookie`.
