import datetime as dt

import aiosqlite

from config import DB_PATH as DB


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            fuel TEXT,
            service TEXT
        );
        CREATE TABLE IF NOT EXISTS searches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ts DATETIME,
            price_avg REAL,
            price_min REAL
        );
        CREATE TABLE IF NOT EXISTS geocache(
            query TEXT PRIMARY KEY,
            lat REAL,
            lng REAL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS geostats(
            month TEXT PRIMARY KEY,
            cnt INTEGER
        );
        """)
        await db.commit()


async def upsert_user(uid: int, fuel: str, service: str):
    """Save or update user preferences."""
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO users(user_id,fuel,service) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET fuel=excluded.fuel, service=excluded.service",
            (uid, fuel, service),
        )
        await db.commit()


async def get_user(uid: int):
    """Retrieve user preferences or None."""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT fuel,service FROM users WHERE user_id=?", (uid,))
        return await cur.fetchone()


async def log_search(uid: int, avg: float, minimum: float):
    """Record search results for analytics."""
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO searches(user_id,ts,price_avg,price_min) VALUES(?,?,?,?)",
            (uid, dt.datetime.now(), avg, minimum),
        )
        await db.commit()
