URL_EXTRACTOR_WELCOME_MSG = (
    "Hello, {first_name}.\n\n"
    "Send a video, image, or post link and ALL VideoDownload Plus will parse and download it. "
    "Supported priority platforms include TikTok, Douyin, WeChat Channels, X, Instagram, YouTube, "
    "Bilibili, and Xiaohongshu.\n\n"
    "Use /settings for quality, cookies, and language. Use /help for the complete guide.\n\n{credits}"
)

HELP_MSG = """
<b>ALL VideoDownload Plus Help</b>

<b>Basic usage</b>
• Send a video, image, or post link directly. The Bot parses and returns the media.
• Priority support: TikTok, Douyin, WeChat Channels, X, Instagram, YouTube, Bilibili, and Xiaohongshu.
• <code>/audio URL</code>: download audio only.
• <code>/link URL</code>: request a direct media link.
• <code>/img URL</code>: download an image or gallery.

<b>Quality and format</b>
• <code>/format</code>: choose best quality, a resolution, or ask every time.
• Select best quality once in Settings to reuse it for future downloads.
• Telegram-safe video and audio formats are selected automatically.

<b>Playlists and multi-media posts</b>
• <code>URL*1*5</code>: download items 1 through 5.
• X posts with multiple videos are downloaded one by one.
• <code>/playlist URL</code>: open the playlist usage guide.

<b>Cookies and restricted content</b>
• Send a Netscape-format <code>cookies.txt</code> file when a site requires login.
• <code>/cookie</code>: open the cookie tools.
• <code>/check_cookie</code>: check saved cookie status.
• Admins can update the WeChat Channels Yuanbao cookie from Settings.

<b>Language and account</b>
• <code>/lang</code>: switch between English and Chinese.
• <code>/settings</code>: open quality, cookie, cleanup, language, and history tools.
• <code>/clean</code>: remove your temporary downloaded files.
• <code>/usage</code>: view your usage record.

<b>Private deployment</b>
• This Bot may require administrator approval before use.
• Use the access request button if your account has not been approved.
"""
