"""Geocache repository: caching results of geocoding lookups."""
from typing import Optional

from sqlalchemy import delete, func, select, text

from ..models import GeoCache
from ..session import AsyncSession


async def get_geocache(address: str) -> Optional[GeoCache]:
    """Fetch a geocache entry by address, excluding soft-deleted rows.

    Args:
        address: Address string as stored in the cache.

    Returns:
        Optional[GeoCache]: The matching row or `None`.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(GeoCache).where(
                GeoCache.address == address,
                GeoCache.del_ts.is_(None),
            )
        )
        return result.scalar_one_or_none()


async def save_geocache(address: str, lat: float, lng: float) -> None:
    """Insert or update a cache entry for an address.

    Args:
        address: Address string key.
        lat: Latitude.
        lng: Longitude.
    """
    async with AsyncSession() as session:
        existing = (await session.execute(
            select(GeoCache).where(GeoCache.address == address)
        )).scalar_one_or_none()

        if existing:
            existing.lat = lat
            existing.lng = lng
        else:
            session.add(GeoCache(address=address, lat=lat, lng=lng))

        await session.commit()


async def delete_old_geocache(days: int = 90) -> None:
    """Hard-delete cache rows older than the given number of days.

    Args:
        days: Age threshold in days (default 90).
    """
    async with AsyncSession() as session:
        await session.execute(
            delete(GeoCache).where(
                GeoCache.ins_ts < func.now() - text(f"INTERVAL '{days} days'")
            )
        )
        await session.commit()
