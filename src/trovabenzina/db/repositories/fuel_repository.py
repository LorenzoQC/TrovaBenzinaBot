"""Fuel repository: read helpers around the Fuel model."""

from typing import Dict

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


async def get_fuel_id_by_code(code: str) -> int:
    """Resolve a fuel internal ID from its public code.

    Args:
        code: Public `Fuel.code`.

    Returns:
        int: The internal `Fuel.id`.

    Raises:
        sqlalchemy.exc.NoResultFound: If the code does not exist.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(Fuel.id).where(Fuel.code == code)
        )
        return result.scalar_one()
