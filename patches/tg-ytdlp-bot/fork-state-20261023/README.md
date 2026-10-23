# fork-state-20261023 — 部署实例 fork 状态快照

SG 实例 `vendor/tg-ytdlp-bot`（上游 upekshaip/tg-ytdlp-bot main, 2026-10-23）
相对上游的全部差异快照，用于灾后重建部署实例。

## 内容

- `0001-fork-state.patch`：被跟踪文件的差异（仪表盘加固、私有用户体系、
  抖音 API 解析、微信视频号、代理/回退逻辑、i18n 等）
- `untracked/`：上游不存在的新增模块（同上功能 + `.dockerignore`）

## 应用方式

```bash
cd vendor/tg-ytdlp-bot
git apply --ignore-whitespace /path/to/0001-fork-state.patch
cp -r /path/to/untracked/. .
```

或直接运行 `scripts/apply-local-patches.sh`（bootstrap 后自动执行）。

## 脱敏说明（已排除，不入库）

`CONFIG/config.py`（实例值含 BOT_TOKEN/ADMIN）、`users/`、`dump.json`、
`.active_sessions.json`、twitter cookies、Caddy 证书与密钥、douyin 配置、
`*.session*`、运行日志。实例值以 `CONFIG/config.py.example` + `.env` 重建。
