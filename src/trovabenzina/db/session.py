from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from trovabenzina.config import DATABASE_URL
from .models import Base

_url = make_url(DATABASE_URL)
if _url.drivername == "postgresql":
    _url = _url.set(drivername="postgresql+asyncpg")

# Create async engine and session factory
engine = create_async_engine(_url, echo=False)
AsyncSession = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Create all tables and the 'v_geostats' view if not already present.
    This should be called at bot startup, before handling any requests.
    """
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        # Create or replace the view for geocache stats:
        await conn.execute(text("""
            CREATE OR REPLACE VIEW v_geostats AS
            SELECT
              COUNT(*)::int AS count
            FROM geocache
            WHERE
              del_ts IS NULL
              AND ins_ts >= NOW() - INTERVAL '30 days'
        """))
