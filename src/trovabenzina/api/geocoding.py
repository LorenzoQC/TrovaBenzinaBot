import aiohttp

from trovabenzina.config import GEOCODE_HARD_CAP, GOOGLE_API_KEY, GEOCODE_URL
from trovabenzina.db.crud import get_cached_geocode, get_recent_geocache_count, upsert_geocode

__all__ = [
    "geocode",
]


async def geocode(addr: str):
    """Return (lat, lng) or None if not found or over quota."""
    # Try cached coordinates
    cached = await get_cached_geocode(addr)
    if cached:
        return cached

    # Rate limiting via view
    count = await get_recent_geocache_count()
    if count >= GEOCODE_HARD_CAP:
        return None

    # Call Google Geocoding API
    params = {
        "address": addr,
        "components": "country:IT",
        "language": "it",
        "key": GOOGLE_API_KEY,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(GEOCODE_URL, params=params, timeout=10) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    results = data.get("results", [])
    if not results:
        return None
    best = next((x for x in results if not x.get("partial_match")), results[0])
    comps = {c["types"][0]: c for c in best.get("address_components", [])}
    if "locality" not in comps:
        return None
    if best["geometry"]["location_type"] not in {"ROOFTOP", "RANGE_INTERPOLATED", "GEOMETRIC_CENTER"}:
        return None

    latlng = best["geometry"]["location"]

    # Update cache
    await upsert_geocode(addr, latlng["lat"], latlng["lng"])

    return latlng["lat"], latlng["lng"]
