"""Logging helpers for Railway deployments.

Provides a JSON log formatter compatible with Railway's log parser and a
convenience function to configure the root logger.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict

from ..config import LOG_LEVEL

__all__ = ["RailwayLogFormatter", "setup_logging", "describe"]


class RailwayLogFormatter(logging.Formatter):
    """Format log records as compact JSON.

    Produces fields that Railway understands so that log levels are parsed
    correctly.

    Attributes:
        default_time_format: Strftime pattern for the timestamp.
        default_msec_format: Millisecond suffix format.
    """

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:  # noqa: N802
        """Return a JSON string for the given record.

        Args:
            record: The log record to format.

        Returns:
            A JSON-encoded string representing the record.
        """
        log_record: Dict[str, Any] = {
            "time": self.formatTime(record, self.default_time_format),
            "level": record.levelname.lower(),
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(default_level: int = logging.INFO) -> None:
    """Configure the root logger for JSON output on stdout.

    Any pre-existing handlers on the root logger are removed.

    Args:
        default_level: Minimum log level to set on the root logger.
    """
    level = getattr(logging, LOG_LEVEL, default_level)
    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    # Railway reads stdout and infers log levels from the JSON field.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(RailwayLogFormatter())
    root.addHandler(handler)


def describe(handler: Any) -> str:
    """
    Return a compact, useful description of a PTB handler.

    Helpful when logging the configured conversation graph.
    """
    from telegram.ext import (
        CallbackQueryHandler,
        CommandHandler,
        ConversationHandler,
        MessageHandler,
    )

    # CommandHandler
    if isinstance(handler, CommandHandler):
        return f"CommandHandler(commands={list(handler.commands)})"

    # CallbackQueryHandler
    if isinstance(handler, CallbackQueryHandler):
        patt = handler.pattern.pattern if getattr(handler, "pattern", None) else None
        return f"CallbackQueryHandler(pattern='{patt}')"

    # ConversationHandler
    if isinstance(handler, ConversationHandler):
        entry_points = []
        for ep in handler.entry_points:
            if isinstance(ep, CommandHandler):
                entry_points.append("/" + ",".join(ep.commands))
            elif isinstance(ep, CallbackQueryHandler):
                ep_pat = ep.pattern.pattern if getattr(ep, "pattern", None) else None
                entry_points.append(f"pattern:{ep_pat}")
            else:
                entry_points.append(ep.__class__.__name__)
        return f"ConversationHandler(entry_points={entry_points})"

    # MessageHandler (no __dict__ → avoid vars())
    if isinstance(handler, MessageHandler):
        # filters has a readable __str__ in PTB 22.x
        try:
            filt_str = str(handler.filters)
        except Exception:
            filt_str = handler.filters.__class__.__name__
        return f"MessageHandler(filters={filt_str})"

    # Generic, but safe if __dict__ is absent (e.g., __slots__)
    try:
        attrs = {k: v for k, v in vars(handler).items() if not k.startswith("_")}
        return f"{handler.__class__.__name__}({attrs})"
    except TypeError:
        # Last-resort: class name only
        return f"{handler.__class__.__name__}()"
