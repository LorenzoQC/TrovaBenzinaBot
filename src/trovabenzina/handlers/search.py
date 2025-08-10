from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from trovabenzina.config import (
    DEFAULT_RADIUS_NEAR,
    DEFAULT_RADIUS_FAR,
    GEOCODE_HARD_CAP,
)
from trovabenzina.i18n import t
from trovabenzina.utils import STEP_SEARCH_LOCATION
from trovabenzina.utils.formatting import (
    format_price_unit,
    format_price,
    format_avg_comparison_text,
    format_date,
    format_directions_url,
)
from ..api import get_station_address, search_stations, geocode_address
from ..db import (
    get_user,
    save_search,
    get_geocache,
    save_geocache,
    count_geocoding_month_calls,
    get_uom_by_code,
    get_user_language_code_by_tg_id,
)

__all__ = ["search_handler"]


async def search_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /search command: ask user for address or location."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)

    button = KeyboardButton(text=t("send_location", lang), request_location=True)
    kb = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=kb,
    )
    return STEP_SEARCH_LOCATION


async def search_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive a location and perform the search."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
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


async def search_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive an address, geocode (with cache) and perform the search."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
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
            return STEP_SEARCH_LOCATION

        coords = await geocode_address(address)
        if not coords:
            await update.message.reply_text(t("invalid_address", lang))
            return STEP_SEARCH_LOCATION

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

    uom = (await get_uom_by_code(fuel_code)) or "L"
    price_unit = format_price_unit(uom=uom, t=t, lang=lang)

    fid = int(fuel_code)
    ft = f"{fuel_code}-x"

    for radius, label_key in [
        (DEFAULT_RADIUS_NEAR, "near_label"),
        (DEFAULT_RADIUS_FAR, "far_label"),
    ]:
        res = await search_stations(lat, lng, radius, ft)
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
            fuels = [f for f in st.get("fuels", []) if f.get("fuelId") == fid]
            if fuels:
                st["_filtered_fuels"] = fuels
                filtered.append(st)

        if not filtered:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML,
            )
            await save_search(uid, fuel_code, radius, num_stations, None, None)
            continue

        # determine target service type based on lowest price fuel; prefer self-service on ties
        all_fuels = [f for st in filtered for f in st["_filtered_fuels"]]
        min_fuel = min(all_fuels, key=lambda f: (f["price"], not f.get("isSelf")))
        target_is_self = min_fuel.get("isSelf")

        # choose cheapest for each station (prefer self-service on price ties) and filter by service type
        for st in filtered:
            st["_chosen_fuel"] = min(
                st["_filtered_fuels"], key=lambda f: (f["price"], not f.get("isSelf"))
            )
        filtered = [st for st in filtered if st["_chosen_fuel"].get("isSelf") == target_is_self]
        num_stations = len(filtered)

        if not filtered:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML,
            )
            await save_search(uid, fuel_code, radius, num_stations, None, None)
            continue

        # calculate average on chosen fuels
        avg = sum(st["_chosen_fuel"]["price"] for st in filtered) / len(filtered)

        # second filter: only stations with price <= average
        below_avg = [st for st in filtered if st["_chosen_fuel"]["price"] <= avg]

        if not below_avg:
            await origin.message.reply_text(
                f"<u>{t(label_key, lang)}</u> 📍\n\n{t('no_stations', lang)}",
                parse_mode=ParseMode.HTML,
            )
            await save_search(uid, fuel_code, radius, num_stations, None, None)
            continue

        # sort by ascending price
        sorted_res = sorted(below_avg, key=lambda r: r["_chosen_fuel"]["price"])

        # compute the lowest price among those below average
        lowest = sorted_res[0]["_chosen_fuel"]["price"]

        # build message lines for the top 3
        lines = []
        medals = ["🥇", "🥈", "🥉"]
        for i, station in enumerate(sorted_res[:3]):
            f0 = station["_chosen_fuel"]
            price = f0["price"]

            dir_url = format_directions_url(station['location']['lat'], station['location']['lng'])

            if not station.get("address"):
                station["address"] = await get_station_address(station["id"]) or t("no_address", lang)

            # Localized timestamp
            formatted_date = format_date(station.get("insertDate"), t=t, lang=lang)

            price_txt = format_price(price, price_unit)
            price_note = format_avg_comparison_text(price, avg, t=t, lang=lang)

            lines.append(
                f"{medals[i]} <b><a href=\"{dir_url}\">{station['brand']} • {station['name']}</a></b>\n"
                f"• <u>{t('address', lang)}</u>: {station['address']}\n"
                f"• <u>{t('price', lang)}</u>: <b>{price_txt}</b>, {price_note}\n"
                f"<i>[{t('last_update', lang)}: {formatted_date}]</i>"
            )

        header = (
            f"<b><u>{t(label_key, lang)}</u></b> 📍\n"
            f"{num_stations} {t('stations_analyzed', lang)}\n"
            f"{t('average_zone_price', lang)}: <b>{format_price(avg, price_unit)}</b>\n\n"
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
            round(lowest, 3),
        )


search_handler = ConversationHandler(
    entry_points=[CommandHandler("search", search_ep)],
    states={
        STEP_SEARCH_LOCATION: [
            MessageHandler(filters.LOCATION, search_receive_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, search_receive_text),
        ],
    },
    fallbacks=[],
    block=True,
    allow_reentry=True,
)
