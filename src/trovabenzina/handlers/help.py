from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..db import get_user_language_code_by_tg_id
from ..i18n import t

__all__ = ["help_ep", "help_handler"]


async def help_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await update.message.reply_text(t("help", lang))


help_handler = CommandHandler("help", help_ep)
