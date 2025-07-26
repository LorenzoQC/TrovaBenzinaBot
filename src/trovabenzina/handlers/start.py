from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, \
    filters

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, LANGUAGES, SERVICE_MAP
from trovabenzina.core.db import upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_FUEL, STEP_LANG, STEP_SERVICE, inline_kb

__all__ = [
    "start_conv",
]


# ────────────────────── entry point ──────────────────────
async def start_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/start entry point."""
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await update.effective_message.reply_text(
        t("select_language", DEFAULT_LANGUAGE),
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

    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_lang")])
    await query.edit_message_text(
        t("select_fuel", lang),
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
    kb.append([InlineKeyboardButton("↩", callback_data="back_fuel")])
    await query.edit_message_text(
        t("select_service", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_SERVICE


async def service_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle chosen service (end of flow)."""
    query = update.callback_query
    await query.answer()

    service = query.data.split("_", maxsplit=1)[1]
    ctx.user_data["service"] = service
    lang = ctx.user_data["lang"]
    fuel = ctx.user_data["fuel"]
    user_id = update.effective_user.id

    await upsert_user(user_id, fuel, service, lang)

    await query.edit_message_text(t("profile_saved", lang))
    return ConversationHandler.END


# ───────────── navigation “back” callbacks ──────────────
async def back_to_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Go back to language selection."""
    query = update.callback_query
    await query.answer()
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await query.edit_message_text(
        t("select_language", DEFAULT_LANGUAGE),
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
        t("select_fuel", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_FUEL


# ──────────── “repeat prompt” catch-all handlers ────────────
async def repeat_lang_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Repeat language keyboard when user sends unrelated content."""
    kb = inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await update.effective_message.reply_text(
        t("select_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


async def repeat_fuel_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Repeat fuel keyboard when user sends unrelated content."""
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_lang")])
    await update.effective_message.reply_text(
        t("select_fuel", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_FUEL


async def repeat_service_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Repeat service keyboard when user sends unrelated content."""
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = inline_kb([(s, f"serv_{s}") for s in SERVICE_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_fuel")])
    await update.effective_message.reply_text(
        t("select_service", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_SERVICE


# ── ConversationHandler object ───────────────────────────────────────────
start_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start_ep)],
    states={
        STEP_LANG: [
            CallbackQueryHandler(language_selected, pattern="^lang_"),
            MessageHandler(filters.ALL, repeat_lang_prompt),
        ],
        STEP_FUEL: [
            CallbackQueryHandler(fuel_selected, pattern="^fuel_"),
            CallbackQueryHandler(back_to_lang, pattern="^back_lang$"),
            MessageHandler(filters.ALL, repeat_fuel_prompt),
        ],
        STEP_SERVICE: [
            CallbackQueryHandler(service_selected, pattern="^serv_"),
            CallbackQueryHandler(back_to_fuel, pattern="^back_fuel$"),
            MessageHandler(filters.ALL, repeat_service_prompt),
        ],
    },
    fallbacks=[],
    block=True,
)
