from HELPERS.bot_menu import YUANBAO_COOKIE_HELP


def _extract_yuanbao_cookie_header(raw_text: str) -> tuple[str, int]:
    """Return a Cookie header value from Netscape cookies.txt or pasted Cookie text."""
    if not isinstance(raw_text, str):
        return "", 0

    pairs = []
    for line in raw_text.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 7:
            continue
        domain, name, value = fields[0], fields[5], fields[6]
        if (
            domain.endswith("yuanbao.tencent.com")
            or domain.endswith("tencent.com")
            or domain.endswith("qq.com")
        ):
            pairs.append(f"{name}={value}")

    if pairs:
        return "; ".join(pairs), len(pairs)

    text = raw_text.strip()
    if text.lower().startswith("cookie:"):
        text = text.split(":", 1)[1].strip()
    text = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if "=" not in text:
        return "", 0
    pair_count = len([part for part in text.split(";") if "=" in part])
    return text, pair_count


def _write_yuanbao_cookie_to_env(cookie_header: str) -> None:
    env_path = os.path.join(os.getcwd(), ".env")
    escaped = cookie_header.replace("$", "$$")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.read().splitlines()

    output = []
    replaced_cookie = False
    replaced_timeout = False
    for line in lines:
        if line.startswith("WECHAT_CHANNELS_YUANBAO_COOKIE="):
            output.append(f"WECHAT_CHANNELS_YUANBAO_COOKIE={escaped}")
            replaced_cookie = True
        elif line.startswith("WECHAT_CHANNELS_TIMEOUT="):
            output.append(line)
            replaced_timeout = True
        else:
            output.append(line)

    if not replaced_cookie:
        output.append(f"WECHAT_CHANNELS_YUANBAO_COOKIE={escaped}")
    if not replaced_timeout:
        output.append("WECHAT_CHANNELS_TIMEOUT=30")

    with open(env_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(output) + "\n")

    os.environ["WECHAT_CHANNELS_YUANBAO_COOKIE"] = cookie_header
    try:
        import URL_PARSERS.wechat_channels_api as wechat_channels_api
        wechat_channels_api.WECHAT_CHANNELS_YUANBAO_COOKIE = cookie_header
    except Exception as exc:
        logger.warning(f"Could not refresh WeChat Channels cookie in current process: {exc}")


@app.on_message(filters.command("set_yuanbao_cookie") & filters.private)
@background_handler(label="set_yuanbao_cookie")
def set_yuanbao_cookie_command(app, message):
    if int(message.chat.id) not in Config.ADMIN:
        send_to_user(message, safe_get_messages(message.chat.id).ADMIN_ACCESS_DENIED_MSG)
        return

    raw_text = ""
    secret_message_ids = [message.id]
    reply = getattr(message, "reply_to_message", None)

    try:
        if reply and getattr(reply, "document", None):
            if reply.document.file_size > 1024 * 1024:
                send_to_user(message, "Cookie 文件太大，请上传 1MB 以下的 cookies.txt。")
                return
            secret_message_ids.append(reply.id)
            with tempfile.TemporaryDirectory() as tmpdir:
                filename = reply.document.file_name or "cookies.txt"
                tmp_path = os.path.join(tmpdir, filename)
                app.download_media(reply, file_name=tmp_path)
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as handle:
                    raw_text = handle.read()
        elif reply and (getattr(reply, "text", None) or getattr(reply, "caption", None)):
            secret_message_ids.append(reply.id)
            raw_text = reply.text or reply.caption or ""
        else:
            command_text = message.text or message.caption or ""
            parts = command_text.split(maxsplit=1)
            raw_text = parts[1] if len(parts) > 1 else ""

        if not raw_text.strip():
            send_to_user(message, YUANBAO_COOKIE_HELP)
            return

        cookie_header, pair_count = _extract_yuanbao_cookie_header(raw_text)
        if not cookie_header:
            send_to_user(
                message,
                "没有识别到元宝 Cookie。\n\n用法：回复 cookies.txt 发送 /set_yuanbao_cookie，"
                "或发送 /set_yuanbao_cookie Cookie: name=value; name2=value2",
            )
            return

        _write_yuanbao_cookie_to_env(cookie_header)
        send_to_user(
            message,
            f"元宝 Cookie 已更新，识别到 {pair_count} 个 cookie。当前 bot 进程已刷新，重启后也会保留。",
        )
        logger.info(f"Yuanbao cookie updated by admin {message.chat.id}; pairs={pair_count}")
    except Exception as exc:
        logger.error(f"Failed to update Yuanbao cookie: {exc}")
        send_to_user(message, "更新元宝 Cookie 失败，请检查 cookie 格式后重试。详细错误已写入服务端日志。")
    finally:
        try:
            app.delete_messages(message.chat.id, secret_message_ids)
        except Exception:
            pass
