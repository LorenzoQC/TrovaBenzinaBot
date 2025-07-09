import datetime as dt
import logging

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    DB_PATH as DB,
    ENABLE_DONATION,
    SCHEDULER_TIMEZONE,
    CACHE_CLEAN_HOUR,
    MONTHLY_REPORT_DAY,
    MONTHLY_REPORT_HOUR,
    PAYPAL_LINK
)

log = logging.getLogger(__name__)


async def clear_cache():
    """Remove geocoding entries older than 90 days."""
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM geocache WHERE ts < date('now','-90 days')")
        await db.commit()
    log.info("Geocode cache cleared")


async def monthly_report(app):
    """Send monthly saving report if donations enabled."""
    if not ENABLE_DONATION:
        return
    today = dt.date.today().replace(day=1)
    start_prev = (today - dt.timedelta(days=1)).replace(day=1)
    end_prev = today - dt.timedelta(days=1)

    async with aiosqlite.connect(DB) as db:
        rows = await (await db.execute("SELECT DISTINCT user_id FROM searches")).fetchall()
        for (uid,) in rows:
            vals = await (await db.execute(
                "SELECT price_avg,price_min FROM searches WHERE user_id=? AND ts BETWEEN ? AND ?",
                (uid, start_prev, end_prev)
            )).fetchall()
            saving = sum((avg - mn) * 50 for avg, mn in vals)
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
