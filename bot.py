import asyncio
import logging
import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)

from config import BOT_TOKEN, BASE_URL
from db import init_db
from handlers import (
    STEP_LANG,
    STEP_FUEL,
    STEP_SERVICE,
    STEP_RADIUS,
    STEP_FAV_NAME,
    STEP_FAV_LOC,
    STEP_LOC
)
from handlers import (
    start,
    language_choice,
    text_handler,
    profilo,
    profile_callback,
    handle_location,
    handle_address,
    show_favorites,
    favorite_selected,
    addfav
)
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    log.info("Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Conversation handler for setup, radius selection, and search flows
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice)],
            STEP_FUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)],
            STEP_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)],
            STEP_RADIUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)],
            STEP_FAV_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)],
            STEP_FAV_LOC: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)
            ],
            STEP_LOC: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)
            ],
        },
        fallbacks=[],
        block=True
    )
    app.add_handler(conv)

    # Inline callbacks for profile editing and favorites
    app.add_handler(CallbackQueryHandler(profile_callback, pattern="^edit_"))
    app.add_handler(CallbackQueryHandler(show_favorites, pattern="^show_favorites$"))
    app.add_handler(CallbackQueryHandler(favorite_selected, pattern="^fav_"))

    # Simple commands
    app.add_handler(CommandHandler("profilo", profilo))
    app.add_handler(CommandHandler("addfav", addfav))

    # Scheduler
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
