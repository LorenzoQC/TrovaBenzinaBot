import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from trovabenzina.config import DATABASE_URL
from .models import Base

log = logging.getLogger(__name__)

ASYNC_SQL_DIR = Path(__file__).parent.parent / "assets" / "config" / "sql"

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
    Create all tables if not already present.
    This should be called at core startup, before handling any requests.
    """
    async with engine.begin() as conn:
        # Force session timezone to Europe/Rome
        await conn.execute(text("SET TIME ZONE 'Europe/Rome';"))
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        # Execute SQL scripts
        if ASYNC_SQL_DIR.exists():
            for sql_file in sorted(ASYNC_SQL_DIR.glob("*.sql")):
                sql_text = sql_file.read_text(encoding="utf-8")
                if not sql_text.strip():
                    continue
                await conn.execute(text(sql_text))
                log.info(f"Executed SQL script: {sql_file.name}")
