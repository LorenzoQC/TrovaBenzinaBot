import datetime as dt
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from trovabenzina.config import (
    ENABLE_DONATION,
    SCHEDULER_TIMEZONE,
    CACHE_CLEAN_HOUR,
    MONTHLY_REPORT_DAY,
    MONTHLY_REPORT_HOUR,
    PAYPAL_LINK
)
from trovabenzina.core.db import fetch, execute

log = logging.getLogger(__name__)


async def clear_cache():
    # remove entries older than 90 days
    await execute("DELETE FROM geocache WHERE ts < NOW() - INTERVAL '90 days'")


async def monthly_report(app):
    """Send monthly saving report if donations enabled."""
    if not ENABLE_DONATION:
        return
    today = dt.date.today().replace(day=1)
    start_prev = (today - dt.timedelta(days=1)).replace(day=1)
    end_prev = today - dt.timedelta(days=1)

    # fetch distinct users
    rows = await fetch("SELECT DISTINCT user_id FROM searches")
    for rec in rows:
        uid = rec["user_id"]
        vals = await fetch(
            "SELECT price_avg,price_min FROM searches WHERE user_id=$1 AND ts BETWEEN $2 AND $3",
            uid, start_prev, end_prev
        )
        saving = sum((r["price_avg"] - r["price_min"]) * 50 for r in vals)
        if saving <= 0:
            continue
        msg = (
            f"Thanks to TrovaBenzinaBot, last month you saved: {saving:.2f}€*.\n\n"
            "Would you like to buy me a coffee?\n"
            f"{PAYPAL_LINK}\n\n"
            "*Calculation based on 50€ refuel per search."
        )
        try:
            await app.bot.send_message(uid, msg)
        except Exception as exc:
            log.warning("Failed to send monthly report to %s: %s", uid, exc)


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
