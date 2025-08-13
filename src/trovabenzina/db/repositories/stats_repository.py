"""Stats repository: read-only helpers built on DB views."""

from typing import Any, Dict, List

from sqlalchemy import select

from ..models import User, VGeocodingMonthCalls, VUsersSearchesStats
from ..session import AsyncSession


async def count_geocoding_month_calls() -> int:
    """Return the number of geocoding calls in the last 30 days.

    Returns:
        int: Value from the `v_geocoding_month_calls` view.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(VGeocodingMonthCalls.count)
        )
        cnt = result.scalar_one_or_none()
        return cnt or 0


async def get_user_stats(tg_id: int) -> List[Dict[str, Any]]:
    """Return per-fuel statistics for a user, from the materialized view.

    Args:
        tg_id: Telegram user ID.

    Returns:
        List[Dict[str, Any]]: One dict per fuel with fields from `VUsersSearchesStats`.
    """
    async with AsyncSession() as session:
        user_id = (await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )).scalar_one()

        stmt = select(*VUsersSearchesStats.__table__.c).where(
            VUsersSearchesStats.user_id == user_id
        )
        result = await session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]
