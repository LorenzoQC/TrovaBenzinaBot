import logging
from typing import Optional, Tuple

import aiohttp

from trovabenzina.config import GEOCODE_HARD_CAP, GOOGLE_API_KEY, GEOCODE_URL
from trovabenzina.db import (
    get_geocache,
    count_geocoding_month_calls,
    save_geocache,
)

__all__ = ["geocode_address"]

log = logging.getLogger(__name__)


async def geocode_address(addr: str) -> Optional[Tuple[float, float]]:
    """Resolve an address to coordinates using Google Geocoding API.

    Applies a read-through cache and enforces a monthly hard cap. Returns a
    `(lat, lng)` tuple or `None` if resolution fails or quota is exceeded.

    Args:
        addr: The address to geocode (assumed Italian context).

    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) if found; else None.
    """
    # Try cached coordinates first
    record = await get_geocache(addr)
    if record:
        return record.lat, record.lng

    # Enforce monthly hard cap
    count = await count_geocoding_month_calls()
    if count >= GEOCODE_HARD_CAP:
        log.info("Geocoding hard cap reached: %s >= %s", count, GEOCODE_HARD_CAP)
        return None

    params = {
        "address": addr,
        "components": "country:IT",
        "language": "it",
        "key": GOOGLE_API_KEY,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GEOCODE_URL, params=params) as resp:
                if resp.status != 200:
                    log.warning("Geocoding failed (status=%s) for %r", resp.status, addr)
                    return None
                data = await resp.json()
    except Exception as exc:
        log.warning("Geocoding error for %r: %s", addr, exc)
        return None

    results = data.get("results", [])
    if not results:
        return None

    # Prefer non-partial matches; otherwise take the first result
    best = next((x for x in results if not x.get("partial_match")), results[0])

    # Basic sanity checks on locality and geometry precision
    comps = {c["types"][0]: c for c in best.get("address_components", []) if c.get("types")}
    if not any(k in comps for k in ("locality", "administrative_area_level_3")):
        return None

    location_type = best.get("geometry", {}).get("location_type")
    if location_type not in {"ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER"}:
        return None

    loc = best.get("geometry", {}).get("location")
    if not loc or "lat" not in loc or "lng" not in loc:
        return None

    lat, lng = float(loc["lat"]), float(loc["lng"])

    # Update cache on success (non-blocking on failure)
    try:
        await save_geocache(addr, lat, lng)
    except Exception as exc:
        log.debug("Failed to update geocache for %r: %s", addr, exc)

    return lat, lng
