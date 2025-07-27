"""
Utilities tightly coupled to python-telegram-core.
"""
from typing import List, Tuple

from telegram import InlineKeyboardButton


def inline_kb(items: List[Tuple[str, str]], per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    """Return an inline-keyboard layout with up to *per_row* buttons per row."""
    return [
        [InlineKeyboardButton(text, callback_data=data) for text, data in items[i: i + per_row]]
        for i in range(0, len(items), per_row)
    ]
