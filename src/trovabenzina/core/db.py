import asyncpg

from trovabenzina.config import DATABASE_URL

# Global connection pool
_db_pool: asyncpg.Pool | None = None

async def init_db():
    """Create tables if they don't exist and migrate schema."""
    global _db_pool
    _db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with _db_pool.acquire() as conn:
        # Initial schema creation
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id      BIGINT PRIMARY KEY,
                fuel         TEXT,
                service      TEXT,
                language     TEXT DEFAULT 'it'
            );
            CREATE TABLE IF NOT EXISTS searches(
                id           SERIAL PRIMARY KEY,
                user_id      BIGINT,
                ts           TIMESTAMP,
                price_avg    REAL,
                price_min    REAL
            );
            CREATE TABLE IF NOT EXISTS geocache(
                query TEXT PRIMARY KEY,
                lat   REAL,
                lng   REAL,
                ts    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS geostats(
                month TEXT PRIMARY KEY,
                cnt   INTEGER
            );
            CREATE TABLE IF NOT EXISTS favorites(
                id      SERIAL PRIMARY KEY,
                user_id BIGINT,
                name    TEXT,
                lat     REAL,
                lng     REAL,
                UNIQUE(user_id, name)
            );
        """)

        # Migrate: add language column if missing
        has_language = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'language'
            )
            """
        )
        if not has_language:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'it'"
            )


async def disconnect_db():
    """Close the connection pool on shutdown."""
    await _db_pool.close()


# Low-level helpers
async def fetch(query: str, *args):
    return await _db_pool.fetch(query, *args)


async def fetchrow(query: str, *args):
    return await _db_pool.fetchrow(query, *args)


async def execute(query: str, *args):
    return await _db_pool.execute(query, *args)


# High-level CRUD methods

# — Users —
async def upsert_user(uid: int, fuel: str, service: str, language: str | None = None):
    """Save or update user preferences (incl. language)."""
    if language is None:
        return await execute(
            """
            INSERT INTO users(user_id, fuel, service)
            VALUES($1, $2, $3)
            ON CONFLICT(user_id) DO UPDATE
              SET fuel = EXCLUDED.fuel,
                  service = EXCLUDED.service
            """,
            uid, fuel, service
        )
    else:
        return await execute(
            """
            INSERT INTO users(user_id, fuel, service, language)
            VALUES($1, $2, $3, $4)
            ON CONFLICT(user_id) DO UPDATE
              SET fuel = EXCLUDED.fuel,
                  service = EXCLUDED.service,
                  language = EXCLUDED.language
            """,
            uid, fuel, service, language
        )

async def get_user(uid: int):
    """Return (fuel, service, language) or None."""
    row = await fetchrow(
        "SELECT fuel, service, language FROM users WHERE user_id = $1",
        uid
    )
    if row:
        return row['fuel'], row['service'], row['language']
    return None


# — Searches —
async def log_search(uid: int, avg: float, minimum: float):
    """Record search results for analytics."""
    return await execute(
        "INSERT INTO searches(user_id, ts, price_avg, price_min) VALUES($1, NOW(), $2, $3)",
        uid, avg, minimum
    )


# — Favorites —
async def add_favorite(uid: int, name: str, lat: float, lng: float):
    """Add or update a favorite location."""
    return await execute(
        """
        INSERT INTO favorites(user_id, name, lat, lng)
        VALUES($1, $2, $3, $4)
        ON CONFLICT(user_id, name) DO UPDATE
          SET lat = EXCLUDED.lat,
              lng = EXCLUDED.lng
        """,
        uid, name, lat, lng
    )

async def list_favorites(uid: int):
    """List all favorite locations for a user."""
    return await fetch(
        "SELECT name, lat, lng FROM favorites WHERE user_id = $1",
        uid
    )

async def delete_favorite(uid: int, name: str):
    """Delete a favorite location by name."""
    return await execute(
        "DELETE FROM favorites WHERE user_id = $1 AND name = $2",
        uid, name
    )
