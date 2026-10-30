# ALL VideoDownload Plus 中文使用说明

[English](README.md) · [部署与迁移](docs/DEPLOYMENT.zh-CN.md) · [Cookie 导入](docs/COOKIE-IMPORT.md) · [安全说明](docs/SECURITY.md)

这是一个可部署在自己 VPS 上的 Telegram 媒体下载项目，基于 `upekshaip/tg-ytdlp-bot` 维护独立的补丁与模板，提供平台解析增强、中英文菜单、个人 Cookie 导入、用户审批和 Web 管理后台。

## 直接下载

在 Bot 私聊中发送平台原始链接或完整分享文案。Bot 按平台能力解析并返回视频、图片、图集或音频。私人部署需先通过管理员审批。

常用入口只有 `/start`、`/settings`、`/cookie`、`/help`；管理员额外看到 `/users`。不用记住所有高级命令。

## 菜单分类

| 入口 | 实际功能 |
|---|---|
| 开始页 → 下载工具 | 音频、图片、播放列表、媒体直链、搜索 |
| 设置 → 下载偏好 | 画质与格式、字幕、文件分段、媒体信息、标签 |
| 设置 → Cookie 与账号 | TXT 导入、平台选择、最近导入时间与记录数 |
| 设置 → 界面与语言 | 中文/English、快捷键盘 |
| 设置 → 文件与记录 | 清理文件与设置、使用统计 |
| 设置 → 高级设置 | 下载代理、下载参数、敏感内容选项 |
| 开始页 → 用户管理（仅管理员） | 申请审批、添加/移除授权、用户列表与黑名单 |

个人 Cookie 和下载设置不属于管理员维护。旧的“更新元宝 Cookie”“从服务器浏览器导入”等按钮不再出现在设置中；旧消息上的 Cookie 按钮会转到统一导入入口。

## 一次上传更新 Cookie

1. 在自己的浏览器登录需要的平台，导出 **Netscape 格式 cookies.txt**。
2. 在 Bot 打开 **设置 → Cookie 与账号**，直接发送 TXT 文件。也可使用 `/cookie`，或先选择对应平台。
3. Bot 自动识别、校验并保存；下一次下载立即使用，无需回复命令或重启。

支持视频号（元宝）、抖音、B站、小红书、YouTube、TikTok、Instagram、X/Twitter。可逐个平台上传，也可上传包含多个平台的一个文件。更新某个平台时保留其他平台记录；不同用户相互隔离。

要求：UTF-8、最多100KB。支持 HttpOnly 与浏览器会话 Cookie；格式错误、所选平台不符或全部过期时保留原文件并提示重试。菜单显示导入时间；“导入成功”代表已保存，不等于平台仍接受该登录态。

**视频号应导出已登录腾讯元宝的 Cookie**，不是任意微信网页 Cookie。Bot 无法自行取得你电脑或手机上的浏览器登录态，平台使会话失效后仍需重新登录并导出。

## 平台与限制

- **视频号**：公开接口与元宝增强解析；仅预览信息不是视频直链。登录态失效时提示更新，不再误用 gallery-dl。
- **抖音**：移动分享页解析及可选 API sidecar；登录、风控或网络限制可能影响结果。
- **TikTok**：有限挑战重试和 Telegram 兼容格式选择，不保证挑战始终可解。
- **X/Twitter**：支持帖子中的多个视频；受限内容可能需要 Cookie。
- **YouTube**：使用 yt-dlp 与 PO-token provider；账号、年龄、会员和地区限制仍适用。
- **B站、小红书、Instagram 等**：结合当前 yt-dlp/gallery-dl 与项目已集成的解析能力；支持程度随平台规则变化。

可用的兼容命令包括 `/audio URL`、`/img URL`、`/link URL`、`/format`、`/subs`、`/clean`、`/usage`、`/lang`。这些功能已放入相应菜单，不再全部堆在 Telegram 命令列表中。

不保证所有链接、清晰度、地区或登录后的权限均可用。Telegram 上传限制、平台反爬、Cookie 失效和下载器更新都会影响结果。

## 安装与部署

需要 Docker/Compose v2、Git、Python3，以及 Telegram Bot Token、API_ID、API_HASH。

```bash
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git
cd ALL-VideoDownload-Plus
cp .env.example .env
cp deploy/config.local.py.example deploy/config.local.py
```

在被 Git 忽略的 `deploy/config.local.py` 中填写自己的 Telegram 凭据、管理员数字ID和独立后台账号，然后：

```bash
scripts/init-local.sh
python3 -m unittest discover -s tests
scripts/local-up.sh
```

后台默认仅监听 `127.0.0.1:5555`；公网 HTTPS、VPS 运维、备份和回滚见[部署手册](docs/DEPLOYMENT.zh-CN.md)。同一 Bot 会话不要在两台机器同时运行。

## 项目结构与隐私

- 定制源码：`scripts/templates/`、`scripts/apply-private-hardening.py`。
- `vendor/tg-ytdlp-bot/` 是本机生成的运行目录，不直接提交。
- Cookie、Token、私钥、会话、用户记录和私有迁移包不进入公开仓库。
- 公开示例使用占位符；历史补丁快照不代表当前菜单和使用方式。

参见[架构](docs/ARCHITECTURE.md)、[安全说明](docs/SECURITY.md)、[上游致谢](docs/CREDITS.md)和[许可证](LICENSE)。

## 运维与后台

部署脚本提供 watchdog 与自动清理计时器，按配置的磁盘阈值和保留时间清理临时媒体。重启服务、切换 IP 和维护列表需要在部署主机执行，Web 后台会提示主机边界，不会在容器内冒充宿主机执行。完整步骤见部署手册。
