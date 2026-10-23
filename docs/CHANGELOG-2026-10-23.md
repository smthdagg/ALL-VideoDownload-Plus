# 2026-10-23 部署修复与功能日志

> 私有部署实例的运维记录，已脱敏（不含服务器地址、凭据、用户标识）。

## 代码变更（本仓库）

### fix(proxy): 空 IP 代理防御

- `vendor/tg-ytdlp-bot/HELPERS/proxy_helper.py` 的 `build_proxy_url`：
  配置 IP 为空时返回 `None`（直连）。
- 修复问题：「域名专属代理」路径只检查端口不检查 IP，在未配置代理时
  拼出 `http://:PORT` 空主机名畸形代理，导致该名单内域名的下载全部失败。

### feat(xhs): 小红书提取器插件

- 新增 `vendor/tg-ytdlp-bot/yt_dlp_plugins/extractor/xhs_share.py`：
  - 主路径：解析分享页 `window.__INITIAL_STATE__.noteData.data.noteData`，
    输出 h264/h265 双档视频流（含分辨率/体积元数据）；请求需移动端 UA。
  - 兜底：调用 XHS-Downloader API（compose 服务 `xhs-downloader`，
    无 cookie 时为低分辨率）。
  - 图文帖回退 `imageList` 图片列表。
- 部署：compose 单文件挂载至容器 site-packages，容器重建不丢失。
- 实测：132MB 视频全量下载通过（h265, ~4MB/s）；TikTok 5.46MB 回归通过。

### 部署配置（实例侧调整，不入库，此处仅记录要点）

- `PROXY_2_*` 指向中国出口隧道，`PROXY_2_DOMAINS` 加入 bilibili 域名——
  B 站网页层 WAF 对数据中心 IP 返回 412（含中国出口），需登录态 cookie。
- 用户 cookie 文件采用多平台合并策略（单文件多域行）。

## 服务器运维记录（脱敏）

### SG（VideoDown 实例）

- TikTok：畸形代理修复后全量下载验证通过。
- 小红书：见上，双路径验证通过。
- B 站：登录 cookie 合并后，版权 MV（经中国出口）与普通视频双验证通过。
- XHS-Downloader API 容器入栈（仅绑定本机回环，内网免鉴权）。
- 监控：健康检查排程修正、核心服务存活探针新增、bot 配置每日备份、
  watchdog 噪音静音。
- compose：新增 xhs-downloader 服务；全部服务日志封顶（json-file）。
- 教训：调整代理配置必须同步核查 proxy_helper 的所有拼接点；
  编辑 compose 的补丁锚点必须带缩进（否则会插入错误位置）。

### HK（订阅/控制面实例）

- JP-AUTO 出口监视器修复 ×3（触发背景：上游机场日本节点群当日宕机，
  监视器对全体候选失明无法自愈）：
  1. 探针靶从 Google 拨测页换为 Apple 标准页（机场出口丢 Google 包，
     导致所有候选被误判失活）。
  2. 候选级 HTTP 错误不再被当作控制器失联而中止全局选路。
  3. 「仅原生 UDP」硬过滤改为原生 UDP 优先排序 + 非 UDP 健康出口降级可用。
- 自检器检查清单同步实例现状（迁移后的容器/服务/隧道）。
- 两个 AI 路由同步定时器恢复启用。
- docker 镜像清理约 6GB（磁盘 85%→57%），journal 全部封顶。
- 订阅 443 SNI 链路在迁移期曾中断（SNI 后端随旧栈下线），已随反代恢复。
- 教训：`compose down` 前必须检索反代/网关配置中对该栈端口与容器名的引用，
  共享型反代容器不能按 compose 归属判断归属权。

### UK（节点实例）

- 凭据轮换（密码 + SSH 密钥，旧公钥撤销）。
- 磁盘精简 82%→41%（593MB 系统日志清理、编译工具链 purge、journal 封顶）。
- 下载配额 nft 表四家族（ip/ip6 × 双协议）核验在位且计数正常。

### US / Tencent（节点 / 链式出口）

- US：全服务验证通过，容器内 yt-dlp 升级至最新。
- Tencent：节点、TUN 出口链、容器栈、巡检定时器全部验证通过。

## 补丁机制（上游克隆的本地修改持久化）

- `vendor/tg-ytdlp-bot/` 由 `scripts/bootstrap-upstream.sh` 从上游克隆，不入库；
  本地修改历史上会随重新 bootstrap 丢失。
- 新增 `scripts/apply-local-patches.sh`：在 bootstrap 后自动应用
  `patches/tg-ytdlp-bot/` 下的补丁与新增文件（幂等）；
  `bootstrap-upstream.sh` 末尾已挂钩。
- 本日入库：`0001-proxy-helper-empty-ip-guard.patch`（空 IP 代理防御）、
  `yt_dlp_plugins/extractor/xhs_share.py`（小红书插件）。
- 实例侧其余定制（仪表盘、私有用户体系、抖音 API 等）暂以
  `docker compose stop` 状态保存在部署机，全量快照待单独脱敏审查后归档。

## 已知限制

- B 站：无登录 cookie 不可下载——平台 JS 挑战墙对数据中心 IP 无差别拦截
  （与出口 IP、客户端指纹、工具版本均无关），配置登录 cookie 后可用。
- TikTok：gallery-dl 兜底通道被平台反爬拦截（主通道 yt-dlp 不受影响）。
- 小红书分享链接中的访问令牌有时效，过期链接属正常现象，重新分享即可。
- 机场日本节点群当日宕机为上游故障，监视器修复后可自动切换恢复。
