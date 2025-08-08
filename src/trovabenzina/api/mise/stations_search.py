import logging
from typing import Any, Dict, Optional

import aiohttp

from trovabenzina.config import MISE_SEARCH_URL

__all__ = ["search_stations"]

log = logging.getLogger(__name__)


async def search_stations(
        lat: float,
        lng: float,
        radius: float,
        fuel_type: str,
) -> Optional[Dict[str, Any]]:
    """Search fuel stations around a point using the public MISE endpoint.

    The endpoint supports polygons; we pass a single point and a radius.
    Results are requested in ascending price order.

    Args:
        lat: Latitude of the search center.
        lng: Longitude of the search center.
        radius: Search radius in meters.
        fuel_type: MISE fuel type identifier (e.g., 'Benzina', 'Gasolio').

    Returns:
        Optional[Dict[str, Any]]: Decoded JSON payload if successful; else None.
    """
    payload = {
        "points": [{"lat": lat, "lng": lng}],
        "radius": radius,
        "fuelType": fuel_type,
        "priceOrder": "asc",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(MISE_SEARCH_URL, json=payload) as resp:
                if resp.status != 200:
                    log.warning("MISE search failed (status=%s) payload=%s", resp.status, payload)
                    return None
                # MISE may reply with text/plain; ignore content-type to parse JSON safely.
                return await resp.json(content_type=None)
    except Exception as exc:
        log.warning("MISE search error: %s", exc)
        return None
