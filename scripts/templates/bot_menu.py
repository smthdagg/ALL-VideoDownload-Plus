import logging


logger = logging.getLogger(__name__)

ADMIN_COMMANDS_BY_LANGUAGE = {
    "en": (
        ("set_yuanbao_cookie", "Update WeChat Channels Cookie"),
        ("users", "Open user management"),
        ("add_user", "Authorize a Bot user"),
        ("remove_user", "Remove a Bot user"),
        ("list_users", "List authorized users"),
        ("blacklist_user", "Permanently blacklist a user"),
        ("unblacklist_user", "Remove a permanent blacklist"),
    ),
    "zh": (
        ("set_yuanbao_cookie", "更新视频号元宝 Cookie"),
        ("users", "打开用户管理菜单"),
        ("add_user", "添加可使用 Bot 的用户"),
        ("remove_user", "移除可使用 Bot 的用户"),
        ("list_users", "查看已授权用户"),
        ("blacklist_user", "永久拉黑一个用户"),
        ("unblacklist_user", "解除用户永久拉黑"),
    ),
}
ADMIN_COMMANDS = ADMIN_COMMANDS_BY_LANGUAGE["en"]
YUANBAO_COOKIE_COMMAND = ADMIN_COMMANDS[0][0]
TELEGRAM_MENU_LANGUAGE_CODES = {
    "en": ("en",),
    "zh": ("zh",),
}
from HELPERS.private_i18n import text


COMMON_COMMAND_DESCRIPTIONS_ZH = {
    "start": "开始使用 Bot",
    "help": "查看使用帮助",
    "settings": "打开下载设置",
    "lang": "切换中文或英文",
    "format": "选择画质与格式",
    "audio": "下载音频",
    "img": "下载图片",
    "link": "获取直接下载链接",
    "clean": "清理已下载文件",
    "cookie": "管理网站 Cookie",
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


def register_admin_bot_commands(app, admin_ids):
    """Register localized global menus and add maintenance commands for admins."""
    from pyrogram.types import BotCommand, BotCommandScopeChat

    try:
        default_commands = app.get_bot_commands()
    except Exception as exc:
        logger.warning("Could not read the default Telegram command menu: %s", exc)
        default_commands = []

    admin_command_names = {name for name, _ in ADMIN_COMMANDS}
    base_commands = [
        command for command in default_commands if command.command not in admin_command_names
    ]

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
