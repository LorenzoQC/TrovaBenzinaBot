from urllib.parse import quote_plus

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from trovabenzina.api import fetch_address, call_api, geocode
from trovabenzina.config import (
    DEFAULT_RADIUS_NEAR,
    DEFAULT_RADIUS_FAR,
    DEFAULT_LANGUAGE,
    GEOCODE_HARD_CAP,
)
from trovabenzina.db.crud import get_user, log_search, get_geocache, save_geocache, count_geostats
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_FIND_LOC

__all__ = ["find_handler"]


async def find_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /find command: ask user for address or location."""
    uid = update.effective_user.id
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)

    button = KeyboardButton(text=t("send_location", lang), request_location=True)
    kb = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=kb,
    )
    return STEP_FIND_LOC

async def find_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive a location and perform the search."""
    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude
    await run_search(update, ctx)
    return ConversationHandler.END

async def find_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive an address, geocode (with cache) and perform the search."""
    uid = update.effective_user.id
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)
    address = update.message.text.strip()

    # check cache
    record = await get_geocache(address)
    if record:
        lat, lng = record.lat, record.lng
    else:
        # ensure we haven't hit hard cap
        stats = await count_geostats()
        if stats >= GEOCODE_HARD_CAP:
            await update.message.reply_text(t("geocode_cap_reached", lang))
            return STEP_FIND_LOC

        coords = await geocode(address)
        if not coords:
            await update.message.reply_text(t("invalid_address", lang))
            return STEP_FIND_LOC

        lat, lng = coords
        await save_geocache(address, lat, lng)

    ctx.user_data["search_lat"] = lat
    ctx.user_data["search_lng"] = lng
    await run_search(update, ctx)
    return ConversationHandler.END

async def run_search(origin, ctx: ContextTypes.DEFAULT_TYPE):
    """Perform two radius searches and send top 3 results for each."""
    uid = origin.effective_user.id
    fuel_code, service_code, lang = await get_user(uid)
    ft = f"{fuel_code}-{service_code}"
    lat = ctx.user_data.get("search_lat")
    lng = ctx.user_data.get("search_lng")

    all_prices = []

    for radius, label_key in [
        (DEFAULT_RADIUS_NEAR, "near_label"),
        (DEFAULT_RADIUS_FAR, "far_label")
    ]:
        # perform API call
        res = await call_api(lat, lng, radius, ft)
        results = res.get("results", []) if res else []
        if not results:
            # send header + no stations text
            await origin.message.reply_text(
                f"*{t(label_key, lang)}*\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.MARKDOWN
            )
            continue

        # compute statistics
        fid = int(fuel_code)
        prices = [
            f["price"]
            for r in results
            for f in r["fuels"]
            if f["fuelId"] == fid
        ]
        avg = sum(prices) / len(prices)
        all_prices.extend(prices)

        sorted_res = sorted(
            results,
            key=lambda r: next(f["price"] for f in r["fuels"] if f["fuelId"] == fid)
        )

        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, station in enumerate(sorted_res[:3]):
            price = next(f["price"] for f in station["fuels"] if f["fuelId"] == fid)
            pct = int(round((avg - price) / avg * 100))
            dest = f"{station['location']['lat']},{station['location']['lng']}"
            link = f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(dest)}"

            if price < avg:
                note = t("note_cheaper", lang, pct=pct)
            elif price > avg:
                note = f"⚠️ {t('note_more_expensive', lang, pct=abs(pct))}"
            else:
                note = t("note_equal", lang)

            if not station.get("address"):
                station["address"] = await fetch_address(station["id"]) or t("no_address", lang)

            lines.append(
                f"{medals[i]} *{t('station', lang)}*: {station['brand']} • {station['name']}\n"
                f"*{t('address', lang)}*:{station['address']}\n"
                f"*{t('price', lang)}*: {price:.3f} €xL\n"
                f"*{t('saving', lang)}*: {abs(pct)}% ({t('average', lang)}: {avg} €xL)\n"
                f"*[{t('lets_go', lang)}]({link})*"
            )

        # send combined message: header + lines
        await origin.message.reply_text(
            f"<u>{t(label_key, lang)}</u>\n\n" + "\n\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    # log analytics once after both searches
    lowest = min(all_prices) if all_prices else None
    avg_overall = sum(all_prices) / len(all_prices) if all_prices else 0
    await log_search(uid, avg_overall, lowest)


find_handler = ConversationHandler(
    entry_points=[CommandHandler("find", find_ep)],
    states={
        STEP_FIND_LOC: [
            MessageHandler(filters.LOCATION, find_receive_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_receive_text),
        ],
    },
    fallbacks=[],
    block=True,
)
