# 2026-10-30 Release Audit

## 中文

- 核对上游 `upekshaip/tg-ytdlp-bot`：本项目当前 vendor 基线与上游 `main` 一致，没有新的主程序提交。
- 升级项目锁定的 `yt-dlp` 基线到 `2026.10.26`，并同步中英文部署说明与生成补丁脚本。
- 核对 `Evil0ctal/Douyin_TikTok_Download_API` 最新 `v5.1.8`。该版本采用独立的浏览器身份池、PostgreSQL、Redis 和 browser-rpc 架构，不兼容当前 Bot 使用的旧 sidecar 接口，因此没有未经验证地替换生产链路。
- TikTok 增加 SSL EOF、连接重置和读取超时的有限重试；抖音与 TikTok 的 Cookie fallback 保持单次边界，避免解析递归。
- 检查公开树中的 Cookie、Session、SSH 密钥、Telegram Token、密码、私有用户状态和运行时目录；这些内容通过忽略规则或示例值隔离。

## English

- Checked upstream `upekshaip/tg-ytdlp-bot`: the generated vendor baseline matches upstream `main`; no new upstream application commit is available.
- Updated the pinned `yt-dlp` baseline to `2026.10.26` and synchronized the bilingual deployment documentation and patch generator.
- Checked `Evil0ctal/Douyin_TikTok_Download_API` latest `v5.1.8`. It uses a separate browser identity pool, PostgreSQL, Redis, and browser-rpc architecture, so it is not a drop-in replacement for this bot's legacy sidecar interface and was not swapped into production without compatibility validation.
- Added bounded retries for TikTok SSL EOF, connection-reset, and read-timeout failures; Douyin and TikTok cookie fallbacks remain single-shot to prevent recursive extraction loops.
- Audited the public tree for cookies, sessions, SSH keys, Telegram tokens, passwords, private-user state, and runtime directories; these are isolated by ignore rules or example values.

## Verification

```text
python3 -m unittest discover -s tests  # 97 passed
python3 -m py_compile scripts/apply-private-hardening.py
git diff --check
```
