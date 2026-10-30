# Cookie TXT 导入

在 Telegram Bot 私聊中打开 **/settings → Cookie 与账号**，然后直接上传浏览器导出的 `cookies.txt`。默认自动识别平台，无需回复命令或重启服务。也可以先点平台按钮，再上传文件。

支持视频号（元宝）、抖音、B站、小红书、YouTube、TikTok、Instagram、X/Twitter。一个文件可以包含多个平台；也可以逐个平台导入。更新某个平台会替换该平台的旧 Cookie，保留其他平台。

文件要求：UTF-8 Netscape Cookie TXT，最多100KB。支持 `#HttpOnly_` 记录、UTF-8 BOM 和浏览器导出的零过期时间会话 Cookie。完全过期、选错平台或格式错误的文件会被拒绝，原文件保持不变。导入菜单显示平台最近导入时间与记录数。

视频号需要导出**登录后的腾讯元宝** Cookie；不是随便导出微信网页 Cookie。各下载器随后读取自己的平台 Cookie。用户之间独立保存，个人导入不会覆盖管理员的全局元宝配置。导入后会清除当前用户的 Cookie 缓存，下一次下载立即使用新文件。

导入成功表示文件已校验并保存，不能保证平台服务器仍接受该登录态。平台失效后仍需重新登录浏览器并导出；Bot 不会自行取得手机/电脑浏览器 Cookie。旧的管理员命令仍可兼容使用，但常规导入不再需要它。

## Implementation and verification

Sources: `scripts/templates/cookie_store.py`, `cookie_import_ui.py`, platform resolver templates, and `scripts/apply-private-hardening.py`. The existing document handler now routes private uploads into the unified importer; the original group handling remains intact.

Each user has a merged Netscape jar (`users/<id>/cookie.txt`) and value-free import metadata (`cookie-import.json`). Writes use a lock, temporary mode0600 files, and atomic replacement. Files uploaded through Telegram are downloaded under a fixed temporary filename. Cookie values are never echoed in responses. Douyin's explicit HTTP Cookie header filters out other sites' credentials; Yuanbao reads the importing user's Tencent cookie records at request time.

Local suite:93 tests pass, covering multi-platform merging/replacement, user isolation, invalid-file preservation, session/HttpOnly cookies, menu selection/upload, unauthorized users, selection expiry, cache reset, immediate Yuanbao refresh, and cross-platform Douyin header isolation. SG focused tests, Compose validation, candidate compilation and pip check passed. No dependency versions were changed.

Deployment updates only the app service after backup and candidate checks. A live WeChat Channels regression URL resolved and downloaded successfully; ffprobe confirmed valid video/audio. Temporary test media was removed. The menu upload flow was exercised with simulated TXT documents; no message was sent on a user's behalf.
