from typing import Mapping, Tuple, List

from telegram import InlineKeyboardButton

__all__ = ["inline_kb", "inline_menu_from_map", "with_back_row"]

def inline_kb(items: List[Tuple[str, str]], per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    return [[InlineKeyboardButton(t, callback_data=d) for t, d in items[i:i + per_row]]
            for i in range(0, len(items), per_row)]


def inline_menu_from_map(choices: Mapping[str, str], prefix: str, per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    items = [(label, f"{prefix}_{key}") for key, label in choices.items()]
    return inline_kb(items, per_row=per_row)


def with_back_row(kb: List[List[InlineKeyboardButton]], callback: str, label: str = "↩") -> List[
    List[InlineKeyboardButton]]:
    return kb + [[InlineKeyboardButton(label, callback_data=callback)]]
