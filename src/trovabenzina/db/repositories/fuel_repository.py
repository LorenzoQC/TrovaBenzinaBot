"""Fuel repository: read helpers around the Fuel model."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

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


async def get_fuel_by_code(code: str) -> Optional[Fuel]:
    """Return Fuel by its `code`, or None if not found or soft-deleted."""
    code = (code or "").strip()
    if not code:
        return None
    async with AsyncSession() as session:
        row = await session.execute(
            select(Fuel).where(Fuel.code == code, Fuel.del_ts.is_(None))
        )
        return row.scalars().first()


async def get_fuel_name_by_code(code: str) -> Optional[str]:
    """Return the fuel name for a given `fuel_code`, or None if not found/soft-deleted."""
    code = (code or "").strip()
    if not code:
        return None
    async with AsyncSession() as session:
        row = await session.execute(
            select(Fuel.name).where(Fuel.code == code, Fuel.del_ts.is_(None))
        )
        return row.scalar_one_or_none()


async def get_fuels_by_codes_map(codes: Iterable[str]) -> Dict[str, Fuel]:
    """Return a dict {fuel_code: Fuel} for the given codes.

    Args:
        codes: Iterable of `Fuel.code`.

    Returns:
        Dict[str, Fuel]: Mapping code -> Fuel instance (only non-deleted).
    """
    norm = [c.strip() for c in codes if c is not None]
    uniq = list({*norm})
    if not uniq:
        return {}
    async with AsyncSession() as session:
        rows = await session.execute(
            select(Fuel).where(Fuel.code.in_(uniq), Fuel.del_ts.is_(None))
        )
        fuels = rows.scalars().all()
    return {f.code: f for f in fuels}


async def get_uom_by_code(code: str) -> Optional[str]:
    """Return the UOM (e.g., 'liter' or 'kilo') for a given `fuel_code`."""
    code = (code or "").strip()
    if not code:
        return None
    async with AsyncSession() as session:
        row = await session.execute(
            select(Fuel.uom).where(Fuel.code == code, Fuel.del_ts.is_(None))
        )
        return row.scalar_one_or_none()


async def get_uom_map_by_codes(codes: Iterable[str]) -> Dict[str, str]:
    """Return a dict {fuel_code: uom} for the given codes.

    Args:
        codes: Iterable of `Fuel.code`.

    Returns:
        Dict[str, str]: Mapping code -> uom (only non-deleted fuels returned).
    """
    norm = [c.strip() for c in codes if c is not None]
    uniq = list({*norm})
    if not uniq:
        return {}
    async with AsyncSession() as session:
        rows = await session.execute(
            select(Fuel.code, Fuel.uom).where(Fuel.code.in_(uniq), Fuel.del_ts.is_(None))
        )
        return dict(rows.all())
