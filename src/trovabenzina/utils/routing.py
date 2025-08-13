"""Command router to break out of any ConversationHandler (except /start)."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

__all__ = ["reroute_command"]


def _extract_cmd(update: Update) -> str:
    text = (update.effective_message.text or "").strip()
    if not text.startswith("/"):
        return ""
    first = text.split()[0]
    # strip bot username suffix: /cmd@MyBot -> /cmd
    return first.split("@", 1)[0].lower()


async def _delete_saved_message(ctx: ContextTypes.DEFAULT_TYPE, key: str = "profile_msg") -> None:
    """Delete a message reference saved in chat_data[key] = {chat_id, message_id}."""
    ref = ctx.chat_data.pop(key, None)
    if not ref:
        return
    try:
        await ctx.bot.delete_message(chat_id=ref["chat_id"], message_id=ref["message_id"])
    except Exception:
        # Already deleted or not found: ignore.
        pass


async def reroute_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """If inside a conversation, reroute the incoming command to its entrypoint.

    Behavior:
      - /start, /restart: do NOT interrupt current flow -> keep state
      - others: delete saved /profile message (if any), end current convo and jump to entrypoint
    """
    cmd = _extract_cmd(update)

    if cmd in ("/start", "/restart"):
        return ctx.chat_data.get("current_state", ConversationHandler.END)

    # Always try to delete the last /profile message if present
    await _delete_saved_message(ctx, "profile_msg")

    # Normal commands: end current convo and jump to entrypoint
    if cmd in ("/search", "/find"):
        from ..handlers.search import search_ep
        await search_ep(update, ctx)
    elif cmd == "/profile":
        from ..handlers.profile import profile_ep
        await profile_ep(update, ctx)
    elif cmd == "/help":
        from ..handlers.help import help_ep
        await help_ep(update, ctx)
    elif cmd == "/statistics":
        from ..handlers.statistics import statistics_ep
        await statistics_ep(update, ctx)

    return ConversationHandler.END
