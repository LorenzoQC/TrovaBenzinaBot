from datetime import datetime
from urllib.parse import quote_plus

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
from trovabenzina.db.crud import (
    get_user,
    save_search,
    get_geocache,
    save_geocache,
    count_geocoding_month_calls,
)
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_FIND_LOCATION

__all__ = ["find_handler"]

async def find_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /find command: ask user for address or location."""
    uid = update.effective_user.id
    _, lang = await get_user(uid) or (None, DEFAULT_LANGUAGE)

    button = KeyboardButton(text=t("send_location", lang), request_location=True)
    kb = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=kb,
    )
    return STEP_FIND_LOCATION

async def find_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive a location and perform the search."""
    uid = update.effective_user.id
    _, lang = await get_user(uid) or (None, DEFAULT_LANGUAGE)
    proc_msg = await update.message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc_msg.message_id

    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude
    await run_search(update, ctx)
    return ConversationHandler.END

async def find_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive an address, geocode (with cache) and perform the search."""
    uid = update.effective_user.id
    _, lang = await get_user(uid) or (None, DEFAULT_LANGUAGE)
    proc_msg = await update.message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc_msg.message_id
    address = update.message.text.strip()

    record = await get_geocache(address)
    if record:
        lat, lng = record.lat, record.lng
    else:
        stats = await count_geocoding_month_calls()
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
    """Perform two radius searches, filter by fuel, send top 3 below-average and log each."""
    uid = origin.effective_user.id
    fuel_code, lang = await get_user(uid)
    lat = ctx.user_data.get("search_lat")
    lng = ctx.user_data.get("search_lng")
    price_unit_all = f"{t('eur_symbol', lang)}{t('slash_symbol', lang)}{t('liter_symbol', lang)}"
    price_unit_cng = f"{t('eur_symbol', lang)}{t('slash_symbol', lang)}{t('kilo_symbol', lang)}"
    price_unit = price_unit_cng if fuel_code == "3" else price_unit_all
    fid = int(fuel_code)
    ft = f"{fuel_code}-x"

    for radius, label_key in [
        (DEFAULT_RADIUS_NEAR, "near_label"),
        (DEFAULT_RADIUS_FAR, "far_label")
    ]:
        res = await call_api(lat, lng, radius, ft)
        stations = res.get("results", []) if res else []
        num_stations = len(stations)

        # delete the “processing” message if present
        chat_id = origin.effective_chat.id
        proc_id = ctx.user_data.pop("processing_msg_id", None)
        if proc_id:
            try:
                await ctx.bot.delete_message(chat_id, proc_id)
            except Exception:
                pass

        # first filter: by fuelId only
        filtered = []
        for st in stations:
            fuels = [
                f for f in st.get("fuels", [])
                if f.get("fuelId") == fid
            ]
            if fuels:
                st["_filtered_fuels"] = fuels
                filtered.append(st)

        if not filtered:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML
            )
            await save_search(uid, fuel_code, radius, num_stations, None, None)
            continue

        # determine target service type based on lowest price fuel; prefer self-service on ties
        all_fuels = [f for st in filtered for f in st["_filtered_fuels"]]
        min_fuel = min(
            all_fuels,
            key=lambda f: (f["price"], not f.get("isSelf"))
        )
        target_is_self = min_fuel.get("isSelf")

        # choose cheapest for each station (prefer self-service on price ties) and filter by service type
        for st in filtered:
            st["_chosen_fuel"] = min(
                st["_filtered_fuels"],
                key=lambda f: (f["price"], not f.get("isSelf"))
            )
        filtered = [
            st for st in filtered
            if st["_chosen_fuel"].get("isSelf") == target_is_self
        ]
        num_stations = len(filtered)

        if not filtered:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML
            )
            await save_search(uid, fuel_code, radius, num_stations, None, None)
            continue

        # calculate average on chosen fuels
        avg = sum(
            st["_chosen_fuel"]["price"] for st in filtered
        ) / len(filtered)

        # second filter: only stations with price <= average
        below_avg = [
            st for st in filtered
            if st["_chosen_fuel"]["price"] <= avg
        ]

        if not below_avg:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML
            )
            await save_search(uid, fuel_code, radius, num_stations, None, None)
            continue

        # sort by ascending price
        sorted_res = sorted(
            below_avg,
            key=lambda r: r["_chosen_fuel"]["price"]
        )

        # compute the lowest price among those below average
        lowest = sorted_res[0]["_chosen_fuel"]["price"]

        # build message lines for the top 3
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, station in enumerate(sorted_res[:3]):
            f0 = station["_chosen_fuel"]
            price = f0["price"]
            pct = int(round((avg - price) / avg * 100))
            dest = f"{station['location']['lat']},{station['location']['lng']}"
            link = f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(dest)}"

            if not station.get("address"):
                station["address"] = await fetch_address(station["id"]) or t("no_address", lang)

            raw_date = station.get("insertDate")
            if raw_date:
                dt = datetime.fromisoformat(raw_date)
                formatted_date = dt.strftime("%d/%m/%Y %H:%M")
            else:
                formatted_date = t("unknown_update", lang)

            price_note = (
                t('equal_average', lang) if pct == 0 else f"{pct}% {t('below_average', lang)}"
            )

            lines.append(
                f"{medals[i]} <b><a href=\"{link}\">{station['brand']} • {station['name']}</a></b>\n"
                f"• <u>{t('address', lang)}</u>: {station['address']}\n"
                f"• <u>{t('price', lang)}</u>: <b>{price:.3f} {price_unit}</b>, {price_note}\n"
                f"<i>[{t('last_update', lang)}: {formatted_date}]</i>"
            )

        header = (
            f"<b><u>{t(label_key, lang)}</u></b> 📍\n"
            f"{num_stations} {t('stations_analyzed', lang)}\n"
            f"{t('average_zone_price', lang)}: <b>{avg:.3f} {price_unit}</b>\n\n"
        )

        await origin.message.reply_text(
            header + "\n\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

        await save_search(
            uid,
            fuel_code,
            radius,
            num_stations,
            round(avg, 3),
            round(lowest, 3)
        )

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
