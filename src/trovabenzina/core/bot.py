import asyncio
import logging
import os

from telegram.ext import (
    ApplicationBuilder,
)

from trovabenzina.config import BOT_TOKEN, BASE_URL
from trovabenzina.core.scheduler import setup_scheduler
from trovabenzina.db.crud import (
    get_fuel_map,
    get_service_map,
    get_language_map,
)
from trovabenzina.db.session import init_db
from trovabenzina.db.sync import sync_config_tables
from trovabenzina.handlers import (
    start_handler,
    help_handler,
    profile_handler,
    find_handler,
)
from trovabenzina.utils import (
    setup_logging,
    describe,
)

# Configure logging
setup_logging()
log = logging.getLogger(__name__)


def main() -> None:
    """
    Entry point: initialize database, sync config tables, load mapping data,
    setup and run the Telegram core.
    """
    # Create and set a new async event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create database schema if needed
    loop.run_until_complete(init_db())
    log.info("Database schema ensured")

    # Sync fuels, services, and languages from CSV files
    loop.run_until_complete(sync_config_tables())
    log.info("Config tables synced from CSV files")

    # Load mappings from database for core use
    language_map = loop.run_until_complete(get_language_map())
    fuel_map = loop.run_until_complete(get_fuel_map())
    service_map = loop.run_until_complete(get_service_map())

    # Populate module-level maps for handlers
    from trovabenzina.config.settings import LANGUAGE_MAP, FUEL_MAP, SERVICE_MAP
    LANGUAGE_MAP.clear()
    LANGUAGE_MAP.update(language_map)
    FUEL_MAP.clear()
    FUEL_MAP.update(fuel_map)
    SERVICE_MAP.clear()
    SERVICE_MAP.update(service_map)

    log.info(
        "Loaded code maps: %d languages, %d fuels, %d services",
        len(LANGUAGE_MAP), len(FUEL_MAP), len(SERVICE_MAP),
    )

    # Build the Telegram application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(start_handler)  # /start
    app.add_handler(help_handler)  # /help
    app.add_handler(profile_handler)  # /profile
    app.add_handler(find_handler)  # /find

    # Background scheduler setup
    setup_scheduler(loop, app)

    # Debug: list registered handlers
    log.debug("=== HANDLER REGISTRY ===")
    for group, handler_list in app.handlers.items():
        for handler in handler_list:
            log.debug("Group %s -> %s", group, describe(handler))

    # Start webhook server
    log.info("Starting webhook server")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        url_path="webhook",
        webhook_url=f"{BASE_URL}/webhook",
    )


if __name__ == "__main__":
    main()
