"""Search repository: writes and analytics helpers for searches."""

from datetime import date
from typing import Optional

from sqlalchemy import select

from ..models import Search, User, Fuel
from ..session import AsyncSession


async def save_search(
        tg_id: int,
        fuel_code: str,
        radius: int,
        num_stations: int,
        price_avg: Optional[float] = None,
        price_min: Optional[float] = None,
) -> None:
    """Persist a search record linked to the given Telegram user.

    Args:
        tg_id: Telegram user ID.
        fuel_code: Fuel code for the search.
        radius: Search radius (km).
        num_stations: Number of stations considered.
        price_avg: Average price among stations (optional).
        price_min: Minimum price among stations (optional).

    Raises:
        sqlalchemy.exc.NoResultFound: If the user or fuel cannot be resolved.
    """
    async with AsyncSession() as session:
        user_id = (await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )).scalar_one()

        fuel_id = (await session.execute(
            select(Fuel.id).where(Fuel.code == fuel_code)
        )).scalar_one()

        new_search = Search(
            user_id=user_id,
            fuel_id=fuel_id,
            radius=radius,
            num_stations=num_stations,
            price_avg=price_avg,
            price_min=price_min,
        )
        session.add(new_search)
        await session.commit()


async def calculate_monthly_savings(
        user_id: int,
        start_date: date,
        end_date: date,
) -> float:
    """Estimate total savings for a user in a period.

    The current heuristic multiplies per-search savings `(avg - min)` by 50
    (approx. liters/year budget per user). Adjust as needed.

    Args:
        user_id: Internal `User.id`.
        start_date: Period start (inclusive).
        end_date: Period end (inclusive).

    Returns:
        float: Estimated savings in the period.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(Search.price_avg, Search.price_min)
            .where(Search.user_id == user_id)
            .where(Search.ins_ts.between(start_date, end_date))
        )
        rows = result.all()
    return sum((r.price_avg - r.price_min) * 50 for r in rows)
