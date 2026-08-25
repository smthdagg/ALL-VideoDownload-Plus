import logging


logger = logging.getLogger(__name__)

YUANBAO_COOKIE_COMMAND = "set_yuanbao_cookie"
YUANBAO_COOKIE_DESCRIPTION = "更新视频号元宝 Cookie"
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

    commands = [
        command
        for command in default_commands
        if command.command != YUANBAO_COOKIE_COMMAND
    ]
    commands.append(BotCommand(YUANBAO_COOKIE_COMMAND, YUANBAO_COOKIE_DESCRIPTION))

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
