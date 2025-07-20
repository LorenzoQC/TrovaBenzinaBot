import datetime as dt
import logging

import aiohttp

from trovabenzina.config import (
    GEOCODE_HARD_CAP,
    GOOGLE_API_KEY,
    GEOCODE_URL,
    MISE_SEARCH_URL,
    MISE_DETAIL_URL,
)
from trovabenzina.core.db import fetchrow, execute

log = logging.getLogger(__name__)


async def geocode(addr: str):
    """Return (lat, lng) or None if not found or over quota."""
    # check cache
    row = await fetchrow(
        "SELECT lat, lng FROM geocache WHERE query = $1", addr
    )
    if row:
        return row['lat'], row['lng']

    # rate limiting
    month = dt.date.today().strftime("%Y-%m")
    cnt_row = await fetchrow(
        "SELECT cnt FROM geostats WHERE month = $1", month
    )
    if cnt_row and cnt_row['cnt'] >= GEOCODE_HARD_CAP:
        return None

    # call Google Geocoding API
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
    # update cache and stats
    await execute(
        """
        INSERT INTO geocache(query, lat, lng)
        VALUES($1, $2, $3)
        ON CONFLICT(query) DO UPDATE
          SET lat = EXCLUDED.lat,
              lng = EXCLUDED.lng,
              ts  = CURRENT_TIMESTAMP
        """,
        addr, latlng["lat"], latlng["lng"]
    )
    await execute(
        """
        INSERT INTO geostats(month, cnt)
        VALUES($1, 1)
        ON CONFLICT(month) DO UPDATE
          SET cnt = geostats.cnt + 1
        """,
        month
    )

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
