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
    """Return a compact, useful description of a PTB handler.

    This is helpful when logging the configured conversation graph.

    Args:
        handler: Any python-telegram-bot handler instance.

    Returns:
        A human-friendly string describing the handler.
    """
    from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

    if isinstance(handler, CommandHandler):
        return f"CommandHandler(commands={list(handler.commands)})"

    if isinstance(handler, CallbackQueryHandler):
        patt = handler.pattern.pattern if handler.pattern else None
        return f"CallbackQueryHandler(pattern='{patt}')"

    if isinstance(handler, ConversationHandler):
        entry_points = []
        for e in handler.entry_points:
            if isinstance(e, CommandHandler):
                entry_points.append("/" + ",".join(e.commands))
            elif isinstance(e, CallbackQueryHandler):
                entry_points.append(f"pattern:{e.pattern.pattern}")
            else:
                entry_points.append(e.__class__.__name__)
        return f"ConversationHandler(entry_points={entry_points})"

    attrs = {k: v for k, v in vars(handler).items() if not k.startswith("_")}
    return f"{handler.__class__.__name__}({attrs})"
