from __future__ import annotations

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
)

from trovabenzina.core import db
from trovabenzina.i18n import t

# Conversation states
LANG_SELECT, FUEL_SELECT, SERVICE_SELECT = range(3)

# Lookup tables for pretty printing -------------------------------------------------
FUEL_LABELS = {
    "gasoline": "Benzina ⛽️",
    "diesel": "Diesel ⛽️",
    "lpg": "GPL",
    "cng": "Metano",
}
SERVICE_LABELS = {
    "self": "Self",
    "served": "Servito",
    "all": "Tutti",
}
LANG_LABELS = {
    "it": "Italiano 🇮🇹",
    "en": "English 🇬🇧",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _keyboard_full_width(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """Return an inline keyboard where *each* button occupies one row."""
    return InlineKeyboardMarkup(rows)


def _build_profile_keyboard(locale: str) -> InlineKeyboardMarkup:
    """Profile menu without the old “favourites” button.

    Each of the three remaining buttons takes an entire row, as requested.
    """
    return _keyboard_full_width(
        [
            [InlineKeyboardButton(t("edit_language", locale), callback_data="profile_set_language")],
            [InlineKeyboardButton(t("edit_fuel", locale), callback_data="profile_set_fuel")],
            [InlineKeyboardButton(t("edit_service", locale), callback_data="profile_set_service")],
        ]
    )


async def _repeat_last_prompt(update: Update, context: CallbackContext, prompt_key: str) -> int:
    """Send the same prompt again when user types random text."""
    locale: str = context.user_data.get("lang", "it")
    await update.message.reply_text(t(prompt_key, locale))
    return context.chat_data["current_state"]


async def _update_single_pref(uid: int, field: str, value: str):
    """Update *one* column inside the `users` table.

    The `field` argument is *not* interpolated – it is whitelisted by caller to
    avoid SQL‑injection.
    """
    assert field in {"fuel", "service", "language"}
    await db.execute(f"UPDATE users SET {field} = $1 WHERE user_id = $2", value, uid)


async def _get_or_create_defaults(uid: int):
    """Return user's current prefs or sensible defaults if none found."""
    row = await db.get_user(uid)
    if row:
        fuel, service, language = row
    else:
        # Defaults match what /start would choose on first run
        fuel, service, language = "gasoline", "self", "it"
        await db.upsert_user(uid, fuel, service, language)
    return fuel, service, language


# ---------------------------------------------------------------------------
# /profile entry point
# ---------------------------------------------------------------------------

async def profile_entry(update: Update, context: CallbackContext) -> None:
    uid = update.effective_user.id
    fuel, service, language = await _get_or_create_defaults(uid)

    # Cache the current language for later prompts
    context.user_data["lang"] = language

    summary = (
        f"• {t('language', language)}: {LANG_LABELS.get(language, language)}\n"
        f"• {t('fuel', language)}: {FUEL_LABELS.get(fuel, fuel)}\n"
        f"• {t('service', language)}: {SERVICE_LABELS.get(service, service)}"
    )

    await update.message.reply_text(summary, reply_markup=_build_profile_keyboard(language))


# ---------------------------------------------------------------------------
# Language flow
# ---------------------------------------------------------------------------

async def ask_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    context.chat_data["current_state"] = LANG_SELECT
    locale: str = context.user_data.get("lang", "it")

    keyboard = [
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data="set_lang:it")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang:en")],
    ]

    await query.edit_message_text(t("profile.select_language", locale), reply_markup=_keyboard_full_width(keyboard))
    return LANG_SELECT


async def save_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split(":", 1)[1]
    uid = update.effective_user.id
    await _update_single_pref(uid, "language", lang_code)
    context.user_data["lang"] = lang_code

    await query.edit_message_text(t("profile.language_saved", lang_code))
    # Refresh profile summary
    await profile_entry(update, context)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Fuel flow
# ---------------------------------------------------------------------------

async def ask_fuel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    context.chat_data["current_state"] = FUEL_SELECT
    locale: str = context.user_data.get("lang", "it")

    fuels = [
        (FUEL_LABELS["gasoline"], "gasoline"),
        (FUEL_LABELS["diesel"], "diesel"),
        (FUEL_LABELS["lpg"], "lpg"),
        (FUEL_LABELS["cng"], "cng"),
    ]
    keyboard = [[InlineKeyboardButton(label, callback_data=f"set_fuel:{code}")] for label, code in fuels]

    await query.edit_message_text(t("profile.select_fuel", locale), reply_markup=_keyboard_full_width(keyboard))
    return FUEL_SELECT


async def save_fuel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    fuel_code = query.data.split(":", 1)[1]
    uid = update.effective_user.id
    await _update_single_pref(uid, "fuel", fuel_code)

    locale: str = context.user_data.get("lang", "it")
    await query.edit_message_text(t("profile.fuel_saved", locale))
    await profile_entry(update, context)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Service flow
# ---------------------------------------------------------------------------

async def ask_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    context.chat_data["current_state"] = SERVICE_SELECT
    locale: str = context.user_data.get("lang", "it")

    services = [
        (SERVICE_LABELS["self"], "self"),
        (SERVICE_LABELS["served"], "served"),
        (SERVICE_LABELS["all"], "all"),
    ]
    keyboard = [[InlineKeyboardButton(label, callback_data=f"set_service:{code}")]
                for label, code in services]

    await query.edit_message_text(t("profile.select_service", locale), reply_markup=_keyboard_full_width(keyboard))
    return SERVICE_SELECT


async def save_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    service_code = query.data.split(":", 1)[1]
    uid = update.effective_user.id
    await _update_single_pref(uid, "service", service_code)

    locale: str = context.user_data.get("lang", "it")
    await query.edit_message_text(t("profile.service_saved", locale))
    await profile_entry(update, context)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Random text handler – repeat prompt
# ---------------------------------------------------------------------------

async def invalid_text(update: Update, context: CallbackContext) -> int:
    state: int = context.chat_data.get("current_state")
    prompt_keys = {
        LANG_SELECT: "profile.select_language",
        FUEL_SELECT: "profile.select_fuel",
        SERVICE_SELECT: "profile.select_service",
    }
    return await _repeat_last_prompt(update, context, prompt_keys[state])
