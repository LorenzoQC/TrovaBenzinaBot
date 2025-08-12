import asyncio
import logging
import os

from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters,
)
from telegram.request import HTTPXRequest

from ..config import BOT_TOKEN, BASE_URL
from ..db import (
    init_db,
    sync_config_tables,
    get_fuel_map,
    get_language_map
)
from ..handlers import (
    start_handler,
    help_handler,
    profile_handler,
    search_handler,
    radius_callback_handler,
    statistics_handler,
    handle_unknown_command,
)
from ..utils import (
    setup_logging,
    describe,
)

KNOWN_CMDS_RE = r"^/(start|find|profile|help)(?:@\w+)?(?:\s|$)"

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

    # Sync languages and fuels from CSV files
    loop.run_until_complete(sync_config_tables())
    log.info("Config tables synced from CSV files")

    # Load mappings from database for core use
    language_map = loop.run_until_complete(get_language_map())
    fuel_map = loop.run_until_complete(get_fuel_map())

    # Populate module-level maps for handlers
    from trovabenzina.config.settings import LANGUAGE_MAP, FUEL_MAP
    LANGUAGE_MAP.clear()
    LANGUAGE_MAP.update(language_map)
    FUEL_MAP.clear()
    FUEL_MAP.update(fuel_map)

    log.info(
        "Loaded code maps: %d languages, %d fuels",
        len(LANGUAGE_MAP), len(FUEL_MAP),
    )

    httpx_request = HTTPXRequest(
        connect_timeout=20.0,  # maximum time to establish the connection
        read_timeout=20.0,  # maximum time to receive the response
        write_timeout=20.0,  # maximum time to send the payload
        pool_timeout=5.0,  # maximum wait time to acquire a connection from the pool
    )

    # Build the Telegram application
    app = (ApplicationBuilder()
           .token(BOT_TOKEN)
           .request(httpx_request)
           .build())

    # Add handlers
    app.add_handler(start_handler)  # /start
    for handler in statistics_handler:  # /statistics
        app.add_handler(handler)
    app.add_handler(help_handler)  # /help
    app.add_handler(search_handler)  # /search
    app.add_handler(radius_callback_handler)  # /search radius callbacks
    app.add_handler(profile_handler)  # /profile
    app.add_handler(MessageHandler(filters.COMMAND & ~filters.Regex(KNOWN_CMDS_RE), handle_unknown_command),
                    group=98)  # unknown commands

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
