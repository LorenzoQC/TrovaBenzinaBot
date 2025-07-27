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

__all__ = ["start_handler"]


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
        choices_getter,
        data_key,
        prompt_key,
        callback_prefix,
        next_state,
        back_callback=None,
):
    """
    Factory for handlers that set a user_data key and move to the next step.
    choices_getter: callable returning dict code->label
    """
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        # extract selected value
        value = query.data.split("_", 1)[1]
        ctx.user_data[data_key] = value

        # if final (service), persist and end
        if data_key == "service":
            await upsert_user(
                update.effective_user.id,
                update.effective_user.username,
                ctx.user_data["fuel"],
                ctx.user_data["service"],
                ctx.user_data["lang"],
            )
            await query.edit_message_text(t("profile_saved", ctx.user_data["lang"]))
            return ConversationHandler.END

        # otherwise prompt next
        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        # reconstruct the current choices
        choices_map = choices_getter()
        kb = build_keyboard(choices_map.items(), callback_prefix, back_callback)
        await query.edit_message_text(
            t(prompt_key, lang),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return next_state

    return handler


def make_back_handler(
        choices_getter,
        prompt_key,
        callback_prefix,
        state,
        back_callback=None,
):
    """
    Factory for handlers that go back one step.
    choices_getter: callable returning dict code->label
    """
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        choices_map = choices_getter()
        kb = build_keyboard(choices_map.items(), callback_prefix, back_callback)
        await query.edit_message_text(
            t(prompt_key, lang),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return state

    return handler


def make_repeat_handler(
        choices_getter,
        prompt_key,
        callback_prefix,
        back_callback,
        state,
):
    """
    Factory for handlers that repeat the prompt on invalid text.
    choices_getter: callable returning dict code->label
    """
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        choices_map = choices_getter()
        kb = build_keyboard(choices_map.items(), callback_prefix, back_callback)
        await update.effective_message.reply_text(
            t(prompt_key, lang),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return state

    return handler


async def start_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for /start: ask user to select language.
    """
    # build fresh choices from DB: invert name->code to code->name
    language_choices = {code: name for name, code in LANGUAGE_MAP.items()}
    kb = build_keyboard(language_choices.items(), "lang")
    await update.effective_message.reply_text(
        t("select_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


# Handlers via factories, passing in getters directly
language_selected = make_selection_handler(
    lambda: {code: name for name, code in FUEL_MAP.items()},
    "lang", "select_fuel", "fuel", STEP_FUEL,
    back_callback="back_lang"
)
fuel_selected = make_selection_handler(
    lambda: {code: name for name, code in SERVICE_MAP.items()},
    "fuel", "select_service", "serv", STEP_SERVICE,
    back_callback="back_fuel"
)
service_selected = make_selection_handler(
    None, "service", None, None, None
)

back_to_lang = make_back_handler(
    lambda: {code: name for name, code in LANGUAGE_MAP.items()},
    "select_language", "lang", STEP_LANG
)
back_to_fuel = make_back_handler(
    lambda: {code: name for name, code in FUEL_MAP.items()},
    "select_fuel", "fuel", STEP_FUEL,
    back_callback="back_lang"
)

repeat_lang_prompt = make_repeat_handler(
    lambda: {code: name for name, code in LANGUAGE_MAP.items()},
    "select_language", "lang", None, STEP_LANG
)
repeat_fuel_prompt = make_repeat_handler(
    lambda: {code: name for name, code in FUEL_MAP.items()},
    "select_fuel", "fuel", "back_lang", STEP_FUEL
)
repeat_service_prompt = make_repeat_handler(
    lambda: {code: name for name, code in SERVICE_MAP.items()},
    "select_service", "serv", "back_fuel", STEP_SERVICE
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
