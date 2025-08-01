"""
CRUD operations for configuration, user management, search logging, and geocode caching.
"""
import logging
from datetime import date
from typing import Optional, Dict, Tuple, Any, List

from sqlalchemy import text, delete, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from .models import Fuel, Service, Language, User, GeoCache, Search
from .session import AsyncSession

logger = logging.getLogger(__name__)


async def get_language_map() -> Dict[str, str]:
    async with AsyncSession() as session:
        result = await session.execute(
            select(Language).where(Language.del_ts.is_(None))
        )
        languages = result.scalars().all()
    return {l.name: l.code for l in languages}


async def get_fuel_map() -> Dict[str, str]:
    async with AsyncSession() as session:
        result = await session.execute(
            select(Fuel).where(Fuel.del_ts.is_(None))
        )
        fuels = result.scalars().all()
    return {f.name: f.code for f in fuels}


async def get_service_map() -> Dict[str, str]:
    async with AsyncSession() as session:
        result = await session.execute(
            select(Service).where(Service.del_ts.is_(None))
        )
        services = result.scalars().all()
    return {s.name: s.code for s in services}


async def upsert_user(
        tg_id: int,
        tg_username: str,
        fuel_code: str,
        service_code: str,
        language_code: Optional[str] = None,
) -> None:
    async with AsyncSession() as session:
        fuel_id = (await session.execute(
            select(Fuel.id).where(Fuel.code == fuel_code)
        )).scalar_one()
        service_id = (await session.execute(
            select(Service.id).where(Service.code == service_code)
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
            service_id=service_id,
            language_id=language_id,
        )
        update_vals: Dict[str, Any] = {"fuel_id": fuel_id, "service_id": service_id}
        if language_code is not None:
            update_vals["language_id"] = language_id
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.tg_id],
            set_=update_vals,
        )
        await session.execute(stmt)
        await session.commit()


async def get_user(
        tg_id: int
) -> Optional[Tuple[str, str, Optional[str]]]:
    async with AsyncSession() as session:
        result = await session.execute(
            select(Fuel.code, Service.code, Language.code)
            .select_from(User)
            .join(Fuel, User.fuel_id == Fuel.id)
            .join(Service, User.service_id == Service.id)
            .outerjoin(Language, User.language_id == Language.id)
            .where(User.tg_id == tg_id)
        )
        row = result.first()
        if not row:
            return None
        return row


async def save_search(
        tg_id: int,
        fuel_code: str,
        service_code: str,
        price_avg: float,
        price_min: float,
) -> None:
    """
    Record search analytics: insert into searches with correct foreign keys.
    """
    async with AsyncSession() as session:
        # get internal user id
        user_id = (await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )).scalar_one()
        # get fuel and service ids
        fuel_id = (await session.execute(
            select(Fuel.id).where(Fuel.code == fuel_code)
        )).scalar_one()
        service_id = (await session.execute(
            select(Service.id).where(Service.code == service_code)
        )).scalar_one()
        # insert Search record
        new_search = Search(
            user_id=user_id,
            fuel_id=fuel_id,
            service_id=service_id,
            price_avg=price_avg,
            price_min=price_min,
        )
        session.add(new_search)
        await session.commit()


async def get_geocache(
        address: str
) -> Optional[GeoCache]:
    async with AsyncSession() as session:
        result = await session.execute(
            select(GeoCache).where(
                GeoCache.address == address,
                GeoCache.del_ts.is_(None)
            )
        )
        return result.scalar_one_or_none()


async def save_geocache(
        address: str,
        lat: float,
        lng: float,
) -> None:
    async with AsyncSession() as session:
        existing = (await session.execute(
            select(GeoCache).where(GeoCache.address == address)
        )).scalar_one_or_none()
        if existing:
            existing.lat = lat
            existing.lng = lng
        else:
            new_entry = GeoCache(address=address, lat=lat, lng=lng)
            session.add(new_entry)
        await session.commit()


async def count_geostats() -> int:
    async with AsyncSession() as session:
        result = await session.execute(
            select(text("count")).select_from(text("v_geostats"))
        )
        cnt = result.scalar_one_or_none()
        return cnt or 0


async def delete_old_geocache(days: int = 90) -> None:
    async with AsyncSession() as session:
        await session.execute(
            delete(GeoCache).where(
                GeoCache.ins_ts < func.now() - text(f"INTERVAL '{days} days'")
            )
        )
        await session.commit()


async def get_search_users() -> List[Tuple[int, int]]:
    async with AsyncSession() as session:
        result = await session.execute(
            select(User.tg_id, User.id)
            .join(Search, Search.user_id == User.id)
            .distinct()
        )
        return result.all()


async def calculate_monthly_savings(
        user_id: int,
        start_date: date,
        end_date: date,
) -> float:
    async with AsyncSession() as session:
        result = await session.execute(
            select(Search.price_avg, Search.price_min)
            .where(Search.user_id == user_id)
            .where(Search.ins_ts.between(start_date, end_date))
        )
        rows = result.all()
    return sum((r.price_avg - r.price_min) * 50 for r in rows)
