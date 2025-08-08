"""Fuel repository: read helpers around the Fuel model."""

from __future__ import annotations

from typing import Dict, Iterable

from sqlalchemy import select

from ..models import Fuel
from ..session import AsyncSession


async def get_fuel_map() -> Dict[str, str]:
    """Return a mapping of fuel names to fuel codes.

    Returns:
        Dict[str, str]: Mapping like {"Benzina": "1", "Gasolio": "2", ...}.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(Fuel).where(Fuel.del_ts.is_(None))
        )
        fuels = result.scalars().all()
    return {f.name: f.code for f in fuels}


async def get_fuels_by_ids_map(ids: Iterable[int]) -> Dict[int, Fuel]:
    """Return a dict {fuel_id: Fuel} for the given IDs.

    Args:
        ids: Iterable of `Fuel.id`.

    Returns:
        Dict[int, Fuel]: Mapping id -> Fuel instance.
    """
    ids = list({*ids})
    if not ids:
        return {}
    async with AsyncSession() as session:
        rows = await session.execute(select(Fuel).where(Fuel.id.in_(ids)))
        fuels = rows.scalars().all()
    return {f.id: f for f in fuels}
