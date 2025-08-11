from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from ..api import get_station_address, search_stations, geocode_address
from ..config import GEOCODE_HARD_CAP
from ..db import (
    get_user,
    save_search,
    get_geocache,
    save_geocache,
    count_geocoding_month_calls,
    get_uom_by_code,
    get_user_language_code_by_tg_id,
)
from ..i18n import t
from ..utils import (
    STEP_SEARCH_LOCATION,
    format_price_unit,
    format_price,
    format_avg_comparison_text,
    format_date,
    format_directions_url,
    format_radius,
)
from ..utils.telegram import inline_kb

__all__ = ["search_handler", "radius_callback_handler"]

# Callback data identifiers
_CB_NARROW = "search:r=2.5"  # 2.5 km
_CB_WIDEN = "search:r=7.5"  # 7.5 km

# Initial radius in km
_INITIAL_RADIUS = 5.0


async def search_ep(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /search command: ask user for address or location (no GPS keyboard)."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    return STEP_SEARCH_LOCATION


async def search_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive a location and perform the initial 5 km search."""
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    proc_msg = await update.message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc_msg.message_id

    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude

    await run_search(update, ctx, radius_km=_INITIAL_RADIUS, show_radius_cta=True)
    return ConversationHandler.END


async def search_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive an address, geocode (with cache) and perform the initial 5 km search."""
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

    await run_search(update, ctx, radius_km=_INITIAL_RADIUS, show_radius_cta=True)
    return ConversationHandler.END


async def run_search(
        origin: Update,
        ctx: ContextTypes.DEFAULT_TYPE,
        *,
        radius_km: float,
        show_radius_cta: bool = False,
):
    """Perform a single-radius search, filter by fuel, send top 3 below-average, and log."""
    msg_obj = getattr(origin, "message", None)
    if msg_obj is None and getattr(origin, "callback_query", None):
        msg_obj = origin.callback_query.message

    uid = origin.effective_user.id
    fuel_code, lang = await get_user(uid)
    lat = ctx.user_data.get("search_lat")
    lng = ctx.user_data.get("search_lng")

    if lat is None or lng is None:
        await msg_obj.reply_text(t("search_session_expired", lang))
        return

    uom = (await get_uom_by_code(fuel_code)) or "L"
    price_unit = format_price_unit(uom=uom, t=t, lang=lang)

    fid = int(fuel_code)
    ft = f"{fuel_code}-x"

    res = await search_stations(lat, lng, radius_km, ft)
    stations = res.get("results", []) if res else []
    num_stations = len(stations)

    # Delete the “processing” message if present
    chat_id = msg_obj.chat.id
    proc_id = ctx.user_data.pop("processing_msg_id", None)
    if proc_id:
        try:
            await ctx.bot.delete_message(chat_id, proc_id)
        except Exception:
            pass

    # Filter by requested fuelId
    filtered = []
    for st in stations:
        fuels = [f for f in st.get("fuels", []) if f.get("fuelId") == fid]
        if fuels:
            st["_filtered_fuels"] = fuels
            filtered.append(st)

    if not filtered:
        await msg_obj.reply_text(
            f"<u>{t('area_label', lang, radius=format_radius(radius_km))}</u> 📍\n\n{t('no_stations', lang)}",
            parse_mode=ParseMode.HTML,
        )
        await save_search(uid, fuel_code, radius_km, num_stations, None, None)
        return

    # Prefer self-service on price ties
    all_fuels = [f for st in filtered for f in st["_filtered_fuels"]]
    min_fuel = min(all_fuels, key=lambda f: (f["price"], not f.get("isSelf")))
    target_is_self = min_fuel.get("isSelf")

    for st in filtered:
        st["_chosen_fuel"] = min(
            st["_filtered_fuels"], key=lambda f: (f["price"], not f.get("isSelf"))
        )
    filtered = [st for st in filtered if st["_chosen_fuel"].get("isSelf") == target_is_self]
    num_stations = len(filtered)

    if not filtered:
        await msg_obj.reply_text(
            f"<u>{t('area_label', lang, radius=format_radius(radius_km))}</u> 📍\n\n{t('no_stations', lang)}",
            parse_mode=ParseMode.HTML,
        )
        await save_search(uid, fuel_code, radius_km, num_stations, None, None)
        return

    avg = sum(st["_chosen_fuel"]["price"] for st in filtered) / len(filtered)
    below_avg = [st for st in filtered if st["_chosen_fuel"]["price"] <= avg]

    if not below_avg:
        await msg_obj.reply_text(
            f"<u>{t('area_label', lang, radius=format_radius(radius_km))}</u> 📍\n\n{t('no_stations', lang)}",
            parse_mode=ParseMode.HTML,
        )
        await save_search(uid, fuel_code, radius_km, num_stations, None, None)
        return

    sorted_res = sorted(below_avg, key=lambda r: r["_chosen_fuel"]["price"])
    lowest = sorted_res[0]["_chosen_fuel"]["price"]

    # Build message
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, station in enumerate(sorted_res[:3]):
        f0 = station["_chosen_fuel"]
        price = f0["price"]
        dir_url = format_directions_url(
            station["location"]["lat"], station["location"]["lng"]
        )

        if not station.get("address"):
            station["address"] = await get_station_address(station["id"]) or t(
                "no_address", lang
            )

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
        f"<b><u>{t('area_label', lang, radius=format_radius(radius_km))}</u></b> 📍\n"
        f"{num_stations} {t('stations_analyzed', lang)}\n"
        f"{t('average_zone_price', lang)}: <b>{format_price(avg, price_unit)}</b>\n\n"
    )

    # Inline radius controls only on the initial 5 km message (one per row)
    reply_markup = None
    if show_radius_cta:
        items = [
            (t("btn_narrow", lang, radius="2.5"), _CB_NARROW),
            (t("btn_widen", lang, radius="7.5"), _CB_WIDEN),
        ]
        reply_markup = InlineKeyboardMarkup(inline_kb(items, per_row=1))

    await msg_obj.reply_text(
        header + "\n\n".join(lines),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=reply_markup,
    )

    await save_search(
        uid,
        fuel_code,
        radius_km,
        num_stations,
        round(avg, 3),
        round(lowest, 3),
    )


# ---------- Callback handler for radius refinement ----------

async def radius_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle inline buttons to refine radius to 2.5 km or 7.5 km."""
    query = update.callback_query
    lang = await get_user_language_code_by_tg_id(update.effective_user.id)
    await query.answer()

    data = (query.data or "").strip()

    # Remove the clicked button from the original 5 km message before results appear
    try:
        if data == _CB_NARROW:
            items = [(t("btn_widen", lang, radius="7.5"), _CB_WIDEN)]
        elif data == _CB_WIDEN:
            items = [(t("btn_narrow", lang, radius="2.5"), _CB_NARROW)]
        else:
            items = []

        new_kb = InlineKeyboardMarkup(inline_kb(items, per_row=1)) if items else None
        await query.edit_message_reply_markup(reply_markup=new_kb)
    except Exception:
        pass  # ignore race conditions

    # Show 'processing' message (auto-removed by run_search)
    proc = await query.message.reply_text(
        t("processing_search", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data["processing_msg_id"] = proc.message_id

    if data == _CB_NARROW:
        await run_search(update, ctx, radius_km=2.5, show_radius_cta=False)
    elif data == _CB_WIDEN:
        await run_search(update, ctx, radius_km=7.5, show_radius_cta=False)


# Exported handlers
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

radius_callback_handler = CallbackQueryHandler(
    radius_callback, pattern=r"^search:r=(?:2\.5|7\.5)$"
)
