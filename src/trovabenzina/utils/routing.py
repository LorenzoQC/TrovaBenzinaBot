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


async def reroute_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """If inside a conversation, reroute the incoming command to its entrypoint.

    Behavior:
      - /start: do NOT interrupt the current flow -> keep state (consume update)
      - others: end current convo and invoke the matched entrypoint immediately
    """
    cmd = _extract_cmd(update)

    # Block /start inside other convos
    if cmd in ("/start", "/restart"):
        # Stay in current state if we can, else just consume the update
        return ctx.chat_data.get("current_state", ConversationHandler.END)

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
