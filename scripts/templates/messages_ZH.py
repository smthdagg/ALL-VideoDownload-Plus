from CONFIG.LANGUAGES.messages_EN import Messages as EnglishMessages


class Messages(EnglishMessages):
    CREDITS_MSG = "<b>界面语言：/lang</b>"
    TO_USE_MSG = "此 Bot 为私人服务；未授权用户请先提交使用申请。"
    ERROR1 = "未找到网址。请发送以 <b>https://</b> 或 <b>http://</b> 开头的链接。"
    WELCOME_MASTER = "管理员您好。发送链接即可下载，使用 /settings 打开设置，使用 /users 管理用户。"
    URL_EXTRACTOR_WELCOME_MSG = (
        "你好，{first_name}。\n\n"
        "直接发送视频或图片链接即可下载。支持 TikTok、Douyin/抖音、WeChat Channels/视频号、"
        "X、Instagram、YouTube、Bilibili/哔哩哔哩、小红书等平台。\n\n"
        "使用 /settings 设置画质、Cookie 与语言；使用 /help 查看完整向导。\n\n{credits}"
    )
    HELP_MSG = """
<b>视频下载 Bot 使用向导</b>

<b>基本使用</b>
• 直接发送视频、图片或帖子链接，Bot 会自动解析并下载。
• 支持 TikTok、Douyin/抖音、WeChat Channels/视频号、X、Instagram、YouTube、Bilibili/哔哩哔哩、小红书等平台。
• <code>/audio 链接</code>：仅下载音频。
• <code>/link 链接</code>：获取直接媒体链接。
• <code>/img 链接</code>：下载图片或图集。

<b>画质与格式</b>
• <code>/format</code>：选择最佳画质、指定分辨率或每次询问。
• 在设置中选择“最佳画质”后，后续链接会直接使用该偏好。

<b>Cookie</b>
• 某些私密或受限制内容需要用户自己的 cookies.txt。
• 直接把 cookies.txt 作为文件发送给 Bot。
• <code>/check_cookie</code>：检查 Cookie。
• 管理员可在 /settings → Cookie 中更新视频号元宝 Cookie。

<b>播放列表和多媒体帖子</b>
• <code>链接*1*5</code>：下载第 1 至 5 项。
• X 等包含多个视频的帖子会依次下载全部媒体。

<b>其他</b>
• <code>/settings</code>：打开设置菜单。
• <code>/lang</code>：切换中文或 English。
• <code>/clean</code>：清理自己的临时文件。
• <code>/usage</code>：查看自己的使用记录。
"""
    PLAYLIST_HELP_MSG = "发送播放列表链接即可下载；可在链接末尾添加 <code>*开始*结束</code>，例如 <code>链接*1*5</code>。"
    IMG_HELP_MSG = "发送 <code>/img 链接</code> 下载图片或图集；范围示例：<code>/img 1-10 链接</code>。"
    SEARCH_MSG = "<b>视频搜索</b>\n\n点击按钮使用 @vid 内联搜索。"
    LINK_HINT_MSG = "发送 <code>/link 链接</code> 获取可用的直接媒体链接。"
    SAVE_AS_COOKIE_HINT = "把 Netscape 格式 Cookie 保存为 cookies.txt 并作为文件发送，或使用 /save_as_cookie 保存文本。"

    CHECKING_CACHE_MSG = "正在检查缓存...\n\n<code>{url}</code>"
    PROCESSING_MSG = "正在处理..."
    DOWNLOADING_MSG = "正在下载媒体...\n\n"
    DOWNLOADING_IMAGE_MSG = "正在下载图片...\n\n"
    DOWNLOAD_COMPLETE_MSG = "下载完成。\n\n"
    DOWNLOADED_STATUS_MSG = "已下载："
    SENT_STATUS_MSG = "已发送："
    PENDING_TO_SEND_STATUS_MSG = "等待发送："
    TITLE_LABEL_MSG = "标题："
    MEDIA_COUNT_LABEL_MSG = "媒体数量："
    AUDIO_DOWNLOAD_FINISHED_PROCESSING_MSG = "下载完成，正在处理音频..."
    VIDEO_PROCESSING_MSG = "正在处理视频..."
    SENT_FROM_CACHE_MSG = "已从缓存发送，共 {count} 个媒体组。"
    VIDEO_SENT_FROM_CACHE_MSG = "视频已从缓存发送。"
    PLAYLIST_SENT_FROM_CACHE_MSG = "播放列表已从缓存发送（{cached}/{total}）。"
    CACHE_PARTIAL_MSG = "已从缓存发送 {cached}/{total}，正在下载缺少的内容..."
    PLEASE_WAIT_MSG = "请稍候..."

    INVALID_URL_MSG = "链接无效。请发送以 http:// 或 https:// 开头的完整网址。"
    ERROR_OCCURRED_MSG = "处理失败\n\n<code>{url}</code>\n\n错误：{error}"
    ERROR_OCCURRED_SHORT_MSG = "处理失败"
    ERROR_SENDING_VIDEO_MSG = "发送视频失败：{error}"
    ERROR_UNKNOWN_MSG = "未知错误：{error}"
    ERROR_NO_DISK_SPACE_MSG = "服务器磁盘空间不足，暂时无法下载。"
    ERROR_FILE_SIZE_LIMIT_MSG = "文件超过 {limit} GB 限制，请选择较小的文件或较低画质。"
    ERROR_GETTING_LINK_MSG = "获取链接失败：\n{error}"
    ERROR_ORIGINAL_NOT_FOUND_MSG = "找不到原消息，请重新发送链接。"
    ERROR_COOKIE_NEEDED_MSG = "该内容可能需要登录 Cookie。请上传对应平台的 cookies.txt 后重试。"
    ERROR_COOKIE_INSTRUCTIONS_MSG = "请从已登录浏览器导出 Netscape 格式 cookies.txt，并作为文件发送给 Bot。"
    DOWNLOAD_ERROR_GENERIC = "下载时发生错误，请稍后重试或更新对应平台 Cookie。"
    SIZE_LIMIT_EXCEEDED = "文件超过 {max_size_gb} GB 限制，请选择较低画质。"
    FAILED_DOWNLOAD_VIDEO_MSG = "视频下载失败：{error}"
    DOWN_UP_ERROR_DOWNLOADING_MSG = "下载失败：{error_message}"
    DOWN_UP_ERROR_GETTING_LINK_MSG = "获取媒体链接失败：{error_msg}"
    VIDEO_PROCESSING_ERROR_MSG = "视频处理失败：{error}"
    AUDIO_DOWNLOAD_FAILED_MSG = "音频下载失败：{error}"
    AUDIO_SEND_FAILED_MSG = "音频发送失败：{error}"
    TAG_FORBIDDEN_CHARS_MSG = "标签 #{tag} 含有不允许的字符。只能使用文字、数字和下划线。请使用：{example}"
    OTHER_TAG_ERROR_MSG = "标签 #{wrong} 含有不允许的字符。只能使用文字、数字和下划线。请使用：{example}"

    BTN_CLOSE = "关闭"
    CHANNEL_JOIN_BUTTON_MSG = "加入频道"
    SETTINGS_DEV_GITHUB_BUTTON_MSG = "项目源码"
    SETTINGS_CONTR_GITHUB_BUTTON_MSG = "上游项目"
    URL_EXTRACTOR_HELP_CLOSE_BUTTON_MSG = "关闭"
    URL_EXTRACTOR_ADD_GROUP_CLOSE_BUTTON_MSG = "关闭"
    SUBS_BACK_BUTTON_MSG = "返回"
    SETTINGS_LANGUAGE_BUTTON_MSG = "界面语言"
    SETTINGS_CLEAN_BUTTON_MSG = "清理文件"
    SETTINGS_COOKIES_BUTTON_MSG = "Cookie"
    SETTINGS_MEDIA_BUTTON_MSG = "媒体与画质"
    SETTINGS_INFO_BUTTON_MSG = "帮助与记录"
    SETTINGS_MORE_BUTTON_MSG = "更多设置"
    SETTINGS_TITLE_MSG = "<b>Bot 设置</b>\n\n请选择类别："
    SETTINGS_MENU_CLOSED_MSG = "菜单已关闭。"
    SETTINGS_CLEAN_TITLE_MSG = "<b>清理选项</b>\n\n请选择要清理的内容："
    SETTINGS_COOKIES_TITLE_MSG = "<b>Cookie 管理</b>\n\n请选择操作："
    SETTINGS_MEDIA_TITLE_MSG = "<b>媒体与画质</b>\n\n请选择操作："
    SETTINGS_LOGS_TITLE_MSG = "<b>帮助与记录</b>\n\n请选择操作："
    SETTINGS_MORE_TITLE_MSG = "<b>更多设置</b>\n\n请选择操作："
    SETTINGS_COMMAND_EXECUTED_MSG = "操作已执行。"
    SETTINGS_FLOOD_LIMIT_MSG = "操作过于频繁，请稍后重试。"
    SETTINGS_HINT_SENT_MSG = "说明已发送。"
    SETTINGS_UNKNOWN_COMMAND_MSG = "未知操作。"
    SETTINGS_DOWNLOAD_COOKIE_BUTTON_MSG = "下载平台 Cookie"
    SETTINGS_COOKIES_FROM_BROWSER_BUTTON_MSG = "从服务器浏览器读取"
    SETTINGS_CHECK_COOKIE_BUTTON_MSG = "检查 Cookie"
    SETTINGS_SAVE_AS_COOKIE_BUTTON_MSG = "保存文本 Cookie"
    SETTINGS_FORMAT_CMD_BUTTON_MSG = "画质与格式"
    SETTINGS_MEDIAINFO_CMD_BUTTON_MSG = "媒体信息"
    SETTINGS_SPLIT_CMD_BUTTON_MSG = "文件分段"
    SETTINGS_AUDIO_CMD_BUTTON_MSG = "仅下载音频"
    SETTINGS_SUBS_CMD_BUTTON_MSG = "字幕"
    SETTINGS_PLAYLIST_CMD_BUTTON_MSG = "播放列表说明"
    SETTINGS_IMG_CMD_BUTTON_MSG = "图片下载说明"
    SETTINGS_TAGS_CMD_BUTTON_MSG = "标签"
    SETTINGS_HELP_CMD_BUTTON_MSG = "使用向导"
    SETTINGS_USAGE_CMD_BUTTON_MSG = "使用记录"
    SETTINGS_PLAYLIST_HELP_CMD_BUTTON_MSG = "播放列表"
    SETTINGS_ADD_BOT_CMD_BUTTON_MSG = "添加到群组"

    FORMAT_ALWAYS_ASK_SET_MSG = "格式已设为每次询问。发送链接后会显示画质选择。"
    FORMAT_ALWAYS_ASK_CONFIRM_MSG = "格式已设为每次询问。"
    FORMAT_BEST_UPDATED_MSG = "已设置为最佳画质（优先 AVC + MP4）：\n{format}"
    FORMAT_ID_UPDATED_MSG = "已设置格式 ID {id}：\n{format}"
    FORMAT_ID_AUDIO_UPDATED_MSG = "已设置音频格式 ID {id}：\n{format}"
    FORMAT_QUALITY_UPDATED_MSG = "已设置画质 {quality}：\n{format}"
    FORMAT_CUSTOM_UPDATED_MSG = "自定义格式已更新：\n{format}"
    FORMAT_RESOLUTION_MENU_MSG = "请选择分辨率和编码："
    FORMAT_SAVED_MSG = "格式已保存。"
    FORMAT_CHOICE_UPDATED_MSG = "格式选择已更新。"
    FORMAT_CODEC_SET_MSG = "编码已设置为 {codec}。"

    SELECT_BROWSER_MSG = "请选择用于导出 Cookie 的浏览器："
    SELECT_BROWSER_NO_BROWSERS_MSG = "服务器上没有找到支持的浏览器。可以上传 cookies.txt 或使用远程 Cookie 地址。"
    COOKIE_YT_FALLBACK_SAVED_MSG = "YouTube Cookie 已下载并保存为 cookie.txt。"
    COOKIES_NO_BROWSERS_NO_URL_MSG = "没有可用浏览器，也没有配置 COOKIE_URL。请上传 cookies.txt。"
    COOKIE_FALLBACK_TOO_LARGE_MSG = "远程 Cookie 文件超过 100KB。"
    COOKIE_FALLBACK_UNAVAILABLE_MSG = "远程 Cookie 暂不可用（状态 {status}）。请上传 cookies.txt。"
    COOKIE_FALLBACK_ERROR_MSG = "下载远程 Cookie 失败，请上传 cookies.txt。"
    COOKIES_ERROR_READING_MSG = "读取 Cookie 文件失败：{error}"
    COOKIES_ERROR_DOWNLOADING_MSG = "下载 {service} Cookie 失败，请稍后重试。"
    COOKIES_YOUTUBE_TEST_START_MSG = "正在检查 YouTube Cookie，请稍候..."

    LANG_SELECTION_MSG = "<b>请选择界面语言</b>\n\n中文 / English"
    LANG_CHANGED_MSG = "界面语言已切换为 {lang_name}。"
    LANG_ERROR_MSG = "切换语言失败。"
    LANG_INVALID_ARGUMENT_MSG = "语言代码无效。可用：zh、en。"
    LANG_CLOSED_MSG = "语言选择已关闭。"

    ADMIN_ACCESS_DENIED_MSG = "无权限：仅管理员可用。"
    ACCESS_DENIED_ADMIN = "无权限：仅管理员可用。"
    RATE_LIMIT_WITH_TIME_MSG = "操作过于频繁，请等待 {time} 后重试。"
    RATE_LIMIT_NO_TIME_MSG = "操作过于频繁，请稍后重试。"
    AUDIO_WAIT_MSG = "请等待上一个下载任务完成。"
    SUBTITLES_FAILED_MSG = "字幕下载失败。"
    SUBS_DISABLED_MSG = "字幕已关闭。"
    SUBS_DOWNLOADING_MSG = "正在下载字幕..."
    SUBS_DISABLED_ERROR_MSG = "字幕已关闭，请使用 /subs 进行设置。"
    SUBS_YOUTUBE_ONLY_MSG = "目前仅支持下载 YouTube 字幕。"
    SUBS_ERROR_DOWNLOAD_MSG = "字幕下载失败。"
    SPLIT_SIZE_SET_MSG = "分段大小已设置为 {size}。"
    SPLIT_MENU_CLOSED_MSG = "菜单已关闭。"
    LINK_INVALID_URL_MSG = "请发送有效链接。"
    LINK_PROCESSING_MSG = "正在获取直接链接..."
    LIST_PROCESSING_MSG = "正在获取可用格式..."
    LIST_INVALID_URL_MSG = "请发送以 http:// 或 https:// 开头的有效链接。"
