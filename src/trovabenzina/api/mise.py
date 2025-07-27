import logging

import aiohttp

from trovabenzina.config import MISE_DETAIL_URL, MISE_SEARCH_URL

__all__ = [
    "fetch_address",
    "call_api",
]

log = logging.getLogger(__name__)


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
