"""
Initial onboarding conversation (/start).

Guides the user through language and fuel selection, then persists the profile.
"""

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from ..config import DEFAULT_LANGUAGE, FUEL_MAP, LANGUAGE_MAP
from ..db import upsert_user, get_user
from ..i18n import t
from ..utils import (
    STEP_START_FUEL,
    STEP_START_LANGUAGE,
    inline_menu_from_map,
    with_back_row,
    delete_last_profile_message,
)

__all__ = ["start_ep", "start_handler"]


def make_selection_handler(
        choices_getter,
        data_key: str,
        prompt_key: str | None,
        callback_prefix: str | None,
        next_state: int | None,
        final: bool = False,
        back_callback: str | None = None,
):
    """
    Factory for selection handlers that set `user_data[data_key]`.

    If `final=True`, it persists the profile and ends the conversation.

    Args:
        choices_getter: Callable(lang) -> dict[code, label] for the next step.
        data_key: Key in `user_data` to store the selected value.
        prompt_key: Translation key for the next prompt.
        callback_prefix: Callback data prefix for the next step's options.
        next_state: Next conversation state.
        final: If True, finalize and persist the profile.
        back_callback: Optional back-button callback data for the next step.

    Returns:
        Callable: An async handler function.
    """

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
        prompt_key: str,
        callback_prefix: str,
        state: int,
        back_callback: str | None = None,
):
    """
    Factory for back-navigation handlers.

    Args:
        choices_getter: Callable(lang) -> dict[code, label] for the target step.
        prompt_key: Translation key for the prompt to show.
        callback_prefix: Callback data prefix for the target options.
        state: Conversation state to return to.
        back_callback: Optional callback data for an extra back row.

    Returns:
        Callable: An async handler function.
    """

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
        prompt_key: str,
        callback_prefix: str,
        back_callback: str | None,
        state: int,
):
    """
    Factory for handlers that repeat a prompt on invalid input.

    Args:
        choices_getter: Callable(lang) -> dict[code, label] for the step.
        prompt_key: Translation key for the prompt.
        callback_prefix: Callback data prefix for the options.
        back_callback: Optional back-button callback data.
        state: Conversation state to return to.

    Returns:
        Callable: An async handler function.
    """

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


async def start_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for /start: asks language unless user already registered.

    Args:
        update: Telegram update.
        ctx: Callback context.

    Returns:
        int: The conversation state to wait for a language selection,
             or END if the user already has a profile.
    """
    await delete_last_profile_message(ctx)

    existing = await get_user(update.effective_user.id)
    if existing:
        _, lang = existing
        lang = lang or DEFAULT_LANGUAGE
        await update.effective_message.reply_text(t("user_already_registered", lang))
        return ConversationHandler.END

    # Language selection
    language_choices = {code: name for name, code in LANGUAGE_MAP.items()}
    kb = inline_menu_from_map(language_choices, "lang", per_row=2)
    sent = await update.effective_message.reply_text(
        t("select_language", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    ctx.user_data["prev_prompt_id"] = sent.message_id
    return STEP_START_LANGUAGE


# Handlers via factories

language_selected = make_selection_handler(
    lambda lang: {code: t(name, lang) for name, code in FUEL_MAP.items()},
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
    lambda lang: {code: name for name, code in LANGUAGE_MAP.items()},
    "select_language",
    "lang",
    STEP_START_LANGUAGE,
)

# Repeat prompts on invalid input
repeat_lang_prompt = make_repeat_handler(
    lambda lang: {code: name for name, code in LANGUAGE_MAP.items()},
    "select_language",
    "lang",
    None,
    STEP_START_LANGUAGE,
)

repeat_fuel_prompt = make_repeat_handler(
    lambda lang: {code: t(name, lang) for name, code in FUEL_MAP.items()},
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
