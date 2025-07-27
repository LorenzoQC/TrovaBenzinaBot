import logging

import aiohttp

from trovabenzina.config import (
    GEOCODE_HARD_CAP,
    GOOGLE_API_KEY,
    GEOCODE_URL,
    MISE_SEARCH_URL,
    MISE_DETAIL_URL,
)
from trovabenzina.db.crud import (
    get_cached_geocode,
    upsert_geocode,
    get_recent_geocache_count,
)

log = logging.getLogger(__name__)

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

async def fetch_address(station_id: int):
    """Get full address from public station registry."""
    url = MISE_DETAIL_URL.format(id=station_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    return data.get("address") if isinstance(data, dict) else None
    except Exception as exc:
        log.warning("Error fetching address for station %s: %s", station_id, exc)
    return None

async def call_api(lat: float, lng: float, radius: float, fuel_type: str):
    """Query fuel price API by location."""
    payload = {
        "points": [{"lat": lat, "lng": lng}],
        "radius": radius,
        "fuelType": fuel_type,
        "priceOrder": "asc",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(MISE_SEARCH_URL, json=payload, timeout=10) as resp:
            return await resp.json() if resp.status == 200 else None
