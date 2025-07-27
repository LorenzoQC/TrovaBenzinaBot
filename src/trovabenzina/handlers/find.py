from urllib.parse import quote_plus

from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from trovabenzina.api.api import geocode, call_api, fetch_address
from trovabenzina.config import (
    FUEL_MAP,
    SERVICE_MAP,
    DEFAULT_RADIUS_NEAR,
    DEFAULT_RADIUS_FAR,
    DEFAULT_LANGUAGE,
)
from trovabenzina.db.crud import get_user, log_search
from trovabenzina.i18n import t
from trovabenzina.utils import (
    STEP_FIND_LOC,
    STEP_FIND_RADIUS,
    inline_kb,
)

__all__ = ["find_conv"]


# ── /find entry point ─────────────────────────────────────────────
async def find_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /find command: ask user for location or address."""
    uid = update.effective_user.id
    # get user language or fallback
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)

    # prompt for location or address text
    await update.message.reply_text(t("ask_location", lang))
    return STEP_FIND_LOC


async def _ask_radius(ctx_target, ctx, edit=False):
    """Send or edit a message asking for search radius."""
    uid = ctx_target.effective_user.id if hasattr(ctx_target, 'effective_user') else ctx_target
    _, _, lang = await get_user(uid)
    kb = inline_kb([(f"2 km", "rad_2"), ("7 km", "rad_7")])

    if edit:
        await ctx_target.edit_message_text(
            t("select_radius", lang),
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        chat_id = ctx_target.effective_chat.id if hasattr(ctx_target, 'effective_chat') else ctx_target
        await ctx.bot.send_message(
            chat_id,
            t("select_radius", lang),
            reply_markup=InlineKeyboardMarkup(kb)
        )
    return STEP_FIND_RADIUS


async def find_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive a location object from user."""
    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude
    return await _ask_radius(update, ctx, edit=False)


async def find_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receive an address text from user and geocode it."""
    uid = update.effective_user.id
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)
    address = update.message.text

    coords = await geocode(address)
    if not coords:
        await update.message.reply_text(t("invalid_address", lang))
        return STEP_FIND_LOC

    ctx.user_data["search_lat"], ctx.user_data["search_lng"] = coords
    return await _ask_radius(update, ctx, edit=False)


async def radius_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle user selection of search radius and perform search."""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    radius_key = query.data.split("_", 1)[1]
    if radius_key == "2":
        ctx.user_data["radius"] = DEFAULT_RADIUS_NEAR
    else:
        ctx.user_data["radius"] = DEFAULT_RADIUS_FAR

    # perform the search
    msg = await _process_search(query, ctx,
                                ctx.user_data["search_lat"], ctx.user_data["search_lng"]
    )
    return ConversationHandler.END


# ── Core search and message formatting ─────────────────────────────
async def _process_search(origin, ctx, lat: float, lng: float):
    """Fetch nearby stations, format results and log the search."""
    uid = origin.from_user.id if hasattr(origin, 'from_user') else origin
    fuel_code, service_code, lang = await get_user(uid)
    radius = ctx.user_data.get("radius", DEFAULT_RADIUS_NEAR)
    ft = f"{FUEL_MAP[fuel_code]}-{SERVICE_MAP[service_code]}"

    # call external API
    res = await call_api(lat, lng, radius, ft)
    results = res.get("results", []) if res else []
    if not results:
        return await origin.message.reply_text(t("no_stations", lang))

    # compute statistics
    fid = int(FUEL_MAP[fuel_code])
    prices = [f["price"] for r in results for f in r["fuels"] if f["fuelId"] == fid]
    avg = sum(prices) / len(prices)

    # sort and pick top 3
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
            f"{medals[i]} *{station['brand']} • {station['name']} • {station['address']}*\n"
            f"{price:.3f} €/L – {note} {t('compared_to_avg', lang, avg=avg)}\n"
            f"[{t('lets_go', lang)}]({link})"
        )

    # log analytics
    await log_search(uid, avg, min(prices))

    return await origin.message.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ── ConversationHandler definition ────────────────────────────────────
find_conv = ConversationHandler(
    entry_points=[CommandHandler(["find", "trova"], find_cmd)],
    states={
        STEP_FIND_LOC: [
            MessageHandler(filters.LOCATION, find_receive_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, find_receive_text),
        ],
        STEP_FIND_RADIUS: [CallbackQueryHandler(radius_selected, pattern="^rad_")],
    },
    fallbacks=[],
    block=True,
)
