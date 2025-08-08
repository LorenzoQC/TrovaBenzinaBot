"""Public API surface for external consumers of the 'api' package.

Exposes:
- Google Maps Geocoding
- MISE search (fuel stations by zone, price-ordered)
- MISE station detail (address)
"""

from .googlemaps.geocoding import geocode_address
from .mise.station_detail import get_station_address
from .mise.stations_search import search_stations

__all__ = [
    "geocode_address",
    "search_stations",
    "get_station_address",
]
