from urllib.parse import quote_plus

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from trovabenzina.config import (
    FUEL_MAP,
    SERVICE_MAP,
    DEFAULT_RADIUS_NEAR,
    DEFAULT_RADIUS_FAR,
    DEFAULT_LANGUAGE,
)
from trovabenzina.core.api import geocode, call_api, fetch_address
from trovabenzina.core.db import get_user, log_search, list_favorites
from trovabenzina.i18n import t
from trovabenzina.utils import (
    STEP_FIND_LOC,
    STEP_FIND_RADIUS,
    inline_kb,
)

__all__ = ["find_conv"]


# ── entry /find ───────────────────────────────────────────────────────────
async def find_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)

    favs = await list_favorites(uid)
    kb = inline_kb([(name, f"favloc_{i}") for i, (name, _, _) in enumerate(favs)])
    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=InlineKeyboardMarkup(kb) if kb else None,
    )
    ctx.user_data["favs_cached"] = favs
    return STEP_FIND_LOC


async def _ask_radius(chat_id: int, ctx, edit=None):
    _, _, lang = await get_user(chat_id) or (None, None, DEFAULT_LANGUAGE)
    kb = inline_kb([("2 km", "rad_2"), ("7 km", "rad_7")])
    if edit:
        await edit.edit_message_text(t("select_radius", lang), reply_markup=InlineKeyboardMarkup(kb))
    else:
        await ctx.bot.send_message(chat_id, t("select_radius", lang), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_FIND_RADIUS


async def find_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    ctx.user_data["search_lat"], ctx.user_data["search_lng"] = loc.latitude, loc.longitude
    return await _ask_radius(update.effective_chat.id, ctx)


async def find_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)
    text = update.message.text

    fav = next((f for f in ctx.user_data.get("favs_cached", []) if f[0] == text), None)
    if fav:
        ctx.user_data["search_lat"], ctx.user_data["search_lng"] = fav[1], fav[2]
        return await _ask_radius(update.effective_chat.id, ctx)

    coords = await geocode(text)
    if not coords:
        await update.message.reply_text(t("invalid_address", lang))
        return STEP_FIND_LOC

    ctx.user_data["search_lat"], ctx.user_data["search_lng"] = coords
    return await _ask_radius(update.effective_chat.id, ctx)


async def favloc_clicked(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_", 1)[1])
    _, lat, lng = ctx.user_data["favs_cached"][idx]
    ctx.user_data["search_lat"], ctx.user_data["search_lng"] = lat, lng
    return await _ask_radius(query.message.chat_id, ctx, edit=query)


async def radius_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    radius_id = query.data.split("_", 1)[1]
    _, _, lang = await get_user(query.from_user.id)

    if radius_id == "2":
        ctx.user_data["radius"] = DEFAULT_RADIUS_NEAR
    elif radius_id == "7":
        ctx.user_data["radius"] = DEFAULT_RADIUS_FAR
    else:
        return await query.answer(t("invalid_radius", lang), show_alert=True)

    msg = await _process_search(query, ctx, ctx.user_data["search_lat"], ctx.user_data["search_lng"])

    cb = f"savefav:{ctx.user_data['search_lat']}:{ctx.user_data['search_lng']}"
    await msg.reply_text(
        "⭐",
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("⭐ Save as favourite", callback_data=cb)
        ),
    )
    ctx.user_data.clear()
    return ConversationHandler.END


# ── search core ───────────────────────────────────────────────────────────
async def _process_search(origin, ctx, lat: float, lng: float):
    if hasattr(origin, "effective_user"):
        uid = origin.effective_user.id
        msg_target = origin.message
    else:
        uid = origin.from_user.id
        msg_target = origin.message

    fuel, service, lang = await get_user(uid)
    radius = ctx.user_data.get("radius", DEFAULT_RADIUS_NEAR)
    ft = f"{FUEL_MAP[fuel]}-{SERVICE_MAP[service]}"

    res = await call_api(lat, lng, radius, ft)
    results = res.get("results", []) if res else []
    if not results:
        return await msg_target.reply_text(t("no_stations", lang))

    fid = int(FUEL_MAP[fuel])
    prices = [f["price"] for r in results for f in r["fuels"] if f["fuelId"] == fid]
    avg = sum(prices) / len(prices)

    sorted_res = sorted(results, key=lambda r: next(f["price"] for f in r["fuels"] if f["fuelId"] == fid))
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, station in enumerate(sorted_res[:3]):
        price = next(f["price"] for f in station["fuels"] if f["fuelId"] == fid)
        pct = int(round((avg - price) / avg * 100))
        dest = f"{station['location']['lat']},{station['location']['lng']}"
        link = f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(dest)}"

        if price < avg:
            note = t("note_cheaper", lang).format(pct=pct)
        elif price > avg:
            note = f"⚠️ {t('note_more_expensive', lang).format(pct=abs(pct))}"
        else:
            note = t("note_equal", lang)

        if not station.get("address"):
            station["address"] = await fetch_address(station["id"]) or t("no_address", lang)

        lines.append(
            f"{medals[i]} *{station['brand']} • {station['name']} • {station['address']}*\n"
            f"{price:.3f} €/L – {note} {t('compared_to_avg', lang).format(avg=avg)}\n"
            f"[{t('lets_go', lang)}]({link})"
        )

    await log_search(uid, avg, prices[0])
    return await msg_target.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ── ConversationHandler object ───────────────────────────────────────────
find_conv = ConversationHandler(
    entry_points=[("command", "find", find_cmd)],
    states={
        STEP_FIND_LOC: [
            ("message_location", find_receive_location),
            ("message_text", find_receive_text),
            ("callback", favloc_clicked),
        ],
        STEP_FIND_RADIUS: [("callback", radius_selected)],
    },
    fallbacks=[],
)
