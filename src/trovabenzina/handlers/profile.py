from __future__ import annotations

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler,
)

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, SERVICE_MAP, LANGUAGE_MAP
from trovabenzina.db.crud import get_user, upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import inline_kb

__all__ = [
    "profile_handler"
]


# Conversation states
LANG_SELECT, FUEL_SELECT, SERVICE_SELECT = range(3)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _keyboard_full_width(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """Return an inline keyboard where each button occupies its own row."""
    return InlineKeyboardMarkup(rows)


def _build_profile_keyboard(locale: str) -> InlineKeyboardMarkup:
    """Build the profile menu keyboard."""
    items = [
        (t("edit_language", locale), "profile_set_language"),
        (t("edit_fuel", locale), "profile_set_fuel"),
        (t("edit_service", locale), "profile_set_service"),
    ]
    # one button per row
    return InlineKeyboardMarkup(inline_kb(items, per_row=1))


async def _get_or_create_defaults(uid: int) -> tuple[str, str, str]:
    """
    Return user's current preferences or set defaults if none exist.
    """
    row = await get_user(uid)
    if row:
        fuel_code, service_code, lang_code = row
    else:
        # defaults: first keys from maps
        lang_code = DEFAULT_LANGUAGE
        fuel_code = next(iter(FUEL_MAP.values()))
        service_code = next(iter(SERVICE_MAP.values()))
        await upsert_user(uid, fuel_code, service_code, lang_code)
    return fuel_code, service_code, lang_code

# ---------------------------------------------------------------------------
# /profile entry point
# ---------------------------------------------------------------------------

async def profile_ep(update: Update, context: CallbackContext) -> int:
    uid = update.effective_user.id
    fuel_code, service_code, lang_code = await _get_or_create_defaults(uid)

    # Cache language for prompts
    context.user_data["lang"] = lang_code

    # Reverse-labels: code -> display name
    fuel_name = next((name for name, code in FUEL_MAP.items() if code == fuel_code), fuel_code)
    service_name = next((name for name, code in SERVICE_MAP.items() if code == service_code), service_code)
    lang_name = LANGUAGE_MAP.get(lang_code, lang_code)

    summary = (
        f"• {t('language', lang_code)}: {lang_name}\n"
        f"• {t('fuel', lang_code)}: {fuel_name}\n"
        f"• {t('service', lang_code)}: {service_name}"
    )

    await update.message.reply_text(summary, reply_markup=_build_profile_keyboard(lang_code))
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# Language flow
# ---------------------------------------------------------------------------

async def ask_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = LANG_SELECT
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    # build buttons from LANGUAGE_MAP
    kb = [[InlineKeyboardButton(name, callback_data=f"set_lang:{code}")]
          for code, name in LANGUAGE_MAP.items()]
    await query.edit_message_text(
        t("profile.select_language", lang), reply_markup=_keyboard_full_width(kb)
    )
    return LANG_SELECT


async def save_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    new_code = query.data.split(":", 1)[1]

    # fetch existing prefs
    fuel_code, service_code, _ = await _get_or_create_defaults(uid)
    # upsert with new language
    await upsert_user(uid, fuel_code, service_code, new_code)
    context.user_data["lang"] = new_code

    await query.edit_message_text(t("profile.language_saved", new_code))
    # show updated summary
    await profile_ep(update, context)
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# Fuel flow
# ---------------------------------------------------------------------------

async def ask_fuel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = FUEL_SELECT
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    # build buttons from FUEL_MAP
    kb = [[InlineKeyboardButton(name, callback_data=f"set_fuel:{code}")]
          for name, code in FUEL_MAP.items()]
    await query.edit_message_text(
        t("profile.select_fuel", lang), reply_markup=_keyboard_full_width(kb)
    )
    return FUEL_SELECT


async def save_fuel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    new_fuel = query.data.split(":", 1)[1]

    # fetch existing prefs
    _, service_code, lang_code = await _get_or_create_defaults(uid)
    await upsert_user(uid, new_fuel, service_code, lang_code)

    await query.edit_message_text(t("profile.fuel_saved", lang_code))
    await profile_ep(update, context)
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# Service flow
# ---------------------------------------------------------------------------

async def ask_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    context.chat_data["current_state"] = SERVICE_SELECT
    lang = context.user_data.get("lang", DEFAULT_LANGUAGE)

    # build buttons from SERVICE_MAP
    kb = [[InlineKeyboardButton(name, callback_data=f"set_service:{code}")]
          for name, code in SERVICE_MAP.items()]
    await query.edit_message_text(
        t("profile.select_service", lang), reply_markup=_keyboard_full_width(kb)
    )
    return SERVICE_SELECT

async def save_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    new_service = query.data.split(":", 1)[1]

    # fetch existing prefs
    fuel_code, _, lang_code = await _get_or_create_defaults(uid)
    await upsert_user(uid, fuel_code, new_service, lang_code)

    await query.edit_message_text(t("profile.service_saved", lang_code))
    await profile_ep(update, context)
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# Invalid text handler
# ---------------------------------------------------------------------------

async def invalid_text(update: Update, context: CallbackContext) -> int:
    state = context.chat_data.get("current_state")
    prompt_keys = {
        LANG_SELECT: "profile.select_language",
        FUEL_SELECT: "profile.select_fuel",
        SERVICE_SELECT: "profile.select_service",
    }
    # repeat last prompt
    return await ask_language(update, context) if state == LANG_SELECT else (
        await ask_fuel(update, context) if state == FUEL_SELECT else (
            await ask_service(update, context)
        )
    )


profile_handler = ConversationHandler(
    entry_points=[CommandHandler("profile", profile_ep)],
    states={
        # handlers must be registered in bot.py via CommandHandler("profile", profile_entry),
        LANG_SELECT: [
            CallbackQueryHandler(ask_language, pattern="^profile_set_language$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        FUEL_SELECT: [
            CallbackQueryHandler(ask_fuel, pattern="^profile_set_fuel$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
        SERVICE_SELECT: [
            CallbackQueryHandler(ask_service, pattern="^profile_set_service$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_text),
        ],
    },
    fallbacks=[],
    block=False,
)
