from telegram import Update
from telegram.ext import ContextTypes

from trovabenzina.config import DEFAULT_LANGUAGE
from trovabenzina.core.db import get_user
from trovabenzina.i18n import t


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _, _, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    await update.message.reply_text(t("help", lang))
