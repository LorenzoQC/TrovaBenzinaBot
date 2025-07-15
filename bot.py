import asyncio
import logging
import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN, BASE_URL
from db import init_db
from handlers import (
    # conversation states
    STEP_LANG,
    STEP_FUEL,
    STEP_SERVICE,
    STEP_FIND_LOC,
    STEP_FIND_RADIUS,
    STEP_FAV_ACTION,
    STEP_FAV_NAME,
    STEP_FAV_LOC,
    STEP_FAV_REMOVE,
    # handlers
    start,
    language_choice,
    fuel_choice,
    service_choice,
    find_cmd,
    find_receive_location,
    find_receive_text,
    find_radius_choice,
    favorites_cmd,
    favorites_callback,
    fav_name,
    fav_loc,
    profile_cmd,
    profile_callback,
    help_cmd,
)
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main() -> None:
    # ── event-loop & DB ──────────────────────────────────────────────────────────
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    log.info("Database initialized")

    # ── bot application ─────────────────────────────────────────────────────────
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start ─ profile setup
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice)],
            STEP_FUEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fuel_choice)],
            STEP_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service_choice)],
        },
        fallbacks=[],
        block=True,
    )
    app.add_handler(start_conv)

    # /find ─ search cheapest stations
    find_conv = ConversationHandler(
        entry_points=[CommandHandler(["find", "trova"], find_cmd)],
        states={
            STEP_FIND_LOC: [
                MessageHandler(filters.LOCATION, find_receive_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, find_receive_text),
            ],
            STEP_FIND_RADIUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, find_radius_choice)
            ],
        },
        fallbacks=[],
        block=True,
    )
    app.add_handler(find_conv)

    # /favorites ─ manage favourites
    fav_conv = ConversationHandler(
        entry_points=[CommandHandler("favorites", favorites_cmd)],
        states={
            STEP_FAV_ACTION: [CallbackQueryHandler(favorites_callback, pattern="^(fav_add|fav_edit)$")],
            STEP_FAV_REMOVE: [CallbackQueryHandler(favorites_callback, pattern="^favdel_")],
            STEP_FAV_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, fav_name)],
            STEP_FAV_LOC: [
                MessageHandler(filters.LOCATION, fav_loc),
                MessageHandler(filters.TEXT & ~filters.COMMAND, fav_loc),
            ],
        },
        fallbacks=[],
        block=True,
    )
    app.add_handler(fav_conv)

    # shared inline-callback handlers (edit profile / save favourite)
    app.add_handler(CallbackQueryHandler(profile_callback, pattern="^(edit_|savefav:)"))

    # simple commands
    app.add_handler(CommandHandler(["profile", "profilo"], profile_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    # scheduler (cache cleaning, monthly reports…)
    setup_scheduler(loop, app)

    # ── webhook start ───────────────────────────────────────────────────────────
    log.info("Starting webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        url_path="webhook",
        webhook_url=f"{BASE_URL}/webhook",
    )


if __name__ == "__main__":
    main()
