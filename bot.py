import asyncio
import logging
import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

from config import BOT_TOKEN, BASE_URL, LOC_STATE
from db import init_db
from handlers import start, text_handler, profilo, trova, handle_location, handle_address
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    log.info("Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profilo", profilo))

    # Conversation handler for location/address
    conv = ConversationHandler(
        entry_points=[CommandHandler("trova", trova)],
        states={
            LOC_STATE: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)
            ]
        },
        fallbacks=[],
        block=True
    )
    app.add_handler(conv)

    # Catch-all text handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Setup scheduled jobs
    setup_scheduler(loop, app)

    log.info("Starting webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        url_path="webhook",
        webhook_url=f"{BASE_URL}/webhook"
    )


if __name__ == "__main__":
    main()
