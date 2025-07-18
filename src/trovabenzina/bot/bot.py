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

from trovabenzina.bot.scheduler import setup_scheduler
from trovabenzina.config import BOT_TOKEN, BASE_URL
from trovabenzina.core.db import init_db
from trovabenzina.handlers.handlers import (
    STEP_LANG,
    STEP_FUEL,
    STEP_SERVICE,
    STEP_FIND_LOC,
    STEP_FIND_RADIUS,
    STEP_FAV_ACTION,
    STEP_FAV_NAME,
    STEP_FAV_LOC,
    STEP_FAV_REMOVE,
    start,
    language_selected,
    fuel_selected,
    service_selected,
    back_to_lang,
    back_to_fuel,
    find_cmd,
    find_receive_location,
    find_receive_text,
    favloc_clicked,
    radius_selected,
    favorites_cmd,
    favorites_callback,
    fav_name,
    fav_loc,
    profile_cmd,
    help_cmd,
)
from trovabenzina.utils.utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)


def main() -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    log.info("DB ready")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                STEP_LANG: [CallbackQueryHandler(language_selected, pattern="^lang_")],
                STEP_FUEL: [
                    CallbackQueryHandler(fuel_selected, pattern="^fuel_"),
                    CallbackQueryHandler(back_to_lang, pattern="^back_lang$"),
                ],
                STEP_SERVICE: [
                    CallbackQueryHandler(service_selected, pattern="^serv_"),
                    CallbackQueryHandler(back_to_fuel, pattern="^back_fuel$"),
                ],
            },
            fallbacks=[],
            block=True,

        )
    )

    # /find
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler(["find", "trova"], find_cmd)],
            states={
                STEP_FIND_LOC: [
                    MessageHandler(filters.LOCATION, find_receive_location),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, find_receive_text),
                    CallbackQueryHandler(favloc_clicked, pattern="^favloc_"),
                ],
                STEP_FIND_RADIUS: [CallbackQueryHandler(radius_selected, pattern="^rad_")],
            },
            fallbacks=[],
            block=True,
        )
    )

    # /favorites
    app.add_handler(
        ConversationHandler(
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
    )

    # shared inline callbacks (edit profile, delete favourite, save favourite)
    app.add_handler(CallbackQueryHandler(favorites_callback, pattern="^(edit_|favdel_|savefav:)"))

    # simple commands
    app.add_handler(CommandHandler(["profile", "profilo"], profile_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    # background jobs
    setup_scheduler(loop, app)

    log.info("Webhook up")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        url_path="webhook",
        webhook_url=f"{BASE_URL}/webhook",
    )


if __name__ == "__main__":
    main()
