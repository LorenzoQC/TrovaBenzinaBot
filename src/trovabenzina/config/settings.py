# src/trovabenzina/config/settings.py

import os

# Database connection URL, e.g. postgresql+asyncpg://user:pass@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# Geocoding cache: maximum number of monthly requests to cache
GEOCODE_HARD_CAP = int(os.getenv("GEOCODE_HARD_CAP", "10000"))

# Telegram webhook base URL (publicly reachable, non-sensitive)
BASE_URL = os.getenv("BASE_URL")

# Scheduler configuration
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Europe/Rome")
# Hour of day to perform daily cache cleanup (0–23)
CACHE_CLEAN_HOUR = int(os.getenv("CACHE_CLEAN_HOUR", "4"))
# Day of month and hour to send monthly report
MONTHLY_REPORT_DAY = int(os.getenv("MONTHLY_REPORT_DAY", "1"))
MONTHLY_REPORT_HOUR = int(os.getenv("MONTHLY_REPORT_HOUR", "9"))

# Donation feature toggle and PayPal link
ENABLE_DONATION = os.getenv("ENABLE_DONATION", "true").lower() == "true"
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://www.paypal.com/donate")

# MISE API endpoints (non-sensitive)
MISE_SEARCH_URL = os.getenv(
    "MISE_SEARCH_URL",
    "https://carburanti.mise.gov.it/ospzApi/search/zone"
)
MISE_DETAIL_URL = os.getenv(
    "MISE_DETAIL_URL",
    "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{id}"
)

# Google Maps Geocoding API endpoint (non-sensitive)
GEOCODE_URL = os.getenv(
    "GEOCODE_URL",
    "https://maps.googleapis.com/maps/api/geocode/json"
)

# Default search radii in kilometers
DEFAULT_RADIUS_NEAR = float(os.getenv("DEFAULT_RADIUS_NEAR", "2"))
DEFAULT_RADIUS_FAR = float(os.getenv("DEFAULT_RADIUS_FAR", "7"))

# In‐memory maps (populated at startup from the database)
# Keys: display name; Values: code string
FUEL_MAP = {}
LANGUAGE_MAP = {}

# Conversation states (for backward‐compatibility)
LOC_STATE = 1

# Default fallback language
DEFAULT_LANGUAGE = "it"
