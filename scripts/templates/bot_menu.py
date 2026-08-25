import logging


logger = logging.getLogger(__name__)

ADMIN_COMMANDS = (
    ("set_yuanbao_cookie", "更新视频号元宝 Cookie"),
    ("users", "打开用户管理菜单"),
    ("add_user", "添加可使用 Bot 的用户"),
    ("remove_user", "移除可使用 Bot 的用户"),
    ("list_users", "查看已授权用户"),
    ("blacklist_user", "永久拉黑一个用户"),
    ("unblacklist_user", "解除用户永久拉黑"),
)
YUANBAO_COOKIE_COMMAND = ADMIN_COMMANDS[0][0]
YUANBAO_COOKIE_HELP = (
    "更新视频号元宝 Cookie\n\n"
    "方式一：发送 /set_yuanbao_cookie Cookie: name=value; name2=value2\n\n"
    "方式二：先发送完整 Cookie 或上传 cookies.txt，然后回复该消息发送 "
    "/set_yuanbao_cookie。\n\n"
    "Cookie 获取入口：https://yuanbao.tencent.com/"
)


def register_admin_bot_commands(app, admin_ids):
    """Add the Yuanbao maintenance command to each admin's private menu."""
    from pyrogram.types import BotCommand, BotCommandScopeChat

    try:
        default_commands = app.get_bot_commands()
    except Exception as exc:
        logger.warning("Could not read the default Telegram command menu: %s", exc)
        default_commands = []

    admin_command_names = {name for name, _ in ADMIN_COMMANDS}
    commands = [
        command
        for command in default_commands
        if command.command not in admin_command_names
    ]
    commands.extend(BotCommand(name, description) for name, description in ADMIN_COMMANDS)

    for admin_id in admin_ids:
        try:
            chat_id = int(admin_id)
            app.set_bot_commands(
                commands,
                scope=BotCommandScopeChat(chat_id),
            )
        except Exception as exc:
            logger.warning(
                "Could not register the admin Telegram menu for %s: %s",
                admin_id,
                exc,
            )
