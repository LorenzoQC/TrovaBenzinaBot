from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from trovabenzina.config import LANGUAGES, DEFAULT_LANGUAGE
from trovabenzina.core.db import get_user
from trovabenzina.i18n import t
from trovabenzina.utils import inline_kb
from .favorites import favorites_callback  # reuse logic

__all__ = ["profile_conv"]


async def profile_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    fuel, service, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    kb = inline_kb(
        [
            (t("edit_language", lang), "edit_language"),
            (t("edit_fuel", lang), "edit_fuel"),
            (t("edit_service", lang), "edit_service"),
            (t("edit_favorite_btn", lang), "fav_edit"),
        ]
    )
    text = t("profile_info", lang).format(fuel=fuel, service=service, language=LANGUAGES[lang])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


profile_conv = favorites_callback  # type: ignore
