from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from trovabenzina.config import FUEL_MAP, SERVICE_MAP, LANGUAGES, DEFAULT_LANGUAGE
from trovabenzina.core.db import upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import (
    STEP_LANG,
    STEP_FUEL,
    STEP_SERVICE,
    inline_kb,
)

__all__ = ["start_conv"]  # exported to bot.main


# ── handlers ──────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await update.message.reply_text(
        t("ask_language_choice", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    ctx.user_data.clear()
    return STEP_LANG


async def language_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.split("_", 1)[1]
    ctx.user_data["lang"] = code

    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([("↩", "back_lang")])
    await query.edit_message_text(t("ask_fuel", code), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_FUEL


async def fuel_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fuel = query.data.split("_", 1)[1]
    lang = ctx.user_data["lang"]

    if fuel not in FUEL_MAP:
        return await query.answer(t("invalid_fuel", lang), show_alert=True)

    ctx.user_data["fuel"] = fuel
    kb = inline_kb([(s, f"serv_{s}") for s in SERVICE_MAP])
    kb.append([("↩", "back_fuel")])
    await query.edit_message_text(t("ask_service", lang), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_SERVICE


async def service_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data.split("_", 1)[1]
    lang = ctx.user_data["lang"]

    if service not in SERVICE_MAP:
        return await query.answer(t("invalid_service", lang), show_alert=True)

    ctx.user_data["service"] = service
    await upsert_user(
        query.from_user.id,
        ctx.user_data["fuel"],
        ctx.user_data["service"],
        lang,
    )
    await query.edit_message_text(t("profile_saved", lang))
    ctx.user_data.clear()
    return ConversationHandler.END


async def back_to_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await query.edit_message_text(
        t("ask_language_choice", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


async def back_to_fuel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([("↩", "back_lang")])
    await query.edit_message_text(t("ask_fuel", lang), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_FUEL


# ── ConversationHandler object exported to bot.main ───────────────────────
start_conv = ConversationHandler(
    entry_points=[("command", "start", start)],  # pseudo-syntax; adapt to PTB 20
    states={
        STEP_LANG: [("callback", language_selected)],
        STEP_FUEL: [("callback", fuel_selected), ("callback", back_to_lang)],
        STEP_SERVICE: [("callback", service_selected), ("callback", back_to_fuel)],
    },
    fallbacks=[],
)
