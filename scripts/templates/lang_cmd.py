from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CONFIG.LANGUAGES.language_router import language_router, set_user_language
from CONFIG.messages import safe_get_messages
from HELPERS.private_i18n import text
from HELPERS.safe_messeger import safe_send_message


SUPPORTED_LANGUAGES = {
    "zh": "中文",
    "en": "English",
}


def _language_keyboard(user_id):
    messages = safe_get_messages(user_id)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("中文", callback_data="lang_select_zh"),
            InlineKeyboardButton("English", callback_data="lang_select_en"),
        ],
        [InlineKeyboardButton(getattr(messages, "BTN_CLOSE", "Close"), callback_data="lang_close")],
    ])


def lang_command(app, message):
    user_id = message.chat.id
    parts = (message.text or "").split()
    if len(parts) >= 2:
        language = parts[1].lower()
        if language not in SUPPORTED_LANGUAGES:
            safe_send_message(
                user_id,
                safe_get_messages(user_id).LANG_INVALID_ARGUMENT_MSG,
                message=message,
            )
            return
        if set_user_language(user_id, language):
            safe_send_message(
                user_id,
                text("language_changed", language=language),
                message=message,
            )
            return
        safe_send_message(user_id, safe_get_messages(user_id).LANG_ERROR_MSG, message=message)
        return

    current = language_router.get_user_language(user_id)
    safe_send_message(
        user_id,
        safe_get_messages(user_id).LANG_SELECTION_MSG,
        reply_markup=_language_keyboard(user_id),
        parse_mode=enums.ParseMode.HTML,
        message=message,
    )
