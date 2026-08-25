# VideoDownload Telegram Bot

一个适合个人自部署的 Telegram 视频下载 bot，重点支持 TikTok、抖音、微信视频号 / WeChat Channels、YouTube、Instagram、X/Twitter、Bilibili、小红书等平台，支持本地 Docker 测试和 VPS 24 小时运行。

本项目不是从零重写下载器，而是基于
[`upekshaip/tg-ytdlp-bot`](https://github.com/upekshaip/tg-ytdlp-bot)
做部署封装和功能增强。上游 bot 负责 Telegram、`yt-dlp`、`gallery-dl`、上传、格式选择等核心能力；本项目负责私有化部署、抖音/视频号增强、TikTok Telegram 兼容、VPS 脚本、安全默认值、测试和文档。这个项目属于“半原创”：成熟下载底座借鉴/复用上游开源项目，中文平台适配、部署流程和安全加固是在 Codex 协助下定制开发完成。

English documentation: [README.md](README.md).

## 功能

- Telegram 内直接发送链接，bot 下载并回传视频。
- 主要支持 TikTok、抖音、微信视频号 / WeChat Channels、YouTube、Instagram、X/Twitter、Bilibili、小红书，以及大量 `yt-dlp` / `gallery-dl` 支持的网站。
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

## 相对上游修改了什么

上游 `tg-ytdlp-bot` 提供 Telegram bot、`yt-dlp` / `gallery-dl`、格式选择、上传流程和后台面板等核心能力。本项目保留上游作为下载底座，在此基础上做了面向个人私有部署的补丁和增强：

- **默认私有使用**：配置模板围绕个人或小范围使用设计，通过 `ADMIN`、`PRIVATE_ALLOWED_USERS` 控制私聊权限，群组默认不开放。
- **后台更安全**：Docker Compose 默认把 Dashboard 绑定到 `127.0.0.1:5555`，VPS 上建议用 SSH tunnel 打开，不直接暴露公网。
- **抖音解析链路**：支持抖音分享文案、短链归一化；优先尝试移动端页面数据，再尝试可选的 `Evil0ctal/Douyin_TikTok_Download_API` sidecar、远程解析接口或 Reqable 抓包输出。
- **视频号解析**：增加 `weixin.qq.com/sph/...` 解析；公开页面只有预览信息时，可用 Yuanbao cookie 作为 fallback。
- **Telegram 内更新 cookie**：管理员可用 `/set_yuanbao_cookie`，直接在 Telegram 里回复 cookie 文件或 Cookie header 来更新元宝 cookie。
- **TikTok Telegram 兼容格式**：优先选 `H.264 + AAC + MP4`，避免某些 TikTok 视频上传成功但 Telegram 播放无声或兼容异常。
- **X/Twitter 多视频帖子**：一个 X/Twitter 帖子里如果有多个视频，补丁会探测全部 media entries，并按多视频任务下载，不再只取第一个。
- **公开安全打包**：`scripts/package-for-vps.sh` 默认排除真实配置、cookies、Telegram session、日志、下载文件和私有压缩包；只有显式 `--include-private` 才会生成个人迁移包。
- **VPS 自检循环**：`scripts/vps-watchdog.sh` 从系统层检查 Docker、app 容器、NTP 时间同步和 Pyrogram session；发现时间漂移或崩溃迹象时只重启 bot 服务。
- **补丁化维护上游**：自定义修改集中在 `scripts/apply-private-hardening.py` 和 `scripts/templates/`，以后重新 clone 上游 bot 后可以重复打补丁。
- **聚焦测试**：为自定义的抖音移动端解析、视频号解析保留了单元测试。

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

### VPS 自检循环

VPS 24 小时运行时，建议安装系统级 watchdog。它每分钟从外部检查 Docker、app 容器、系统时间同步，以及 Telegram Pyrogram session 是否真的启动。遇到 Telegram 时间漂移、近期 Python/Telegram 崩溃、容器停止等情况时，只重启 `app` 服务，不会重启整台 VPS。

```bash
sudo install -m 0755 scripts/vps-watchdog.sh /usr/local/bin/video-download-watchdog

sudo tee /etc/systemd/system/video-download-watchdog.service >/dev/null <<'EOF'
[Unit]
Description=VideoDownload bot watchdog
Wants=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
Environment=APP_DIR=/opt/video-download-bot/vendor/tg-ytdlp-bot
Environment=APP_SERVICE=app
Environment=LOG_FILE=/var/log/video-download-watchdog.log
ExecStart=/usr/local/bin/video-download-watchdog
EOF

sudo tee /etc/systemd/system/video-download-watchdog.timer >/dev/null <<'EOF'
[Unit]
Description=Run VideoDownload bot watchdog every minute

[Timer]
OnBootSec=2min
OnUnitActiveSec=1min
AccuracySec=10s
Persistent=true
Unit=video-download-watchdog.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now video-download-watchdog.timer
```

查看状态：

```bash
systemctl list-timers --all video-download-watchdog.timer
systemctl status video-download-watchdog.service --no-pager -l
tail -f /var/log/video-download-watchdog.log
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

视频号 Yuanbao fallback 可在 `scripts/init-local.sh` 生成的运行时环境文件里配置：

```env
WECHAT_CHANNELS_YUANBAO_COOKIE=
WECHAT_CHANNELS_TIMEOUT=30
```

也可以用管理员账号在 Telegram 里发送 `/set_yuanbao_cookie`，回复 cookie 文件或 Cookie header，即可运行时更新。

### 抖音 Cookie 更新

抖音很多链接可以不依赖本人 cookie，但抖音风控变化比较频繁，保持一个新的 cookie 可以提高解析成功率。

支持两种格式：

- 浏览器导出的 Netscape `cookies.txt`；
- 原始请求头，例如 `Cookie: name=value; name2=value2`。

更新步骤：

1. 浏览器打开 <https://www.douyin.com/> 并登录。
2. 导出 Douyin cookies.txt，或在开发者工具 Network / 网络里复制 `douyin.com` 请求的 `Cookie` header。
3. 保存到：

   ```text
   deploy/cookies/douyin.txt
   ```

4. 重新执行初始化，让脚本同步到可选的 Douyin sidecar 配置：

   ```bash
   scripts/init-local.sh
   scripts/local-up.sh
   ```

如果是在 VPS 上，进入部署目录后执行同样命令，例如：

```bash
cd /opt/video-download-bot
scripts/init-local.sh
scripts/local-up.sh
```

注意：

- `deploy/cookies/douyin.txt` 已被 Git 忽略，不会上传 GitHub。
- `scripts/package-for-vps.sh` 默认不会打包这个 cookie。
- 只有使用 `--include-private` 时才会包含真实 cookie，所以这个私有迁移包必须自己保存。

### 视频号 Yuanbao Cookie 获取

部分视频号链接的公开页面 `weixin.qq.com/sph/...` 只返回预览信息，这时项目可以选择使用已登录的腾讯元宝网页 cookie 作为 fallback。

元宝入口：

- 当前网页应用及登录入口：<https://yuanbao.tencent.com/>
- 原来的 `/chat/` 地址现在会跳转到网页应用首页。

推荐步骤：

1. 用浏览器打开 <https://yuanbao.tencent.com/> 并登录。
2. 打开浏览器开发者工具，然后刷新页面。
3. 在 Network / 网络里找到一个已登录状态下发往 `yuanbao.tencent.com` 的请求。
4. 复制请求里的 `Cookie` header，或者导出 cookie 文件。
5. 在 Telegram 里用管理员账号发送 `/set_yuanbao_cookie`。
6. 把 Cookie header 或 cookie 文件回复给 bot。

如果元宝请求返回 HTTP `401`，表示保存的 cookie 已经过期或被拒绝，需要重新登录并按上述步骤更新。元宝可能调整内部接口地址，因此应从当前网页应用获取 cookie，不要依赖旧教程中的固定接口。

手动更新方式：

1. 打开 `vendor/tg-ytdlp-bot/.env`。
2. 把复制到的 Cookie header 填到 `WECHAT_CHANNELS_YUANBAO_COOKIE=` 后面。
3. 重启 bot：

   ```bash
   scripts/local-up.sh
   ```

这个 cookie 等同于你的登录态，请像密码一样保管。不要提交到 GitHub，不要贴到 issue，不要放进公开打包文件。

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
- 本项目自研/半原创部分包括：部署封装、私有化安全默认值、抖音移动端解析、视频号/Yuanbao 解析、Telegram 更新 cookie 命令、TikTok Telegram 兼容格式策略、测试、文档和 VPS 运维流程；这些部分是在 Codex 协助下开发整理完成。

## 法律和安全提示

请只下载你拥有、获得授权，或法律允许保存的内容。请遵守平台条款、版权和当地法律。

不要提交真实 bot token、Telegram API、cookie、session 或私密打包文件。
