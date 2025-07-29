from __future__ import annotations

from collections.abc import Mapping

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, SERVICE_MAP, LANGUAGE_MAP
from trovabenzina.db.crud import get_user, upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import inline_kb

__all__ = ["profile_handler"]

# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------
MENU, LANG_SELECT, FUEL_SELECT, SERVICE_SELECT = range(4)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _keyboard_full_width(
        rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:  # noqa: D401 – short description ok
    """Return an inline keyboard where each button occupies its own row."""
    return InlineKeyboardMarkup(rows)


def _build_profile_keyboard(locale: str) -> InlineKeyboardMarkup:
    """Inline keyboard with the three *edit* actions."""
    items = [
        (t("edit_language", locale), "profile_set_language"),
        (t("edit_fuel", locale), "profile_set_fuel"),
        (t("edit_service", locale), "profile_set_service"),
    ]
    return InlineKeyboardMarkup(inline_kb(items, per_row=1))


async def _get_or_create_defaults(uid: int, username: str) -> tuple[str, str, str]:
    """Return the user's (fuel, service, language) or create defaults if none exist.

    Works with whatever shape the row comes in (SQLAlchemy RowMapping or a plain
    tuple of length 3/4).
    """
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
            elif len(seq) == 4:
                _, fuel_code, service_code, lang_code = seq
            else:
                raise ValueError("Unexpected user row format")
        return fuel_code, service_code, lang_code or DEFAULT_LANGUAGE

    # no record yet – bootstrap with sensible defaults
    fuel_code = next(iter(FUEL_MAP.values()))
    service_code = next(iter(SERVICE_MAP.values()))
    await upsert_user(uid, username, fuel_code, service_code, DEFAULT_LANGUAGE)
    return fuel_code, service_code, DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# /profile entry-point
# ---------------------------------------------------------------------------
async def profile_ep(update: Update, context: CallbackContext) -> int:  # noqa: D401 – imperative mood
    """Send profile summary + edit buttons; enter MENU state."""
    uid = update.effective_user.id
    username = update.effective_user.username
    fuel_code, service_code, lang_code = await _get_or_create_defaults(uid, username)

    # cache language for subsequent prompts
    context.user_data["lang"] = lang_code

    # human-readable labels
    if lang_code in LANGUAGE_MAP:
        lang_name = LANGUAGE_MAP[lang_code]
    else:  # LANGUAGE_MAP could be name→code
        lang_name = next((n for n, c in LANGUAGE_MAP.items() if c == lang_code), lang_code)

    fuel_name = next((n for n, c in FUEL_MAP.items() if c == fuel_code), fuel_code)
    service_name = next((n for n, c in SERVICE_MAP.items() if c == service_code), service_code)

    summary = (
        f"• {t('language', lang_code)}: {lang_name}\n"
        f"• {t('fuel', lang_code)}: {fuel_name}\n"
        f"• {t('service', lang_code)}: {service_name}"
    )

    await update.effective_message.reply_text(summary, reply_markup=_build_profile_keyboard(lang_code))
    context.chat_data["current_state"] = MENU
    return MENU


# ---------------------------------------------------------------------------
# Language flow
# ---------------------------------------------------------------------------
async def ask_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = LANG_SELECT
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    rows: list[list[InlineKeyboardButton]] = []
    for key, value in LANGUAGE_MAP.items():
        # Support both code→name and name→code maps
        if len(key) <= 3 and key.isalpha():  # typical ISO code
            code, name = key, value
        else:
            name, code = key, value
        rows.append([InlineKeyboardButton(name, callback_data=f"set_lang:{code}")])

    await query.edit_message_text(t("profile.select_language", lang), reply_markup=_keyboard_full_width(rows))
    return LANG_SELECT


async def save_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    username = update.effective_user.username
    new_code = query.data.split(":", 1)[1]

    fuel_code, service_code, _ = await _get_or_create_defaults(uid, username)
    await upsert_user(uid, username, fuel_code, service_code, new_code)
    context.user_data["lang"] = new_code

    await query.edit_message_text(t("profile.language_saved", new_code))
    return await profile_ep(update, context)


# ---------------------------------------------------------------------------
# Fuel flow
# ---------------------------------------------------------------------------
async def ask_fuel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = FUEL_SELECT
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    kb = [[InlineKeyboardButton(name, callback_data=f"set_fuel:{code}")]
          for name, code in FUEL_MAP.items()]
    await query.edit_message_text(t("profile.select_fuel", lang), reply_markup=_keyboard_full_width(kb))
    return FUEL_SELECT


async def save_fuel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    username = update.effective_user.username
    new_fuel = query.data.split(":", 1)[1]

    _, service_code, lang_code = await _get_or_create_defaults(uid, username)
    await upsert_user(uid, username, new_fuel, service_code, lang_code)

    await query.edit_message_text(t("profile.fuel_saved", lang_code))
    return await profile_ep(update, context)


# ---------------------------------------------------------------------------
# Service flow
# ---------------------------------------------------------------------------
async def ask_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = SERVICE_SELECT
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    kb = [[InlineKeyboardButton(name, callback_data=f"set_service:{code}")]
          for name, code in SERVICE_MAP.items()]
    await query.edit_message_text(t("profile.select_service", lang), reply_markup=_keyboard_full_width(kb))
    return SERVICE_SELECT


async def save_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    username = update.effective_user.username
    new_service = query.data.split(":", 1)[1]

    fuel_code, _, lang_code = await _get_or_create_defaults(uid, username)
    await upsert_user(uid, username, fuel_code, new_service, lang_code)

    await query.edit_message_text(t("profile.service_saved", lang_code))
    return await profile_ep(update, context)


# ---------------------------------------------------------------------------
# Invalid text handler (keeps UX bullet‑proof)
# ---------------------------------------------------------------------------
async def invalid_text(update: Update, context: CallbackContext) -> int:
    state = context.chat_data.get("current_state", MENU)
    if state == MENU:
        return await profile_ep(update, context)
    if state == LANG_SELECT:
        return await ask_language(update, context)
    if state == FUEL_SELECT:
        return await ask_fuel(update, context)
    # SERVICE_SELECT fallback
    return await ask_service(update, context)


# ---------------------------------------------------------------------------
# Conversation definition – plug into the application
# ---------------------------------------------------------------------------
profile_handler = ConversationHandler(
    entry_points=[CommandHandler("profile", profile_ep)],
    states={
        MENU: [
            CallbackQueryHandler(ask_language, pattern="^profile_set_language$"),
            CallbackQueryHandler(ask_fuel, pattern="^profile_set_fuel$"),
            CallbackQueryHandler(ask_service, pattern="^profile_set_service$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        LANG_SELECT: [
            CallbackQueryHandler(save_language, pattern="^set_lang:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        FUEL_SELECT: [
            CallbackQueryHandler(save_fuel, pattern="^set_fuel:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        SERVICE_SELECT: [
            CallbackQueryHandler(save_service, pattern="^set_service:"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
    },
    fallbacks=[],
    block=False,
)
