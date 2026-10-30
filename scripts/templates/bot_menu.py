import logging


logger = logging.getLogger(__name__)

ADMIN_COMMANDS_BY_LANGUAGE = {
    'en': (('users', 'User management'),),
    'zh': (('users', '用户管理'),),
}
ADMIN_COMMANDS = ADMIN_COMMANDS_BY_LANGUAGE['en']
YUANBAO_COOKIE_COMMAND = 'set_yuanbao_cookie'  # Legacy command, excluded from visible menus.
TELEGRAM_MENU_LANGUAGE_CODES = {
    "en": ("en",),
    "zh": ("zh",),
}
from HELPERS.private_i18n import text


COMMON_COMMAND_DESCRIPTIONS_ZH = {
    "start": "开始使用 Bot",
    "help": "查看使用帮助",
    "settings": "设置：下载、账号、界面与文件",
    "lang": "切换中文或英文",
    "format": "选择画质与格式",
    "audio": "下载音频",
    "img": "下载图片",
    "link": "获取直接下载链接",
    "clean": "清理已下载文件",
    "cookie": "导入 Cookie TXT 与查看状态",
    "check_cookie": "检查 Cookie 状态",
    "usage": "查看使用统计",
    "tags": "设置媒体标签",
    "subs": "设置字幕选项",
    "split": "设置文件分段",
    "mediainfo": "查看媒体信息",
    "keyboard": "显示快捷键盘",
    "proxy": "设置下载代理",
    "search": "搜索媒体",
    "args": "设置下载参数",
    "nsfw": "设置敏感内容选项",
    "list": "查看支持的内容",
}

COMMON_COMMAND_DESCRIPTIONS_EN = {
    "start": "Start the bot",
    "lang": "Change language",
    "help": "Show help instructions",
    "keyboard": "Show the shortcut keyboard",
    "settings": "Open download settings",
    "clean": "Clean temporary files",
    "vid": "Download video",
    "img": "Download image",
    "audio": "Download audio",
    "search": "Search media",
    "cookie": "Manage website cookies",
    "cookies_from_browser": "Import browser cookies",
    "playlist": "Download playlists",
    "format": "Choose quality and format",
    "list": "List available formats",
    "mediainfo": "Toggle media information",
    "split": "Set file split size",
    "subs": "Set subtitle options",
    "link": "Get direct media links",
    "proxy": "Set download proxy",
    "check_cookie": "Check cookie status",
    "save_as_cookie": "Save text as cookies",
    "tags": "Manage media tags",
    "usage": "View usage statistics",
    "nsfw": "Set sensitive-content options",
    "args": "Set advanced download options",
}


YUANBAO_COOKIE_HELP = text("yuanbao_guide", language="zh")


def get_yuanbao_cookie_help(user_id):
    return text("yuanbao_guide", user_id=user_id)


def _localized_base_commands(default_commands, language, bot_command_type):
    if language != "zh":
        return list(default_commands)
    return [
        bot_command_type(
            command.command,
            COMMON_COMMAND_DESCRIPTIONS_ZH.get(command.command, command.description),
        )
        for command in default_commands
    ]


def _fallback_commands(bot_command_type):
    return [bot_command_type(command, COMMON_COMMAND_DESCRIPTIONS_EN[command])
            for command in ('start', 'settings', 'cookie', 'help')]


def register_admin_bot_commands(app, admin_ids):
    """Register localized global menus and add maintenance commands for admins."""
    from pyrogram.types import BotCommand, BotCommandScopeChat

    # Replace previous scopes instead of merging stale commands back into them.
    base_commands = _fallback_commands(BotCommand)

    try:
        app.set_bot_commands(_localized_base_commands(base_commands, "en", BotCommand))
    except Exception as exc:
        logger.warning("Could not register the default Telegram menu: %s", exc)

    for language, telegram_codes in TELEGRAM_MENU_LANGUAGE_CODES.items():
        for telegram_code in telegram_codes:
            try:
                app.set_bot_commands(
                    _localized_base_commands(base_commands, language, BotCommand),
                    language_code=telegram_code,
                )
            except Exception as exc:
                logger.warning(
                    "Could not register the global Telegram menu for %s (%s): %s",
                    language,
                    telegram_code,
                    exc,
                )

    for admin_id in admin_ids:
        try:
            chat_id = int(admin_id)
            scope = BotCommandScopeChat(chat_id)
            try:
                admin_commands = _localized_base_commands(base_commands, "en", BotCommand)
                admin_commands.extend(BotCommand(name, description) for name, description in ADMIN_COMMANDS_BY_LANGUAGE["en"])
                app.set_bot_commands(admin_commands, scope=scope)
            except Exception as exc:
                logger.warning("Could not register the default admin menu for %s: %s", admin_id, exc)
            for language, telegram_codes in TELEGRAM_MENU_LANGUAGE_CODES.items():
                for telegram_code in telegram_codes:
                    localized_commands = ADMIN_COMMANDS_BY_LANGUAGE[language]
                    commands = _localized_base_commands(base_commands, language, BotCommand)
                    commands.extend(BotCommand(name, description) for name, description in localized_commands)
                    app.set_bot_commands(commands, scope=scope, language_code=telegram_code)
        except Exception as exc:
            logger.warning(
                "Could not register the admin Telegram menu for %s: %s",
                admin_id,
                exc,
            )
