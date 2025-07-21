from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, LANGUAGES, SERVICE_MAP
from trovabenzina.core.db import upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_FUEL, STEP_LANG, STEP_SERVICE, inline_kb

__all__ = [
    "start",
    "language_selected",
    "fuel_selected",
    "service_selected",
    "back_to_lang",
    "back_to_fuel",
    "repeat_lang_prompt",
    "repeat_fuel_prompt",
    "repeat_service_prompt",
]


# ────────────────────── entry point ──────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/start entry point."""
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await update.effective_message.reply_text(
        t("choose_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


# ─────────────────── callback handlers ───────────────────
async def language_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle chosen language."""
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_", maxsplit=1)[1]
    ctx.user_data["lang"] = lang
    user = update.effective_user
    upsert_user(user.id, lang)
    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    await query.edit_message_text(
        t("choose_fuel", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_FUEL


async def fuel_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle chosen fuel."""
    query = update.callback_query
    await query.answer()
    fuel = query.data.split("_", maxsplit=1)[1]
    ctx.user_data["fuel"] = fuel
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(s, f"serv_{s}") for s in SERVICE_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_lang")])
    await query.edit_message_text(
        t("choose_service", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_SERVICE


async def service_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle chosen service (end of flow)."""
    query = update.callback_query
    await query.answer()
    service = query.data.split("_", maxsplit=1)[1]
    ctx.user_data["service"] = service
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    await query.edit_message_text(t("searching", lang))
    # … start search job here …
    return ConversationHandler.END


# ───────────── navigation “back” callbacks ──────────────
async def back_to_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Go back to language selection."""
    query = update.callback_query
    await query.answer()
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await query.edit_message_text(
        t("choose_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


async def back_to_fuel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Go back to fuel selection."""
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    await query.edit_message_text(
        t("choose_fuel", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_FUEL


# ──────────── “repeat prompt” catch-all handlers ────────────
async def repeat_lang_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Repeat language keyboard when user sends unrelated content."""
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await update.effective_message.reply_text(
        t("choose_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


async def repeat_fuel_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Repeat fuel keyboard when user sends unrelated content."""
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_lang")])
    await update.effective_message.reply_text(
        t("choose_fuel", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_FUEL


async def repeat_service_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Repeat service keyboard when user sends unrelated content."""
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(s, f"serv_{s}") for s in SERVICE_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_fuel")])
    await update.effective_message.reply_text(
        t("choose_service", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_SERVICE
