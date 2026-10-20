# 抖音下载恢复：匿名设备 Cookie + 代理出口

日期：2026-10-20。接续 2026-10-15 的 `douyin-cookie-recovery` 修复。

## 故障现象

所有抖音链接报 `Fresh cookies (not necessarily logged in) are needed`，
全局 cookie（7 月导出，已过期）、sidecar 配置 cookie、无 cookie 全部失败。

## 根因（三层叠加）

1. **Cookie 全部过期**：sidecar 配置 cookie 为 7 月 7 日导出，全局 `TXT/cookie.txt` 同样陈旧；无 cookie 请求只返回页面框架。
2. **web 详情接口全线 403**：`aweme/v1/web/aweme/detail/` 现要求 `a_bogus` 签名，yt-dlp 的 DouyinIE 未实现（上游 TODO 明示），Evil0ctal sidecar 的 X-Bogus/a_bogus 请求也被 403。该接口无论 cookie 新旧都不可用。
3. **域不匹配导致 cookie 从未生效**：移动分享页在 `iesdouyin.com`，而 cookie jar 全是 `douyin.com` 域，requests 按域匹配把 cookie 全部丢弃——即使用户上传了新鲜 cookie 也等于没带。10-15 的成功是当时风控较松的偶然结果，不是 cookie 路径真正打通。
4. **出口 IP 被风控**：VPS 所在 HK 机房 IP 被抖音 IP 级挑战（对照 yt-dlp 测试集中多年的老视频同样被挡），任何 cookie/指纹都无效。

## 改动（tracked 模板与生成脚本）

`scripts/templates/douyin_api.py`：

- 新增自铸匿名设备 token：`_mint_ttwid()`（字节官方 ttwid 注册接口，6 小时进程内缓存）+ `_generate_verify_fp()`（`verify_` 形状 s_v_web_id）+ 随机 msToken。
- 移动分享页改用**显式 Cookie 头**：用户上传的 jar cookie 优先、匿名 token 补位，修复跨注册域丢失；仍不回写任何文件。
- 新增 `DOUYIN_MOBILE_PROXY_URL` 环境变量：为分享页请求指定 HTTP 代理出口。
- resolver 链在用户 cookie 之后、匿名请求之前插入**全局 cookie 回退**（`TXT/cookie.txt`，`DOUYIN_GLOBAL_COOKIE_PATH` 可覆盖）。

`scripts/apply-private-hardening.py`：

- `patch_compose` 的 dashboard 端口块改为容忍部署后定制：归一既有 ports 块并按 `VPS_DASHBOARD_HTTP_BINDING`（默认 `80:80`）重写，修复"部署后手工改过端口导致生成器重跑崩溃"。

## 两套方案并行（当前架构）

- **方案 A（cookie 路径）**：用户上传 cookie → 移动分享页显式携带；无上传时回退全局 cookie。cookie 过期需**手工重新提供**（浏览器导出 Netscape 格式，替换 `deploy/cookies/douyin.txt` 与全局 `TXT/cookie.txt`，sidecar 配置经 `scripts/sync-douyin-cookie.sh` 再生成）。
- **方案 B（无 cookie 路径）**：自铸匿名 ttwid/s_v_web_id，无需任何登录或手工 cookie。**仅在干净出口 IP 上有效**；被风控的 IP 必须配置 `DOUYIN_MOBILE_PROXY_URL` 走干净出口。

## 部署出口（VPS 运行时，不含在仓库）

- 干净出口：另一台自有 VPS 上运行无依赖 Python CONNECT 转发代理（`/usr/local/bin/douyin_forward_proxy.py`，systemd `douyin-proxy.service`，端口 8888，allowlist 限定视频 VPS 出口 IP）。
- 视频 VPS：安全组白名单放行后**直连**干净出口，app 的 `.env` 设置 `DOUYIN_MOBILE_PROXY_URL=http://<干净出口IP>:8888`。
- 备用路径（已停用保留）：systemd `douyin-proxy-tunnel.service` 经 SSH 本地转发 `<docker网关>:8888 → 干净 VPS 127.0.0.1:8888`（专用密钥，authorized_keys 带 `from=` 出口 IP 限制），宿主 ufw 放行 docker 子网访问 8888；白名单失效时重新启用并把 `.env` 改回网关地址。
- 端口或出口 IP 变化时，仅需改 `.env` 与干净出口侧 allowlist/白名单并重启 app。

## 验证

- 本地（干净 IP）与 VPS 容器内，同一失败视频 `7698299645013447675` 均由 `fetch_douyin_video` 成功返回元数据与直链（标题、时长正确）。
- 直链实测下载 1,793,541 字节，`content-type: video/mp4`。
- 全局/共享 cookie 文件 SHA-256 前后一致；未在任何输出中写入 cookie 值。
- 本地与 VPS 测试各 **79 项通过**（新增：全局 cookie 回退 5 项、匿名 token/代理/铸造 5 项、compose 端口漂移 3 项）。
- app 容器重建后 Telegram 会话正常连接，重启计数 0。
- 已同步 VPS 运行文件与 `.env`；GitHub 推送见提交记录。

## 已知边界

- 抖音 web 详情接口（需 a_bogus 签名）在 yt-dlp 侧仍不可用；抖音解析强依赖移动分享页路径。
- 部分登录限定/私密内容仍需方案 A 的有效登录 cookie。
- SSH 隧道与代理为系统级运行设施，VPS 重启后由 systemd 自动拉起；若干净出口 IP 变化，需同步更新 110 侧 allowlist 与 authorized_keys `from=`。
