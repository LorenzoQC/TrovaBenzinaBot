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

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, SERVICE_MAP, LANGUAGE_MAP
from trovabenzina.db.crud import get_user, upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import inline_kb, STEP_PROFILE_MENU, STEP_PROFILE_LANGUAGE, STEP_PROFILE_FUEL, \
    STEP_PROFILE_SERVICE

__all__ = ["profile_handler"]


async def exit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _build_profile_keyboard(locale: str) -> InlineKeyboardMarkup:
    """Inline keyboard with the three *edit* actions, one per row."""
    items = [
        (t("edit_language", locale), "profile_set_language"),
        (t("edit_fuel", locale), "profile_set_fuel"),
        (t("edit_service", locale), "profile_set_service"),
    ]
    return InlineKeyboardMarkup(inline_kb(items, per_row=1))

async def _get_or_create_defaults(uid: int, username: str) -> tuple[str, str, str]:
    """Return user's (fuel, service, language) or set defaults."""
    row = await get_user(uid)
    if row is not None:
        if isinstance(row, Mapping) or hasattr(row, "keys"):
            fuel_code = row["fuel_code"]
            service_code = row["service_code"]
            lang_code = row["lang_code"]
        else:
            seq = list(row)
            if len(seq) == 3:
                fuel_code, service_code, lang_code = seq
            else:
                _, fuel_code, service_code, lang_code = seq
        return fuel_code, service_code, lang_code or DEFAULT_LANGUAGE

    # bootstrap defaults
    fuel_code = next(iter(FUEL_MAP.values()))
    service_code = next(iter(SERVICE_MAP.values()))
    await upsert_user(uid, username, fuel_code, service_code, DEFAULT_LANGUAGE)
    return fuel_code, service_code, DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# BACK BUTTON HANDLER
# ---------------------------------------------------------------------------

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '↩' callback by returning to the main profile menu."""
    query = update.callback_query
    await query.answer()

    # retrieve current settings from DB or defaults
    uid = update.effective_user.id
    username = update.effective_user.username
    fuel_code, service_code, lang_code = await _get_or_create_defaults(uid, username)

    # prepare human-readable labels
    lang_name = LANGUAGE_MAP.get(
        lang_code,
        next((n for n, c in LANGUAGE_MAP.items() if c == lang_code), lang_code)
    )
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    service_name_key = next((n for n, c in SERVICE_MAP.items() if c == service_code), service_code)
    fuel_label = t(fuel_name_key, lang_code)
    service_label = t(service_name_key, lang_code)

    summary = (
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}\n"
        f"{t('service', lang_code)}: {service_label}"
    )

    # edit the message to show the main menu again
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
    fuel_code, service_code, lang_code = await _get_or_create_defaults(uid, username)

    context.user_data["lang"] = lang_code

    # human-readable labels
    lang_name = LANGUAGE_MAP.get(
        lang_code,
        next((n for n, c in LANGUAGE_MAP.items() if c == lang_code), lang_code)
    )
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    service_name_key = next((n for n, c in SERVICE_MAP.items() if c == service_code), service_code)
    fuel_label = t(fuel_name_key, lang_code)
    service_label = t(service_name_key, lang_code)

    summary = (
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}\n"
        f"{t('service', lang_code)}: {service_label}"
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
async def ask_language(update: Update, context: CallbackContext) -> int:
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

async def save_language(update: Update, context: CallbackContext) -> int:
    """Save new language and show confirmation + profile menu in one message."""
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    username = update.effective_user.username
    new_code = query.data.split(":", 1)[1]

    # persist new language
    fuel_code, service_code, _ = await _get_or_create_defaults(uid, username)
    await upsert_user(uid, username, fuel_code, service_code, new_code)
    context.user_data["lang"] = new_code

    # rebuild profile summary
    lang_name = LANGUAGE_MAP.get(new_code, next((n for n, c in LANGUAGE_MAP.items() if c == new_code), new_code))
    fuel_name = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    service_name = next((n for n, c in SERVICE_MAP.items() if c == service_code), service_code)
    summary = (
        f"{t('language_updated', new_code)}\n\n"
        f"{t('language', new_code)}: {lang_name}\n"
        f"{t('fuel', new_code)}: {fuel_name}\n"
        f"{t('service', new_code)}: {service_name}"
    )
    await query.edit_message_text(
        summary,
        reply_markup=_build_profile_keyboard(new_code),
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
    _, service_code, lang_code = await _get_or_create_defaults(uid, username)

    await upsert_user(uid, username, new_fuel, service_code, lang_code)

    # rebuild profile summary
    lang_name = LANGUAGE_MAP.get(lang_code, lang_code)
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == new_fuel), new_fuel)
    service_name_key = next((n for n, c in SERVICE_MAP.items() if c == service_code), service_code)
    fuel_label = t(fuel_name_key, lang_code)
    service_label = t(service_name_key, lang_code)

    summary = (
        f"{t('fuel_updated', lang_code)}\n\n"
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}\n"
        f"{t('service', lang_code)}: {service_label}"
    )
    await query.edit_message_text(
        summary,
        reply_markup=_build_profile_keyboard(lang_code),
    )
    context.chat_data["current_state"] = STEP_PROFILE_MENU
    return STEP_PROFILE_MENU

# ---------------------------------------------------------------------------
# Service flow
# ---------------------------------------------------------------------------
async def ask_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = STEP_PROFILE_SERVICE
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    items = [
        (t(name, lang), f"set_service:{code}")
        for name, code in SERVICE_MAP.items()
    ]
    rows = inline_kb(items, per_row=2)
    rows.append([InlineKeyboardButton("↩", callback_data="profile")])

    await query.edit_message_text(
        t("select_service", lang),
        reply_markup=InlineKeyboardMarkup(rows),
    )
    return STEP_PROFILE_SERVICE


async def save_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save new service and show confirmation + profile menu in one message."""
    query = update.callback_query
    await query.answer()

    uid = update.effective_user.id
    username = update.effective_user.username
    new_service = query.data.split(":", 1)[1]
    fuel_code, _, lang_code = await _get_or_create_defaults(uid, username)

    await upsert_user(uid, username, fuel_code, new_service, lang_code)

    # rebuild profile summary
    lang_name = LANGUAGE_MAP.get(lang_code, lang_code)
    fuel_name_key = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    service_name_key = next((n for n, c in SERVICE_MAP.items() if c == new_service), new_service)
    fuel_label = t(fuel_name_key, lang_code)
    service_label = t(service_name_key, lang_code)

    summary = (
        f"{t('service_updated', lang_code)}\n\n"
        f"{t('language', lang_code)}: {lang_name}\n"
        f"{t('fuel', lang_code)}: {fuel_label}\n"
        f"{t('service', lang_code)}: {service_label}"
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
    return await ask_service(update, context)

# ---------------------------------------------------------------------------
# Conversation definition
# ---------------------------------------------------------------------------
profile_handler = ConversationHandler(
    entry_points=[CommandHandler("profile", profile_ep)],
    states={
        STEP_PROFILE_MENU: [
            CallbackQueryHandler(ask_language, pattern="^profile_set_language$"),
            CallbackQueryHandler(ask_fuel, pattern="^profile_set_fuel$"),
            CallbackQueryHandler(ask_service, pattern="^profile_set_service$"),
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
        STEP_PROFILE_SERVICE: [
            CallbackQueryHandler(back_to_menu, pattern="^profile$"),
            CallbackQueryHandler(save_service, pattern="^set_service:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
    },
    fallbacks=[
        MessageHandler(filters.COMMAND, exit_profile),
    ],
    block=False,
    allow_reentry=True,
)
