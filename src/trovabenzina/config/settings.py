import os

# Database
DB_PATH = os.getenv("DB_PATH", "/data/data.db")

# Geocoding
GEOCODE_HARD_CAP = int(os.getenv("GEOCODE_HARD_CAP", "10000"))  # max monthly requests cached

# Telegram base URL (non-sensitive)
BASE_URL = os.getenv("BASE_URL")  # e.g. https://your.domain

# Scheduler
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Europe/Rome")
CACHE_CLEAN_HOUR = int(os.getenv("CACHE_CLEAN_HOUR", "4"))  # daily at 4:00
MONTHLY_REPORT_DAY = int(os.getenv("MONTHLY_REPORT_DAY", "1"))  # day of month
MONTHLY_REPORT_HOUR = int(os.getenv("MONTHLY_REPORT_HOUR", "9"))
ENABLE_DONATION = os.getenv("ENABLE_DONATION", "true").lower() == "true"
PAYPAL_LINK = os.getenv("PAYPAL_LINK", "https://www.paypal.com/donate")

# MISE API (endpoints, non-sensitive)
MISE_SEARCH_URL = os.getenv(
    "MISE_SEARCH_URL",
    "https://carburanti.mise.gov.it/ospzApi/search/zone"
)
MISE_DETAIL_URL = os.getenv(
    "MISE_DETAIL_URL",
    "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{id}"
)

# Maps API (endpoint, non-sensitive)
GEOCODE_URL = os.getenv(
    "GEOCODE_URL",
    "https://maps.googleapis.com/maps/api/geocode/json"
)

# Default search radii (km)
DEFAULT_RADIUS_NEAR = float(os.getenv("DEFAULT_RADIUS_NEAR", "2"))
DEFAULT_RADIUS_FAR = float(os.getenv("DEFAULT_RADIUS_FAR", "7"))

# Fuel and service mappings
FUEL_MAP = {"Benzina": "1", "Gasolio": "2", "Metano": "3",
            "GPL": "4", "L-GNC": "323", "GNL": "324"}
SERVICE_MAP = {"Self-service": "1", "Servito": "0", "Indifferente": "x"}

# Conversation states
LOC_STATE = 1

# Supported languages
LANGUAGES = {
    "it": "Italiano", "en": "English", "de": "Deutsch",
    "fr": "Français", "es": "Español", "ru": "Русский",
    "zh": "中文", "ja": "日本語", "pt": "Português", "ar": "العربية",
}

# Default language
DEFAULT_LANGUAGE = "it"
