import datetime as dt

import aiosqlite

from config import DB_PATH as DB


async def init_db():
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            user_id      INTEGER PRIMARY KEY,
            fuel         TEXT,
            service      TEXT,
            language     TEXT DEFAULT 'it'
        );
        CREATE TABLE IF NOT EXISTS searches(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            ts           DATETIME,
            price_avg    REAL,
            price_min    REAL
        );
        CREATE TABLE IF NOT EXISTS geocache(
            query TEXT PRIMARY KEY,
            lat   REAL,
            lng   REAL,
            ts    DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS geostats(
            month TEXT PRIMARY KEY,
            cnt   INTEGER
        );
        CREATE TABLE IF NOT EXISTS favorites(
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name    TEXT,
            lat     REAL,
            lng     REAL,
            UNIQUE(user_id,name)
        );
        """)
        await db.commit()

async def upsert_user(uid: int, fuel: str, service: str, language: str = None):
    """Save or update user preferences (incl. language)."""
    async with aiosqlite.connect(DB) as db:
        if language is None:
            await db.execute(
                "INSERT INTO users(user_id,fuel,service) VALUES(?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET fuel=excluded.fuel,service=excluded.service",
                (uid, fuel, service)
            )
        else:
            await db.execute(
                "INSERT INTO users(user_id,fuel,service,language) VALUES(?,?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET fuel=excluded.fuel,service=excluded.service,language=excluded.language",
                (uid, fuel, service, language)
            )
        await db.commit()

async def get_user(uid: int):
    """Return (fuel, service, language) or None."""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT fuel,service,language FROM users WHERE user_id=?", (uid,)
        )
        return await cur.fetchone()

async def log_search(uid: int, avg: float, minimum: float):
    """Record search results for analytics."""
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO searches(user_id,ts,price_avg,price_min) VALUES(?,?,?,?)",
            (uid, dt.datetime.now(), avg, minimum),
        )
        await db.commit()

async def add_favorite(uid: int, name: str, lat: float, lng: float):
    """Add or update a favorite location."""
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO favorites(user_id,name,lat,lng) VALUES(?,?,?,?)",
            (uid, name, lat, lng)
        )
        await db.commit()

async def list_favorites(uid: int):
    """List all favorite locations for a user."""
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT name,lat,lng FROM favorites WHERE user_id=?", (uid,)
        )
        return await cur.fetchall()

async def delete_favorite(uid: int, name: str):
    """Delete a favorite location by name."""
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "DELETE FROM favorites WHERE user_id=? AND name=?", (uid, name)
        )
        await db.commit()
