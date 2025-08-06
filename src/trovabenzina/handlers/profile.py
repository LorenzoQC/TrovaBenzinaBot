from __future__ import annotations

from collections.abc import Mapping

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters, ContextTypes,
)

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, LANGUAGE_MAP
from trovabenzina.db.crud import get_user, upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import inline_kb, STEP_PROFILE_MENU, STEP_PROFILE_LANGUAGE, STEP_PROFILE_FUEL

__all__ = ["profile_handler"]


async def exit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _build_profile_keyboard(locale: str) -> InlineKeyboardMarkup:
    """Inline keyboard with edit actions: language and fuel."""
    items = [
        (t("edit_language", locale), "profile_set_language"),
        (t("edit_fuel", locale), "profile_set_fuel"),
    ]
    return InlineKeyboardMarkup(inline_kb(items, per_row=1))


async def _get_or_create_defaults(uid: int, username: str) -> tuple[str, str]:
    """Return user's (fuel, language) or set defaults."""
    row = await get_user(uid)
    if row is not None:
        if isinstance(row, Mapping) or hasattr(row, "keys"):
            fuel_code = row["fuel_code"]
            lang_code = row["lang_code"]
        else:
            seq = list(row)
            # row structure: (fuel_code, lang_code)
            fuel_code, lang_code = seq
        return fuel_code, lang_code or DEFAULT_LANGUAGE

    # bootstrap defaults
    fuel_code = next(iter(FUEL_MAP.values()))
    await upsert_user(uid, username, fuel_code, DEFAULT_LANGUAGE)
    return fuel_code, DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# BACK BUTTON HANDLER
# ---------------------------------------------------------------------------

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '↩' callback by returning to the main profile menu."""
    query = update.callback_query
    await query.answer()

    uid = update.effective_user.id
    username = update.effective_user.username
    fuel_code, lang_code = await _get_or_create_defaults(uid, username)

    lang_name = LANGUAGE_MAP.get(
        lang_code,
        next((n for n, c in LANGUAGE_MAP.items() if c == lang_code), lang_code)
    )
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    fuel_label = t(fuel_name_key, lang_code)

    summary = (
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}"
    )

    await query.edit_message_text(
        summary,
        reply_markup=_build_profile_keyboard(lang_code),
    )
    context.chat_data["current_state"] = STEP_PROFILE_MENU
    return STEP_PROFILE_MENU

# ---------------------------------------------------------------------------
# /profile entry-point
# ---------------------------------------------------------------------------
async def profile_ep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    username = update.effective_user.username
    fuel_code, lang_code = await _get_or_create_defaults(uid, username)

    context.user_data["lang"] = lang_code

    lang_name = LANGUAGE_MAP.get(
        lang_code,
        next((n for n, c in LANGUAGE_MAP.items() if c == lang_code), lang_code)
    )
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    fuel_label = t(fuel_name_key, lang_code)

    summary = (
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}"
    )

    await update.effective_message.reply_text(
        summary,
        reply_markup=_build_profile_keyboard(lang_code),
    )
    context.chat_data["current_state"] = STEP_PROFILE_MENU
    return STEP_PROFILE_MENU

# ---------------------------------------------------------------------------
# Language flow
# ---------------------------------------------------------------------------
async def ask_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = STEP_PROFILE_LANGUAGE
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    items = [
        (name, f"set_lang:{code}")
        for name, code in LANGUAGE_MAP.items()
    ]
    rows = inline_kb(items, per_row=2)
    rows.append([InlineKeyboardButton("↩", callback_data="profile")])

    await query.edit_message_text(
        t("select_language", lang),
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return STEP_PROFILE_LANGUAGE


async def save_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save new language and show confirmation + profile menu in one message."""
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    username = update.effective_user.username
    new_lang = query.data.split(":", 1)[1]

    # persist new language
    fuel_code = (await _get_or_create_defaults(uid, username))[:2]
    await upsert_user(uid, username, fuel_code, new_lang)
    context.user_data["lang"] = new_lang

    lang_name = LANGUAGE_MAP.get(
        new_lang,
        next((n for n, c in LANGUAGE_MAP.items() if c == new_lang), new_lang)
    )
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    fuel_label = t(fuel_name_key, new_lang)

    summary = (
        f"{t('language_updated', new_lang)}\n\n"
        f"{t('language', new_lang)}: {lang_name}\n"
        f"{t('fuel', new_lang)}: {fuel_label}"
    )
    await query.edit_message_text(
        summary,
        reply_markup=_build_profile_keyboard(new_lang),
    )
    context.chat_data["current_state"] = STEP_PROFILE_MENU
    return STEP_PROFILE_MENU

# ---------------------------------------------------------------------------
# Fuel flow
# ---------------------------------------------------------------------------
async def ask_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = STEP_PROFILE_FUEL
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    items = [
        (t(name, lang), f"set_fuel:{code}")
        for name, code in FUEL_MAP.items()
    ]
    rows = inline_kb(items, per_row=2)
    rows.append([InlineKeyboardButton("↩", callback_data="profile")])

    await query.edit_message_text(
        t("select_fuel", lang),
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return STEP_PROFILE_FUEL

async def save_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save new fuel and show confirmation + profile menu in one message."""
    query = update.callback_query
    await query.answer()

    uid = update.effective_user.id
    username = update.effective_user.username
    new_fuel = query.data.split(":", 1)[1]

    # persist new fuel
    _, lang_code = await _get_or_create_defaults(uid, username)
    await upsert_user(uid, username, new_fuel, lang_code)

    lang_name = LANGUAGE_MAP.get(
        lang_code,
        next((n for n, c in LANGUAGE_MAP.items() if c == lang_code), lang_code)
    )
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == new_fuel), new_fuel)
    fuel_label = t(fuel_name_key, lang_code)

    summary = (
        f"{t('fuel_updated', lang_code)}\n\n"
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}"
    )
    await query.edit_message_text(
        summary,
        reply_markup=_build_profile_keyboard(lang_code),
    )
    context.chat_data["current_state"] = STEP_PROFILE_MENU
    return STEP_PROFILE_MENU

# ---------------------------------------------------------------------------
# Invalid text handler
# ---------------------------------------------------------------------------
async def invalid_text(update: Update, context: CallbackContext) -> int:
    state = context.chat_data.get("current_state", STEP_PROFILE_MENU)
    if state == STEP_PROFILE_MENU:
        return ConversationHandler.END
    if state == STEP_PROFILE_LANGUAGE:
        return await ask_language(update, context)
    if state == STEP_PROFILE_FUEL:
        return await ask_fuel(update, context)
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# Conversation definition
# ---------------------------------------------------------------------------
profile_handler = ConversationHandler(
    entry_points=[CommandHandler("profile", profile_ep)],
    states={
        STEP_PROFILE_MENU: [
            CallbackQueryHandler(ask_language, pattern="^profile_set_language$"),
            CallbackQueryHandler(ask_fuel, pattern="^profile_set_fuel$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        STEP_PROFILE_LANGUAGE: [
            CallbackQueryHandler(back_to_menu, pattern="^profile$"),
            CallbackQueryHandler(save_language, pattern="^set_lang:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        STEP_PROFILE_FUEL: [
            CallbackQueryHandler(back_to_menu, pattern="^profile$"),
            CallbackQueryHandler(save_fuel, pattern="^set_fuel:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
    },
    fallbacks=[
        MessageHandler(filters.COMMAND, exit_profile),
    ],
    block=False,
    allow_reentry=True,
)
