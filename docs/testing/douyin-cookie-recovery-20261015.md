# 抖音解析卡住：修复与验证

日期：2026-10-15（新加坡时间）。已接续 Codex A 原 VideoDownload 项目。

## 原因与改动

1. 非 YouTube Cookie 回退把同一个解析回调再次送入 Cookie 回退，产生递归，日志大量报 `maximum recursion depth exceeded`。现增加按请求隔离的重入保护，失败后有限结束。
2. 回退原先没有切换传给下载器的 Cookie 参数。现分别使用用户 Cookie、服务 Cookie、全局 Cookie、无 Cookie，并复制选项。Cookie 文件用临时副本交给 yt-dlp，防止其保存 cookie jar 时覆盖用户上传的文件。
3. 抖音 resolver 未接收 user_id，移动分享页请求不携带用户 Cookie。本次同一视频无 Cookie 时只有页面框架，携带已有 Cookie 后返回媒体信息。已将格式探测、直接链接、下载入口接入当前用户的 Cookie；保留域名、路径和过期边界，不在 resolver 中写回文件。
4. 反复生成补丁曾在格式探测入口累计插入四次抖音解析调用。现归一为一次，同时去除直接链接入口的重复块；连续生成两次相关文件哈希一致。
5. 单路已封装 MP4 被错误标记为 requested_formats，触发不必要的合并并找不到中间文件。已移除该字段；移动接口毫秒时长同时转换为秒。

## 实际验证

- 原失败视频：`7695756868949964150`。
- VPS 真实 `get_video_formats` 入口约 **2.46 秒**返回，媒体来源为移动分享页。
- 使用上述结果实际完整下载 **2,118,118 字节** MP4。
- ffprobe 成功：**H.264 视频 + AAC 音频**，时长 **43.002993 秒**。
- 已上传的个性化 Cookie 文件 SHA-256 在验证前后相同；未输出 Cookie 值。
- TikTok 独立回归：原短链接正常解析，视频 `7688659325102918932`，12 个格式，97 秒，原代理仍生效。
- 本地完整测试 **67 项通过**；服务器现有测试集 **65 项通过**。
- Python 语法检查、Compose 配置校验、Git diff whitespace 检查通过。
- app 镜像重建成功；运行环境和新镜像的 `pip check` 均返回 `No broken requirements found`。修复已在原容器挂载代码中生效，未为此切换运行依赖版本。
- Telegram 会话重新连接，dashboard 启动正常，容器重启计数为 0。
- 测试使用容器内的实际下载入口和下载器，没有启动第二个 Telegram 客户端，也未主动向 Telegram 用户发送测试消息。临时媒体自动清除。

## 上游核对及范围

截至本次核对，yt-dlp 最新正式发布仍为 `2026.08.19`；tg-ytdlp-bot 上游 main 与现有 vendor HEAD 一致，没有可直接同步解决本问题的新提交。

Evil0ctal 参考项目最新为 v5.1.3，其浏览器后端通过真实浏览器生成匿名 Cookie 和指纹、提供签名上下文。本次审查了 browser-rpc 的 Cloak 后端及 minting client；没有将其完整身份池、数据库和浏览器栈安装到 VPS。当前恢复路径使用已有用户 Cookie，不代表已完成所有抖音视频的无 Cookie 下载。

参考：[yt-dlp 发布](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.08.19)、[参考项目发布](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/releases/tag/v5.1.3)、[浏览器后端](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/blob/main/docker/browser_rpc/backends/cloak.py)。上游读取使用 agent-reach 的 GitHub CLI 路径。

## 部署与回滚

项目源码已同步至原 VideoDownload 项目的 tracked 模板与生成脚本，而非只修改 vendor。
运行文件备份：`/root/ops/backups/douyin-cookie-resolver-20261015-102519/`。
回滚镜像：`tg-ytdlp-bot-app:rollback-douyin-20261015-102519`。
仅按备份恢复本次涉及的运行文件和源文件后重启 app；不要覆盖 users、Cookie、授权及 Telegram 会话数据。
