"""
Miscellaneous handlers for unrecognized messages and commands.

Handles:
- Any non-command message outside conversations
- Any unknown command
"""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..db import get_user_language_code_by_tg_id
from ..i18n import t

__all__ = ["handle_unrecognized_message", "handle_unknown_command"]


async def handle_unrecognized_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Reply to any non-command message with a fixed hint to use /help.

    Args:
        update: Telegram update.
        context: Callback context.

    Returns:
        None
    """
    uid = update.effective_user.id if update.effective_user else None
    lang = await get_user_language_code_by_tg_id(uid) if uid else None
    await update.effective_message.reply_html(t("unknown_message_hint", lang=lang))


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Reply to any unknown command with a fixed hint to use /help.

    Args:
        update: Telegram update.
        context: Callback context.

    Returns:
        None
    """
    uid = update.effective_user.id if update.effective_user else None
    lang = await get_user_language_code_by_tg_id(uid) if uid else None
    await update.effective_message.reply_html(t("unknown_command_hint", lang=lang))
