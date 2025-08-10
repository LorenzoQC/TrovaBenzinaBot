"""Public exports for the :mod:`utils` package.

This file re-exports convenience functions and constants so they can be
imported as ``from trovabenzina.utils import ...``.
"""

from .formatting import (
    format_avg_comparison_text,
    format_date,
    format_directions_url,
    format_price,
    format_price_unit,
    pct_delta_from_avg,
    symbol_eur,
    symbol_kilo,
    symbol_liter,
    symbol_slash,
)
from .logging import RailwayLogFormatter, describe, setup_logging
from .states import (
    STEP_PROFILE_FUEL,
    STEP_PROFILE_LANGUAGE,
    STEP_PROFILE_MENU,
    STEP_SEARCH_LOCATION,
    STEP_START_FUEL,
    STEP_START_LANGUAGE,
)
from .telegram import inline_kb, inline_menu_from_map, with_back_row

__all__ = [
    # formatting
    "symbol_eur",
    "symbol_slash",
    "symbol_liter",
    "symbol_kilo",
    "format_price_unit",
    "format_price",
    "pct_delta_from_avg",
    "format_avg_comparison_text",
    "format_date",
    "format_directions_url",
    # logging
    "RailwayLogFormatter",
    "setup_logging",
    "describe",
    # states
    "STEP_START_LANGUAGE",
    "STEP_START_FUEL",
    "STEP_SEARCH_LOCATION",
    "STEP_PROFILE_MENU",
    "STEP_PROFILE_LANGUAGE",
    "STEP_PROFILE_FUEL",
    # telegram
    "inline_kb",
    "inline_menu_from_map",
    "with_back_row",
]
