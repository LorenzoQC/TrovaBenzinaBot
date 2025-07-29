import json
import logging
import sys


class RailwayLogFormatter(logging.Formatter):
    """Output log record as JSON so Railway legge il livello corretto."""

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:  # noqa: N802
        log_record = {
            "time": self.formatTime(record, self.default_time_format),
            "level": record.levelname.lower(),
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(level: int = logging.DEBUG) -> None:
    """Configure root logger for Railway (stdout  JSON)."""
    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)  # stdout ≠ error in Railway
    handler.setFormatter(RailwayLogFormatter())
    root.addHandler(handler)


def describe(h):
    """Returns a compact but useful string for any type of handler."""
    from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler

    if isinstance(h, CommandHandler):
        return f"CommandHandler(commands={list(h.commands)})"

    if isinstance(h, CallbackQueryHandler):
        patt = h.pattern.pattern if h.pattern else None
        return f"CallbackQueryHandler(pattern='{patt}')"

    if isinstance(h, ConversationHandler):
        ep = []
        for e in h.entry_points:
            if isinstance(e, CommandHandler):
                ep.append("/" + ",".join(e.commands))
            elif isinstance(e, CallbackQueryHandler):
                ep.append(f"pattern:{e.pattern.pattern}")
            else:
                ep.append(e.__class__.__name__)
        return f"ConversationHandler(entry_points={ep})"

    attrs = {k: v for k, v in vars(h).items() if not k.startswith('_')}
    return f"{h.__class__.__name__}({attrs})"
