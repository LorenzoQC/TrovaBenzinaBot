from __future__ import annotations

"""
Database session and initialization helpers.

This module exposes:
- `engine`: the async SQLAlchemy engine (asyncpg for PostgreSQL).
- `AsyncSession`: session factory for async ORM use.
- `init_db()`: idempotent database initializer (tables + optional SQL scripts).

Notes:
    - Models must be imported before `Base.metadata.create_all()` so that all
      mapped classes are registered. We import the `models` package explicitly
      for that side effect.
"""

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from trovabenzina.config import DATABASE_URL
from .models import Base
from . import models as _models  # side-effect import: registers all mapped classes

log = logging.getLogger(__name__)

# Project root and SQL assets directory (adjust if your layout changes)
BASE_DIR = Path(__file__).resolve().parents[3]
ASSETS_SQL_DIR = BASE_DIR / "assets" / "config" / "sql"

# Normalize URL to async driver if it's plain "postgresql"
_url = make_url(DATABASE_URL)
if _url.drivername == "postgresql":
    _url = _url.set(drivername="postgresql+asyncpg")

# Async engine and session factory
engine = create_async_engine(_url, echo=False, pool_pre_ping=True, future=True)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


def _ensure_models_loaded() -> None:
    """Touch exported symbols to silence linters while ensuring models are imported.

    This function relies on the side effect of importing `.models` above.
    """
    _ = (
        _models.Fuel,
        _models.Language,
        _models.User,
        _models.Search,
        _models.GeoCache,
        _models.VGeocodingMonthCalls,
        _models.VUsersSearchesStats,
    )
    return None


def _split_sql_naive(sql: str) -> list[str]:
    """Naively split a SQL script into statements by ';'.

    Warning:
        This splitter is safe for simple DDL like CREATE VIEW statements.
        It is NOT suitable for complex scripts with functions/procedures,
        dollar-quoted bodies, or semicolons inside string literals.

    Args:
        sql: Raw SQL script content.

    Returns:
        List of statements without trailing semicolons and surrounding whitespace.
    """
    return [s.strip() for s in sql.split(";") if s.strip()]


async def _execute_sql_scripts_dir(dir_path: Path) -> None:
    """Execute all .sql files in a directory, sorted by filename.

    For each file:
        - Try to execute as a single statement.
        - If it fails, fallback to a naive split and execute statements one-by-one.

    Args:
        dir_path: Directory containing .sql files.
    """
    if not dir_path.exists():
        log.info("SQL assets directory not found: %s", dir_path)
        return

    sql_files = sorted(dir_path.glob("*.sql"))
    if not sql_files:
        log.info("No SQL scripts to execute under: %s", dir_path)
        return

    async with engine.begin() as conn:
        for sql_file in sql_files:
            raw = sql_file.read_text(encoding="utf-8").strip()
            if not raw:
                continue

            try:
                # Fast path: single-statement file
                await conn.execute(text(raw))
                log.info("Executed SQL script: %s", sql_file.name)
            except Exception as e:
                # Fallback: naive split into multiple statements
                log.warning(
                    "Single-statement execution failed for %s (%s). "
                    "Falling back to naive split.",
                    sql_file.name,
                    e,
                )
                statements = _split_sql_naive(raw)
                for stmt in statements:
                    try:
                        # `exec_driver_sql` bypasses SQLAlchemy SQL compiler
                        await conn.exec_driver_sql(stmt)
                    except Exception as inner:
                        log.error(
                            "Error executing statement from %s:\n---\n%s\n---\n%s",
                            sql_file.name,
                            stmt,
                            inner,
                        )
                        raise
                log.info("Executed SQL script (split): %s", sql_file.name)


async def init_db() -> None:
    """Initialize database: set session timezone, create tables, run SQL assets.

    Steps:
        1) Set session time zone to Europe/Rome (server-side).
        2) Create all tables from SQLAlchemy metadata.
        3) Execute optional SQL scripts (e.g., CREATE OR REPLACE VIEW ...).

    Notes:
        - Ensure models are imported before `create_all()` so that all mappings
          are present on `Base.metadata`.
        - SQL scripts are executed within a transaction; failing statements will
          abort the transaction and raise, making the deploy fail fast.

    Raises:
        Exception: Propagates any SQL execution error for visibility in logs.
    """
    # Step 1: set TZ and create tables
    async with engine.begin() as conn:
        # Force session timezone (affects NOW(), etc.)
        await conn.execute(text("SET TIME ZONE 'Europe/Rome';"))

        # Ensure models are imported/registered on Base.metadata
        _ensure_models_loaded()

        # Create tables for all mapped classes
        await conn.run_sync(Base.metadata.create_all)

    # Step 2: execute SQL assets (e.g., create/replace views)
    await _execute_sql_scripts_dir(ASSETS_SQL_DIR)
