# WeChat Channels expired login — 2026-10-28

Reported symptom: VideoDown displayed “yt-dlp failed, trying gallery-dl…” for a WeChat Channels short link.

Root cause: the official public feed API returned preview metadata without media; the Yuanbao enhancement endpoint returned HTTP401. The direct-download path ignored the resolver error and continued into engines that do not support the link. The quality menu also lacked the WeChat-specific error branch.

Changes:

- Yuanbao401/403 now produces an actionable login-refresh message, without exposing cookie contents.
- Direct download and quality selection stop on unavailable WeChat media and escape error text before displaying it.
- Valid media continues through the original downloader path. Cookie updates already refresh the running resolver module; that behavior was retained.
- Changes live in the tracked resolver template and patch generator, rather than only the generated vendor tree.

Verification:

- Local complete test suite:83 passed; syntax checks and diff whitespace checks passed.
- Deployment focused WeChat tests:6 passed.
- Deployment full suite has3 preexisting Compose fixture errors; these reproduced using the pre-change patch generator. Production Compose formatting differs from the test fixture assumptions. No unrelated Compose normalization change was made.
- Candidate image built from the existing production image with only3 changed Python files; no dependency upgrade. Compose validation and candidate Python compilation passed.
- Only the app container was recreated. Dashboard /health returned200; backup files and a rollback image remain on the server.
- Initial reproduction returned WECHAT_CHANNELS_MEDIA_UNAVAILABLE with login_refresh_required=true. A subsequent post-deployment media download succeeded; see the latest verification note below.

Deployment validation: only the app was recreated; health and Telegram startup passed. A subsequent real WeChat Channels media download and ffprobe check succeeded. The new unified importer supersedes the older command workflow; see [Cookie import](../COOKIE-IMPORT.md).
