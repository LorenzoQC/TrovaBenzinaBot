"""Public surface for the repositories package.

Expose high-level repository functions so callers can do:
    from trovabenzina.db.repositories import get_user, save_search
"""

from .fuel_repository import get_fuel_map, get_fuel_id_by_code
from .geocache_repository import get_geocache, save_geocache, delete_old_geocache
from .language_repository import get_language_map, get_language_id_by_code
from .search_repository import save_search, calculate_monthly_savings
from .stats_repository import count_geocoding_month_calls, get_user_stats
from .user_repository import upsert_user, get_user, get_user_id_by_tg_id, get_search_users

__all__ = [
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
