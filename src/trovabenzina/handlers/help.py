from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from trovabenzina.config import DEFAULT_LANGUAGE
from trovabenzina.db import get_user
from trovabenzina.i18n import t

__all__ = [
    "help_handler",
]


async def help_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _, _, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    await update.message.reply_text(t("help", lang))


help_handler = CommandHandler("help", help_ep)
