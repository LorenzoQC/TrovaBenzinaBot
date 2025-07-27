"""
CRUD operations for configuration, user management, and search logging.
"""
from typing import Optional, Dict, Tuple, Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from .models import Fuel, Service, Language, User
from .session import AsyncSession


async def get_fuel_map() -> Dict[str, str]:
    """
    Return a mapping of fuel names to fuel codes.
    Example: { "Benzina": "1", "Gasolio": "2", ... }
    """
    async with AsyncSession() as session:
        result = await session.execute(select(Fuel))
        fuels = result.scalars().all()
    return {f.name: f.code for f in fuels}


async def get_service_map() -> Dict[str, str]:
    """
    Return a mapping of service names to service codes.
    Example: { "Self-service": "1", "Servito": "0", ... }
    """
    async with AsyncSession() as session:
        result = await session.execute(select(Service))
        services = result.scalars().all()
    return {s.name: s.code for s in services}


async def get_language_map() -> Dict[str, str]:
    """
    Return a mapping of language names to language codes.
    Example: { "Italiano": "it", "English": "en", ... }
    """
    async with AsyncSession() as session:
        result = await session.execute(select(Language))
        languages = result.scalars().all()
    return {l.name: l.code for l in languages}


async def upsert_user(
        tg_id: int,
        fuel_code: str,
        service_code: str,
        language_code: Optional[str] = None,
) -> None:
    """
    Insert or update a user record with preferences.
    Inserts new if tg_id not present; updates fuel, service, and language otherwise.
    """
    async with AsyncSession() as session:
        # Resolve foreign key IDs
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

        # Upsert using PostgreSQL ON CONFLICT
        stmt = insert(User).values(
            tg_id=tg_id,
            fuel_id=fuel_id,
            service_id=service_id,
            language_id=language_id,
        )
        update_dict: Dict[str, Any] = {"fuel_id": fuel_id, "service_id": service_id}
        if language_code is not None:
            update_dict["language_id"] = language_id
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.tg_id],
            set_=update_dict,
        )
        await session.execute(stmt)
        await session.commit()


async def get_user(
        tg_id: int
) -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Return (fuel_code, service_code, language_code) or None.
    """
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


async def log_search(
        tg_id: int,
        price_avg: float,
        price_min: float,
) -> None:
    """
    Record search analytics: inserts a row into searches with timestamp, price_avg, price_min.
    """
    async with AsyncSession() as session:
        await session.execute(
            text(
                "INSERT INTO searches (user_id, ins_ts, price_avg, price_min) "
                "VALUES (:uid, NOW(), :avg, :min)"
            ),
            {"uid": tg_id, "avg": price_avg, "min": price_min}
        )
        await session.commit()


async def get_cached_geocode(
        address: str
) -> Optional[Tuple[float, float]]:
    """
    Return cached (lat, lng) for given address, or None.
    """
    from .models import GeoCache
    async with AsyncSession() as session:
        result = await session.execute(
            select(GeoCache).where(
                GeoCache.address == address,
                GeoCache.del_ts.is_(None)
            )
        )
        obj = result.scalar_one_or_none()
        if obj:
            return obj.lat, obj.lng
        return None


async def upsert_geocode(
        address: str,
        lat: float,
        lng: float,
) -> None:
    """
    Insert or update a geocache record for an address.
    """
    from .models import GeoCache
    async with AsyncSession() as session:
        result = await session.execute(
            select(GeoCache).where(GeoCache.address == address)
        )
        obj = result.scalar_one_or_none()
        if obj:
            obj.lat = lat
            obj.lng = lng
        else:
            obj = GeoCache(address=address, lat=lat, lng=lng)
            session.add(obj)
        await session.commit()


async def get_recent_geocache_count() -> int:
    """
    Return count of recent geocache entries via view v_geostats.
    """
    from .models import VGeoStats
    async with AsyncSession() as session:
        result = await session.execute(select(VGeoStats.count))
        cnt = result.scalar_one_or_none()
        return cnt or 0
