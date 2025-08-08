"""Top-level exports for the `trovabenzina.db` package.

Expose:
- ORM models and mixins (Base, TimestampMixin, CodeNameMixin, entities, views)
- Session/engine helpers (engine, AsyncSession, init_db)
- Repository functions (get_user, save_search, maps, stats, geocache, etc.)
"""

# Models
from .models import (
    Base,
    TimestampMixin,
    CodeNameMixin,
    Fuel,
    Language,
    User,
    Search,
    GeoCache,
    VGeocodingMonthCalls,
    VUsersSearchesStats,
)
# Repository functions (instead of legacy crud)
from .repositories import (
    # maps
    get_fuel_map,
    get_fuel_id_by_code,
    get_language_map,
    get_language_id_by_code,
    # users
    upsert_user,
    get_user,
    get_user_id_by_tg_id,
    get_search_users,
    # searches
    save_search,
    calculate_monthly_savings,
    # geocache
    get_geocache,
    save_geocache,
    delete_old_geocache,
    # stats/views
    count_geocoding_month_calls,
    get_user_stats,
)
# Session
from .session import engine, AsyncSession, init_db

__all__ = [
    # Models/mixins
    "Base",
    "TimestampMixin",
    "CodeNameMixin",
    "Fuel",
    "Language",
    "User",
    "Search",
    "GeoCache",
    "VGeocodingMonthCalls",
    "VUsersSearchesStats",
    # Session
    "engine",
    "AsyncSession",
    "init_db",
    # Repositories
    "get_fuel_map",
    "get_fuel_id_by_code",
    "get_language_map",
    "get_language_id_by_code",
    "upsert_user",
    "get_user",
    "get_user_id_by_tg_id",
    "get_search_users",
    "save_search",
    "calculate_monthly_savings",
    "get_geocache",
    "save_geocache",
    "delete_old_geocache",
    "count_geocoding_month_calls",
    "get_user_stats",
]
