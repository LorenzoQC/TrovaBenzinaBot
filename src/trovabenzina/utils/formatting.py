from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

__all__ = [
    "symbol_eur",
    "symbol_slash",
    "symbol_liter",
    "symbol_kilo",
    "format_price_unit",
    "format_price",
    "pct_delta_from_avg",
    "format_avg_comparison_text",
    "format_date",
]

TFunc = Optional[Callable[[str, Optional[str]], str]]


def _tx(t: TFunc, lang: Optional[str], key: str, default: str) -> str:
    """Safe translate: fall back to default on any error/missing key."""
    if t is None:
        return default
    try:
        v = t(key, lang)
        return v if isinstance(v, str) and v else default
    except Exception:
        return default


def symbol_eur(t: TFunc = None, lang: Optional[str] = None) -> str:
    """Return the localized EUR symbol."""
    return _tx(t, lang, "eur_symbol", "€")


def symbol_slash(t: TFunc = None, lang: Optional[str] = None) -> str:
    """Return the localized slash separator."""
    return _tx(t, lang, "slash_symbol", "/")


def symbol_liter(t: TFunc = None, lang: Optional[str] = None) -> str:
    """Return the localized liter symbol."""
    return _tx(t, lang, "liter_symbol", "L")


def symbol_kilo(t: TFunc = None, lang: Optional[str] = None) -> str:
    """Return the localized kilogram symbol."""
    return _tx(t, lang, "kilo_symbol", "kg")


def format_price_unit(
        uom: Optional[str] = None,
        t: TFunc = None,
        lang: Optional[str] = None,
) -> str:
    """Return a unit string like '€/L' or '€/kg'.

    Args:
        uom: Unit hint from data source (e.g., 'L', 'kg').
        t: Translation function t(key, lang).
        lang: Language code.

    Returns:
        Localized unit string '€/<unit>'.
    """
    if uom.strip().lower() in {"kg", "kilogram", "kilo"}:
        unit_suffix = symbol_kilo(t, lang)
    else:
        unit_suffix = symbol_liter(t, lang)

    return f"{symbol_eur(t, lang)}{symbol_slash(t, lang)}{unit_suffix}"


def format_price(value: Optional[float], unit: str) -> str:
    """Format a price with 3 decimals and trailing unit.

    Args:
        value: Price value or None.
        unit: Unit string like '€/L'.

    Returns:
        Formatted price string.
    """
    if value is None:
        return f"— {unit}"
    return f"{value:.3f} {unit}"


def pct_delta_from_avg(price: Optional[float], average: Optional[float]) -> int:
    """Return % delta of price vs average (rounded int).
    Negative means 'below average', positive 'above average'.

    Args:
        price: Price value.
        average: Average price.

    Returns:
        Integer percentage delta; 0 if invalid inputs.
    """
    if price is None or average is None or average <= 0:
        return 0
    return int(round((price - average) / average * 100))


def format_avg_comparison_text(
        price: Optional[float],
        average: Optional[float],
        t: TFunc = None,
        lang: Optional[str] = None,
) -> str:
    """Human-friendly text for price vs average using translations.

    Uses keys:
      - 'equal_average'
      - 'below_average'
      - 'above_average'

    Args:
        price: Price value.
        average: Average price.
        t: Translation function.
        lang: Language code.

    Returns:
        Localized comparison string.
    """
    delta = pct_delta_from_avg(price, average)
    if delta == 0:
        return _tx(t, lang, "equal_average", "equal to average")
    label = "below_average" if delta < 0 else "above_average"
    return f"{abs(delta)}% {_tx(t, lang, label, label.replace('_', ' '))}"


def _parse_iso_dt(iso_str: str) -> datetime:
    """Parse ISO timestamp with 'Z' support."""
    # Support '...Z'
    iso = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(iso)


def format_date(
        iso: Optional[str],
        src_tz: str = "UTC",
        dst_tz: str = "Europe/Rome",
        fmt: str = "%d/%m/%Y %H:%M",
        t: TFunc = None,
        lang: Optional[str] = None,
) -> str:
    """Format an ISO timestamp to local time string.

    If the input is naive (no tzinfo), it's assumed to be in `src_tz`.
    Then it's converted to `dst_tz` and formatted with `fmt`.

    Args:
        iso: ISO datetime string (e.g., '2025-08-08T12:34:56+00:00').
        src_tz: Source timezone name if input is naive.
        dst_tz: Destination timezone name.
        fmt: Output strftime format.
        t: Translation function.
        lang: Language code.

    Returns:
        Localized formatted datetime or a fallback (e.g., 'n/a').
    """
    if not iso:
        return _tx(t, lang, "unknown_update", "n/a")
    try:
        dt = _parse_iso_dt(iso)
        if dt.tzinfo is None and ZoneInfo:
            dt = dt.replace(tzinfo=ZoneInfo(src_tz))
        if ZoneInfo and dst_tz:
            dt = dt.astimezone(ZoneInfo(dst_tz))
        return dt.strftime(fmt)
    except Exception:
        return _tx(t, lang, "unknown_update", "n/a")


def format_directions_url(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
