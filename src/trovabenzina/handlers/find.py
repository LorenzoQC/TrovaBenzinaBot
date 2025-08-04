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
from trovabenzina.db.crud import get_user, save_search, get_geocache, save_geocache, count_geostats
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_FIND_LOCATION

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
    return STEP_FIND_LOCATION

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
        stats = await count_geostats()
        if stats >= GEOCODE_HARD_CAP:
            await update.message.reply_text(t("geocode_cap_reached", lang))
            return STEP_FIND_LOCATION

        coords = await geocode(address)
        if not coords:
            await update.message.reply_text(t("invalid_address", lang))
            return STEP_FIND_LOCATION

        lat, lng = coords
        await save_geocache(address, lat, lng)

    ctx.user_data["search_lat"] = lat
    ctx.user_data["search_lng"] = lng
    await run_search(update, ctx)
    return ConversationHandler.END

async def run_search(origin, ctx: ContextTypes.DEFAULT_TYPE):
    """Perform two radius searches, filter by fuel/service, send top 3 below-average and log each."""
    uid = origin.effective_user.id
    fuel_code, service_code, lang = await get_user(uid)
    lat = ctx.user_data.get("search_lat")
    lng = ctx.user_data.get("search_lng")

    # determine self-service flag
    is_self = service_code == "1"
    fid = int(fuel_code)
    ft = f"{fuel_code}-{service_code}"

    for radius, label_key in [
        (DEFAULT_RADIUS_NEAR, "near_label"),
        (DEFAULT_RADIUS_FAR, "far_label")
    ]:
        res = await call_api(lat, lng, radius, ft)
        stations = res.get("results", []) if res else []

        # first filter: fuelId and isSelf
        filtered = []
        for st in stations:
            fuels = [
                f for f in st.get("fuels", [])
                if f.get("fuelId") == fid and f.get("isSelf") == is_self
            ]
            if fuels:
                st["_filtered_fuels"] = fuels
                filtered.append(st)

        if not filtered:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML
            )
            await save_search(uid, fuel_code, service_code, 0.0, 0.0)
            continue

        # calculate prices and average
        prices = [f["price"] for st in filtered for f in st["_filtered_fuels"]]
        avg = sum(prices) / len(prices)

        # second filter: only stations with price <= average
        below_avg = [
            st for st in filtered
            if st["_filtered_fuels"][0]["price"] <= avg
        ]

        if not below_avg:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML
            )
            await save_search(uid, fuel_code, service_code, 0.0, 0.0)
            continue

        # sort by ascending price
        sorted_res = sorted(
            below_avg,
            key=lambda r: r["_filtered_fuels"][0]["price"]
        )

        # compute the lowest price among those below average
        lowest = min(
            f["price"]
            for st in below_avg
            for f in st["_filtered_fuels"]
        )

        # build message lines for the top 3
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, station in enumerate(sorted_res[:3]):
            f0 = station["_filtered_fuels"][0]
            price = f0["price"]
            pct = int(round((avg - price) / avg * 100))
            dest = f"{station['location']['lat']},{station['location']['lng']}"
            link = f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(dest)}"

            if not station.get("address"):
                station["address"] = await fetch_address(station["id"]) or t("no_address", lang)

            if abs(pct) == 0:
                price_note = t('equal_average', lang)
            else:
                price_note = t('below_average', lang, pct=abs(pct))

            lines.append(
                f"{medals[i]} <b><a href=\"{link}\">{station['brand']} • {station['name']}</a></b>\n"
                f"<b>{t('address', lang)}</b>: {station['address']}\n"
                f"<b>{t('price', lang)}</b>: {price:.3f} {t('price_unit', lang)}, {price_note}"
            )

        # send the combined message
        await origin.message.reply_text(
            f"<u>{t(label_key, lang)}</u> 📍\n" +
            f"{t('average_zone_price', lang)}: {avg:.3f}\n\n" +
            "\n\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        # log each search
        await save_search(uid, fuel_code, service_code, round(avg, 3), round(lowest, 3))


find_handler = ConversationHandler(
    entry_points=[CommandHandler("find", find_ep)],
    states={
        STEP_FIND_LOCATION: [
            MessageHandler(filters.LOCATION, find_receive_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_receive_text),
        ],
    },
    fallbacks=[],
    block=True,
    allow_reentry=True,
)
