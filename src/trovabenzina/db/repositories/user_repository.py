"""User repository: CRUD and lookups for users."""

from typing import Optional, Tuple, List

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from ..models import User, Fuel, Language, Search
from ..session import AsyncSession


async def upsert_user(
        tg_id: int,
        tg_username: str,
        fuel_code: str,
        language_code: Optional[str] = None,
) -> None:
    """Insert or update a user by Telegram ID.

    If the user exists, updates preferred fuel (and language if provided).
    Uses a DB-side upsert on the unique index over `User.tg_id`.

    Args:
        tg_id: Telegram user ID.
        tg_username: Telegram username (without '@').
        fuel_code: Preferred fuel code (resolves to `Fuel.id`).
        language_code: Optional language code (resolves to `Language.id`).

    Raises:
        sqlalchemy.exc.NoResultFound: If `fuel_code` or `language_code` are invalid.
    """
    async with AsyncSession() as session:
        fuel_id = (await session.execute(
            select(Fuel.id).where(Fuel.code == fuel_code)
        )).scalar_one()

        language_id = None
        if language_code:
            language_id = (await session.execute(
                select(Language.id).where(Language.code == language_code)
            )).scalar_one()

        stmt = insert(User).values(
            tg_id=tg_id,
            tg_username=tg_username,
            fuel_id=fuel_id,
            language_id=language_id,
        )

        update_vals = {"fuel_id": fuel_id, "upd_ts": func.now()}
        if language_code is not None:
            update_vals["language_id"] = language_id

        stmt = stmt.on_conflict_do_update(
            index_elements=[User.tg_id],
            set_=update_vals,
        )

        await session.execute(stmt)
        await session.commit()


async def get_user(tg_id: int) -> Optional[Tuple[str, Optional[str]]]:
    """Fetch the user's preferences (fuel code, language code).

    Args:
        tg_id: Telegram user ID.

    Returns:
        Optional[Tuple[str, Optional[str]]]: `(fuel_code, language_code)` or `None`
        if the user does not exist.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(Fuel.code, Language.code)
            .select_from(User)
            .join(Fuel, User.fuel_id == Fuel.id)
            .outerjoin(Language, User.language_id == Language.id)
            .where(User.tg_id == tg_id)
        )
        row = result.first()
        return None if not row else row


async def get_user_id_by_tg_id(tg_id: int) -> Optional[int]:
    """Get internal user ID from Telegram ID.

    Args:
        tg_id: Telegram user ID.

    Returns:
        Optional[int]: Internal `User.id` or `None` if not found.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )
        return result.scalar_one_or_none()


async def get_search_users() -> List[Tuple[int, int]]:
    """Return distinct users that have at least one search.

    Returns:
        List[Tuple[int, int]]: List of `(tg_id, user_id)` pairs.
    """
    async with AsyncSession() as session:
        result = await session.execute(
            select(User.tg_id, User.id)
            .join(Search, Search.user_id == User.id)
            .distinct()
        )
        return result.all()
