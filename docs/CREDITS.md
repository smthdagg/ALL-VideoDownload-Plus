# Credits and Original Work

VideoDownload combines a mature open-source Telegram downloader with a focused
private deployment and resolver layer.

## Upstream and Dependencies

- [`upekshaip/tg-ytdlp-bot`](https://github.com/upekshaip/tg-ytdlp-bot): core
  Telegram bot, download orchestration, upload flow, dashboard, and config
  model.
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp): primary media extraction
  engine.
- [`gallery-dl`](https://github.com/mikf123/gallery-dl): image/gallery
  extraction support.
- [`FFmpeg`](https://ffmpeg.org/): media probing, remuxing, and transcoding.
- [`Pyrogram`](https://pyrogram.org/): Telegram MTProto client library used by
  the upstream bot.
- [`Evil0ctal/Douyin_TikTok_Download_API`](https://github.com/Evil0ctal/Douyin_TikTok_Download_API):
  optional Douyin/TikTok resolver sidecar.
- [`Brainicism/bgutil-ytdlp-pot-provider`](https://github.com/Brainicism/bgutil-ytdlp-pot-provider):
  optional YouTube PO token provider.

## Original Work In This Repository

- Local and VPS bootstrap scripts.
- Public-safe and private migration packaging modes.
- Private-mode authorization defaults for personal Telegram bot use.
- Dashboard localhost binding and Docker deployment hardening.
- Douyin share-text cleanup, short-link normalization, mobile page parsing, and
  optional sidecar/remote resolver integration.
- WeChat Channels public-link resolver and optional Yuanbao cookie fallback.
- Telegram admin command for updating Yuanbao cookies without editing files on
  the server.
- TikTok H.264 + AAC MP4 format preference to avoid silent Telegram playback.
- Tests for custom Douyin and WeChat Channels parsing.
- English and Chinese project documentation.

## License

The upstream bot is distributed under GPL-3.0. This wrapper and patch set is
published under the same GPL-3.0 license for compatibility.

