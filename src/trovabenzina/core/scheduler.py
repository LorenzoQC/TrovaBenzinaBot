import datetime as dt
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from trovabenzina.config import (
    ENABLE_DONATION,
    SCHEDULER_TIMEZONE,
    CACHE_CLEAN_HOUR,
    MONTHLY_REPORT_DAY,
    MONTHLY_REPORT_HOUR,
    PAYPAL_LINK,
)
from trovabenzina.db.crud import (
    delete_old_geocache,
    get_search_users,
    calculate_monthly_savings,
)

log = logging.getLogger(__name__)


async def clear_cache():
    """
    Remove geocache entries older than 90 days.
    """
    await delete_old_geocache(90)


async def monthly_report(app):
    """Send monthly savings report if donations enabled."""
    if not ENABLE_DONATION:
        return

    today = dt.date.today().replace(day=1)
    start_prev = (today - dt.timedelta(days=1)).replace(day=1)
    end_prev = today - dt.timedelta(days=1)

    # get users who performed searches
    users = await get_search_users()
    for tg_id, user_id in users:
        saving = await calculate_monthly_savings(user_id, start_prev, end_prev)
        if saving <= 0:
            continue

        msg = (
            f"Thanks to TrovaBenzinaBot, last month you saved: {saving:.2f}€*.\n\n"
            "Would you like to buy me a coffee?\n"
            f"{PAYPAL_LINK}\n\n"
            "*Calculation based on 50€ refuel per search."
        )
        try:
            await app.bot.send_message(tg_id, msg)
        except Exception as exc:
            log.warning("Failed to send monthly report to %s: %s", tg_id, exc)


def setup_scheduler(loop, app):
    """Configure and start scheduled jobs."""
    sched = AsyncIOScheduler(event_loop=loop, timezone=SCHEDULER_TIMEZONE)
    sched.add_job(clear_cache, 'cron', hour=CACHE_CLEAN_HOUR)
    sched.add_job(
        monthly_report,
        'cron',
        day=MONTHLY_REPORT_DAY,
        hour=MONTHLY_REPORT_HOUR,
        args=[app]
    )
    sched.start()
    log.info("Scheduler started with timezone %s", SCHEDULER_TIMEZONE)
