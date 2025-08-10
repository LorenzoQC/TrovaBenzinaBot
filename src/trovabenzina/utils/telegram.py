"""Small helpers for building Telegram inline keyboards."""

from __future__ import annotations

from typing import List, Mapping, Tuple

from telegram import InlineKeyboardButton

__all__ = ["inline_kb", "inline_menu_from_map", "with_back_row"]


def inline_kb(items: List[Tuple[str, str]], per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    """Build a grid of inline buttons.

    Args:
        items: A list of ``(text, callback_data)`` tuples in display order.
        per_row: Maximum number of buttons per row. Must be >= 1.

    Returns:
        A list of rows suitable for ``InlineKeyboardMarkup``.
    """
    if per_row < 1:
        raise ValueError("per_row must be >= 1")
    return [
        [InlineKeyboardButton(text, callback_data=data) for text, data in items[i: i + per_row]]
        for i in range(0, len(items), per_row)
    ]


def inline_menu_from_map(choices: Mapping[str, str], prefix: str, per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    """Build a menu from a code->label mapping.

    Each button's ``callback_data`` is prefixed as ``f\"{prefix}_{code}\"``.

    Args:
        choices: Mapping of option code -> human label.
        prefix: Callback prefix to namespace the selection.
        per_row: Maximum number of buttons per row.

    Returns:
        Inline keyboard markup structure.
    """
    items = [(label, f"{prefix}_{code}") for code, label in choices.items()]
    return inline_kb(items, per_row=per_row)


def with_back_row(kb: List[List[InlineKeyboardButton]], callback: str, label: str = "↩") -> List[
    List[InlineKeyboardButton]]:
    """Append a single full-width 'Back' row to an inline keyboard.

    Args:
        kb: Existing keyboard (list of rows).
        callback: Callback data for the back button.
        label: Button label (defaults to a back arrow).

    Returns:
        The original keyboard plus a final row with a single back button.
    """
    return kb + [[InlineKeyboardButton(label, callback_data=callback)]]
