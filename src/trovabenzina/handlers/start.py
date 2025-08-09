from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from trovabenzina.config import DEFAULT_LANGUAGE, FUEL_MAP, LANGUAGE_MAP
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_START_FUEL, STEP_START_LANGUAGE
from trovabenzina.utils.telegram import inline_menu_from_map, with_back_row
from ..db import upsert_user, get_user

__all__ = ["start_handler"]


def make_selection_handler(
        choices_getter,
        data_key,
        prompt_key,
        callback_prefix,
        next_state,
        final=False,
        back_callback=None,
):
    """Factory for handlers that set a user_data key and move to the next step or finalize."""
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        value = query.data.split("_", 1)[1]
        ctx.user_data[data_key] = value

        if final:
            uid = update.effective_user.id
            username = update.effective_user.username
            fuel = ctx.user_data.get("fuel")
            lang = ctx.user_data.get("lang") or DEFAULT_LANGUAGE
            await upsert_user(uid, username, fuel, lang)
            await query.edit_message_text(t("profile_saved", lang))
            return ConversationHandler.END

        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        choices_map = choices_getter(lang)
        kb = inline_menu_from_map(choices_map, callback_prefix, per_row=2)
        if back_callback:
            kb = with_back_row(kb, back_callback)
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
    """Factory for handlers that go back one step."""
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        choices_map = choices_getter(lang)
        kb = inline_menu_from_map(choices_map, callback_prefix, per_row=2)
        if back_callback:
            kb = with_back_row(kb, back_callback)
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
    """Factory for handlers that repeat the prompt on invalid text."""
    async def handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        old_id = ctx.user_data.get("prev_prompt_id")
        if old_id:
            try:
                await ctx.bot.delete_message(chat_id=chat_id, message_id=old_id)
            except Exception:
                pass

        lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
        choices_map = choices_getter(lang)
        kb = inline_menu_from_map(choices_map, callback_prefix, per_row=2)
        if back_callback:
            kb = with_back_row(kb, back_callback)
        sent = await update.effective_message.reply_text(
            t(prompt_key, lang),
            reply_markup=InlineKeyboardMarkup(kb),
        )
        ctx.user_data["prev_prompt_id"] = sent.message_id
        return state

    return handler


async def start_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Entry point for /start: ask user to select language or notify if already registered."""
    existing = await get_user(update.effective_user.id)
    if existing:
        _, lang = existing
        lang = lang or DEFAULT_LANGUAGE
        await update.effective_message.reply_text(t("user_already_registered", lang))
        return ConversationHandler.END

    # Language selection
    language_choices = dict(LANGUAGE_MAP.items())
    kb = inline_menu_from_map(language_choices, "lang", per_row=2)
    sent = await update.effective_message.reply_text(
        t("select_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    ctx.user_data["prev_prompt_id"] = sent.message_id
    return STEP_START_LANGUAGE


# Handlers via factories

language_selected = make_selection_handler(
    lambda lang: {t(name, lang): code for name, code in FUEL_MAP.items()},
    "lang",
    "select_fuel",
    "fuel",
    STEP_START_FUEL,
    back_callback="back_lang",
)

fuel_selected = make_selection_handler(
    None,
    "fuel",
    None,
    None,
    None,
    final=True,
    back_callback="back_fuel",
)

back_to_lang = make_back_handler(
    lambda lang: dict(LANGUAGE_MAP.items()),
    "select_language",
    "lang",
    STEP_START_LANGUAGE,
)

repeat_lang_prompt = make_repeat_handler(
    lambda lang: dict(LANGUAGE_MAP.items()),
    "select_language",
    "lang",
    None,
    STEP_START_LANGUAGE,
)

repeat_fuel_prompt = make_repeat_handler(
    lambda lang: {t(name, lang): code for name, code in FUEL_MAP.items()},
    "select_fuel",
    "fuel",
    "back_lang",
    STEP_START_FUEL,
)

start_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_ep)],
    states={
        STEP_START_LANGUAGE: [
            CallbackQueryHandler(language_selected, pattern=r"^lang_"),
            MessageHandler(filters.ALL, repeat_lang_prompt),
        ],
        STEP_START_FUEL: [
            CallbackQueryHandler(fuel_selected, pattern=r"^fuel_"),
            CallbackQueryHandler(back_to_lang, pattern=r"^back_lang$"),
            MessageHandler(filters.ALL, repeat_fuel_prompt),
        ],
    },
    fallbacks=[],
    block=True,
)
