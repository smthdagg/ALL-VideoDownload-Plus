# VideoDownload Telegram Bot

一个适合个人自部署的 Telegram 视频下载 bot，支持本地 Docker 测试和 VPS 24 小时运行。

本项目不是从零重写下载器，而是基于
[`upekshaip/tg-ytdlp-bot`](https://github.com/upekshaip/tg-ytdlp-bot)
做部署封装和功能增强。上游 bot 负责 Telegram、`yt-dlp`、`gallery-dl`、上传、格式选择等核心能力；本项目负责私有化部署、抖音/视频号增强、VPS 脚本、安全默认值和文档。

English documentation: [README.md](README.md).

## 功能

- Telegram 内直接发送链接，bot 下载并回传视频。
- 支持 YouTube、TikTok、Instagram、X/Twitter、Bilibili、小红书，以及大量 `yt-dlp` / `gallery-dl` 支持的网站。
- 默认私有使用：
  - 只有 `ADMIN` 和 `PRIVATE_ALLOWED_USERS` 可以私聊使用；
  - 群组默认关闭，除非显式加入 `ALLOWED_GROUP`。
- 本地 Docker 测试，确认无误后部署到 VPS。
- VPS Docker Compose 常驻运行。
- Dashboard 默认只绑定 `127.0.0.1`，建议通过 SSH tunnel 查看，不直接暴露公网。
- 抖音增强：
  - 支持抖音分享文案、短链、`iesdouyin` 链接归一化；
  - 优先从移动端页面数据解析无水印直链；
  - 可选接入 `Evil0ctal/Douyin_TikTok_Download_API` sidecar；
  - 可选接入远程解析接口。
- 视频号增强：
  - 支持 `https://weixin.qq.com/sph/...`；
  - 可选使用 Yuanbao cookie 解析只返回预览信息的链接。
- TikTok 兼容模式：
  - 优先选择 `H.264 + AAC + MP4`，避免 Telegram 播放无声或兼容异常。
- 管理员可在 Telegram 里用 `/set_yuanbao_cookie` 更新 Yuanbao cookie。

## 项目结构

本仓库不直接提交完整上游 bot。初始化时会把上游项目 clone 到：

```text
vendor/tg-ytdlp-bot
```

然后执行 `scripts/apply-private-hardening.py` 打补丁。

会提交到 GitHub 的内容：

- `scripts/`：初始化、打补丁、运行、打包脚本。
- `scripts/templates/`：自定义抖音/视频号解析模块。
- `deploy/config.local.py.example`：安全配置模板。
- `.env.example`：环境变量模板。
- `tests/`：自定义解析器测试。
- `docs/`：架构、部署、安全、来源说明。

不会提交的私密/运行时文件：

- `deploy/config.local.py`
- `deploy/cookies/*.txt`
- `vendor/tg-ytdlp-bot/.env`
- `vendor/tg-ytdlp-bot/magic.session`
- 下载文件、日志、缓存、打包压缩包。

## 本地 Docker 安装

依赖：

- Docker
- Docker Compose v2
- Python 3
- Git

步骤：

```bash
git clone https://github.com/smthdagg/VideoDownload.git
cd VideoDownload
cp .env.example .env
scripts/init-local.sh
```

第一次运行会创建：

```text
deploy/config.local.py
```

填入以下信息：

- `BOT_NAME`
- `BOT_NAME_FOR_USERS`
- `ADMIN`
- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `LOGS_ID`
- `DASHBOARD_PASSWORD`

然后再次运行：

```bash
scripts/init-local.sh
scripts/local-up.sh
```

Dashboard：

```text
http://localhost:5555
```

停止本地服务：

```bash
scripts/local-down.sh
```

查看日志：

```bash
scripts/logs.sh
```

## VPS 部署

VPS 需要先安装 Docker 和 Docker Compose。

### 方式一：VPS 上直接 clone

```bash
git clone https://github.com/smthdagg/VideoDownload.git /opt/video-download-bot
cd /opt/video-download-bot
cp .env.example .env
cp deploy/config.local.py.example deploy/config.local.py
```

填写 `deploy/config.local.py` 后：

```bash
scripts/init-local.sh
scripts/local-up.sh
```

### 方式二：本地打包后上传

默认生成不含私密信息的公开安全包：

```bash
scripts/package-for-vps.sh
```

如果是你自己的 VPS 迁移包，需要包含本地真实配置、cookies、session，可显式使用：

```bash
scripts/package-for-vps.sh --include-private
```

注意：`--include-private` 生成的包必须私密保存，不能上传 GitHub。

上传并启动：

```bash
scp video-download-bot-vps.tar.gz root@YOUR_VPS:/opt/
ssh root@YOUR_VPS
mkdir -p /opt/video-download-bot
tar -xzf /opt/video-download-bot-vps.tar.gz -C /opt/video-download-bot --strip-components=1
cd /opt/video-download-bot
scripts/init-local.sh
scripts/local-up.sh
```

Dashboard 建议通过 SSH tunnel 打开：

```bash
ssh -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

然后浏览器访问：

```text
http://localhost:5555
```

## Cookie 配置

可选 cookie 文件放在：

```text
deploy/cookies/youtube.txt
deploy/cookies/instagram.txt
deploy/cookies/tiktok.txt
deploy/cookies/twitter.txt
deploy/cookies/facebook.txt
deploy/cookies/vk.txt
deploy/cookies/douyin.txt
```

默认使用 Netscape cookies.txt 格式。

视频号 Yuanbao fallback 可在 `.env` 配置：

```env
WECHAT_CHANNELS_YUANBAO_COOKIE=
WECHAT_CHANNELS_TIMEOUT=30
```

也可以用管理员账号在 Telegram 里发送 `/set_yuanbao_cookie`，回复 cookie 文件或 Cookie header，即可运行时更新。

## 验证

```bash
python3 -m unittest discover -s tests
python3 -m py_compile scripts/apply-private-hardening.py
git status --ignored -s
```

## 来源和自研部分

见 [docs/CREDITS.md](docs/CREDITS.md)。

简要说明：

- 核心 bot 来自 `upekshaip/tg-ytdlp-bot`。
- 下载能力来自 `yt-dlp`、`gallery-dl`、`ffmpeg`。
- 可选抖音 sidecar 来自 `Evil0ctal/Douyin_TikTok_Download_API`。
- 本项目自研部分包括：部署封装、私有化安全默认值、抖音移动端解析、视频号/Yuanbao 解析、Telegram 更新 cookie 命令、TikTok Telegram 兼容格式策略、测试和文档。

## 法律和安全提示

请只下载你拥有、获得授权，或法律允许保存的内容。请遵守平台条款、版权和当地法律。

不要提交真实 bot token、Telegram API、cookie、session 或私密打包文件。
