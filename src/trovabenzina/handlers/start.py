from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, SERVICE_MAP, LANGUAGE_MAP
from trovabenzina.db.crud import upsert_user
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_FUEL, STEP_LANG, STEP_SERVICE, inline_kb

# Invert mappings: code -> label
FUEL_CHOICES_MAP = {code: label for label, code in FUEL_MAP.items()}
SERVICE_CHOICES_MAP = {code: label for label, code in SERVICE_MAP.items()}
LANGUAGE_CHOICES_MAP = {code: label for label, code in LANGUAGE_MAP.items()}

__all__ = [
    "start_handler",
]


def build_keyboard(choices, prefix, back_callback=None):
    """
    Build an InlineKeyboardMarkup from choices.
    :param choices: iterable of (key, label)
    :param prefix: callback_data prefix, e.g. 'lang', 'fuel', 'serv'
    :param back_callback: callback_data for the back button (optional)
    """
    kb = inline_kb([(label, f"{prefix}_{key}") for key, label in choices])
    if back_callback:
        kb.append([InlineKeyboardButton("↩", callback_data=back_callback)])
    return kb


def make_selection_handler(
        choices_map,
        data_key,
        prompt_key,
        callback_prefix,
        next_state,
        back_callback=None,
):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        # extract selected value
        value = query.data.split("_", 1)[1]
        ctx.user_data[data_key] = value

        # if it's the final step, save profile and end
        if data_key == "service":
            await upsert_user(
                update.effective_user.id,
                ctx.user_data["fuel"],
                ctx.user_data["service"],
                ctx.user_data["lang"],
            )
            await query.edit_message_text(t("profile_saved", ctx.user_data["lang"]))
            return ConversationHandler.END

        # otherwise build next keyboard and prompt
        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        kb = build_keyboard(choices_map.items(), callback_prefix, back_callback)
        await query.edit_message_text(
            t(prompt_key, lang),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return next_state

    return handler


def make_back_handler(choices_map, prompt_key, callback_prefix, state):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        kb = build_keyboard(choices_map.items(), callback_prefix)
        await query.edit_message_text(
            t(prompt_key, lang),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return state

    return handler


def make_repeat_handler(choices_map, prompt_key, callback_prefix, back_callback, state):
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        kb = build_keyboard(choices_map.items(), callback_prefix, back_callback)
        await update.effective_message.reply_text(
            t(prompt_key, ctx.user_data.get("lang", DEFAULT_LANGUAGE)),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return state

    return handler


async def start_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = build_keyboard(LANGUAGE_CHOICES_MAP.items(), "lang")
    await update.effective_message.reply_text(
        t("select_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


# Handlers via factories
language_selected = make_selection_handler(
    LANGUAGE_CHOICES_MAP, "lang", "select_fuel", "fuel", STEP_FUEL, back_callback="back_lang"
)
fuel_selected = make_selection_handler(
    FUEL_CHOICES_MAP, "fuel", "select_service", "serv", STEP_SERVICE, back_callback="back_fuel"
)
service_selected = make_selection_handler(
    SERVICE_CHOICES_MAP, "service", None, None, None
)

back_to_lang = make_back_handler(
    LANGUAGE_CHOICES_MAP, "select_language", "lang", STEP_LANG
)
back_to_fuel = make_back_handler(
    FUEL_CHOICES_MAP, "select_fuel", "fuel", STEP_FUEL
)

repeat_lang_prompt = make_repeat_handler(
    LANGUAGE_CHOICES_MAP, "select_language", "lang", None, STEP_LANG
)
repeat_fuel_prompt = make_repeat_handler(
    FUEL_CHOICES_MAP, "select_fuel", "fuel", "back_lang", STEP_FUEL
)
repeat_service_prompt = make_repeat_handler(
    SERVICE_CHOICES_MAP, "select_service", "serv", "back_fuel", STEP_SERVICE
)

start_handler = ConversationHandler(
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
