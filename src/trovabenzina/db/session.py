from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from models import Base
from trovabenzina.config import DATABASE_URL

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
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
