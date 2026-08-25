# ALL VideoDownload Plus 部署与迁移

这是本项目本地安装、VPS 部署、备份、迁移、验收和回滚的中文标准手册。
生产域名、IP、SSH 端口、密码和 Cookie 不保存在 GitHub。

## 环境要求

- Docker Engine 或 Docker Desktop
- Docker Compose v2
- Git、Python 3、`rsync`、`tar`
- Telegram Bot token、`API_ID` 和 `API_HASH`

当前容器基线为 Python 3.12、稳定版 yt-dlp 2026.08.19 和
bgutil-ytdlp-pot-provider 1.3.2。

## 本地安装

```bash
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git
cd ALL-VideoDownload-Plus
cp .env.example .env
scripts/init-local.sh
```

第一次初始化会创建被 Git 忽略的 `deploy/config.local.py`。填写 Telegram
参数、管理员数字 ID、日志聊天 ID 和独立的 Web 后台账号密码，然后执行：

```bash
scripts/init-local.sh
python3 -m unittest discover -s tests
scripts/local-up.sh
```

本地后台为 `http://localhost:5555`。VPS 启动同一个 Bot 前必须停止本地服务：

```bash
scripts/local-down.sh
```

## 全新 VPS 安装

```bash
git clone https://github.com/smthdagg/ALL-VideoDownload-Plus.git /opt/video-download-bot
cd /opt/video-download-bot
cp .env.example .env
cp deploy/config.local.py.example deploy/config.local.py
```

填写私有配置后执行：

```bash
scripts/init-local.sh
python3 -m unittest discover -s tests
scripts/local-up.sh
sudo scripts/install-vps-operations.sh
```

检查：

```bash
cd /opt/video-download-bot/vendor/tg-ytdlp-bot
docker compose ps
docker compose exec -T app pip check
curl -fsS http://127.0.0.1:5555/health
systemctl is-active video-download-watchdog.timer video-download-runtime-cleanup.timer
```

## 后台访问

后台默认只监听 `127.0.0.1:5555`。私有访问可使用 SSH tunnel：

```bash
ssh -p YOUR_SSH_PORT -L 5555:127.0.0.1:5555 root@YOUR_VPS
```

如果主机 443 已被占用，需要公网 HTTPS 后台时，可把 Caddy 发布到 8443：

```bash
cd /opt/video-download-bot
DASHBOARD_DOMAIN=bot-admin.example.com \
DASHBOARD_HTTPS_PORT=8443 \
scripts/configure-vps-dashboard.sh
```

脚本会先备份 Compose、Caddy 和私有配置。仓库不会提供默认生产域名。

## 公开安全包

```bash
scripts/package-for-vps.sh
```

公开包不包含真实配置、Cookie、Session、动态用户、用户目录、运行数据库、
下载媒体、日志、TLS 状态、SSH 密钥、旧压缩包和可重新生成的 vendor 目录，
并附带清单和 SHA-256 校验和。目标机运行 `scripts/init-local.sh` 时重新 clone 上游。

## 在旧 VPS 准备私有迁移包

```bash
cd /opt/video-download-bot
sudo scripts/prepare-vps-migration.sh
```

这个脚本会：

1. 记录 Bot 与 watchdog 定时器是否正在运行；
2. 暂停 watchdog，并只停止 `app` 容器，使 Telegram Session 保持一致；
3. 保存私有配置、Cookie、Session、动态授权、用户偏好和运行数据库；
4. 排除下载媒体、临时日志、Caddy TLS 私钥、缓存、SSH 密钥和旧压缩包；
5. 生成 SHA-256 校验和，并把文件权限设置为 600；
6. 无论成功或出错，都自动恢复原 Bot 与 watchdog。

默认输出目录为 `/root/video-download-migrations`。私有迁移包绝不能上传 GitHub。

## 传输到新 VPS

```bash
scp -P YOUR_SSH_PORT \
  root@OLD_VPS:/root/video-download-migrations/video-download-bot-private-TIMESTAMP.tar.gz* \
  /root/
```

在新 VPS 验证并解压：

```bash
cd /root
sha256sum -c video-download-bot-private-TIMESTAMP.tar.gz.sha256
mkdir -p /opt/video-download-bot
tar -tzf video-download-bot-private-TIMESTAMP.tar.gz | head
tar -xzf video-download-bot-private-TIMESTAMP.tar.gz \
  -C /opt/video-download-bot --strip-components=1
```

启动新 VPS 前，必须停止旧 VPS 的 Bot，避免同一个 Telegram session 同时在线：

```bash
ssh -p YOUR_SSH_PORT root@OLD_VPS \
  'cd /opt/video-download-bot/vendor/tg-ytdlp-bot && docker compose stop app'
```

然后在新 VPS 激活：

```bash
cd /opt/video-download-bot
sudo scripts/restore-vps-migration.sh
```

恢复脚本会重新接入上游 Git、应用本项目补丁、验证 Compose、重建容器、安装
watchdog 和磁盘清理定时器，并检查后台健康状态。公网域名需单独配置。

## 迁移验收

```bash
cd /opt/video-download-bot/vendor/tg-ytdlp-bot
docker compose ps
docker compose exec -T app pip check
curl -fsS http://127.0.0.1:5555/health
docker compose logs --since=5m app | grep -E 'Session started|Started [0-9]+ HandlerTasks'
systemctl is-active video-download-watchdog.timer video-download-runtime-cleanup.timer
```

随后用已授权 Telegram 用户测试消息，并分别测试 TikTok、抖音、视频号、
Instagram、X/Twitter 和 YouTube。TikTok 必须检查实际音频流和视频流，不能只看
是否生成文件。

## 回滚

新 VPS 未通过全部验收前不要删除旧 VPS。失败时停止新 VPS 的 `app`，重新启动
旧 VPS 的 `app`，保留原迁移包不变，查看新服务器日志后再修复。

原地升级时，应先备份运行文件并给当前应用镜像打回滚标签。Telegram session、
后台健康检查或真实下载测试失败时，恢复旧文件和旧镜像。

## Agent 接手

新的 Coding Agent 必须先读根目录 [AGENTS.md](../AGENTS.md)。
`vendor/tg-ytdlp-bot` 是被忽略的生成目录，长期修改必须写入
`scripts/apply-private-hardening.py`、`scripts/templates/`、测试和文档。
