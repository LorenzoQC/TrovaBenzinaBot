"""
Help command handler (/help).

Shows a concise list of available commands with localized descriptions.
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from ..db import get_user_language_code_by_tg_id
from ..i18n import t
from ..utils import delete_last_profile_message

__all__ = ["help_ep", "help_handler"]


async def help_ep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help by sending the localized commands overview.

    Args:
        update: Telegram update.
        context: Callback context.
    """
    await delete_last_profile_message(context)

    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await update.message.reply_text(
        t("help", lang) + t("disclaimer", lang),
        parse_mode=ParseMode.HTML,
    )


help_handler = CommandHandler("help", help_ep)
