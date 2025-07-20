import logging
from urllib.parse import quote_plus

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from trovabenzina.config import (
    FUEL_MAP,
    SERVICE_MAP,
    DEFAULT_RADIUS_NEAR,
    DEFAULT_RADIUS_FAR,
    LANGUAGES,
    DEFAULT_LANGUAGE,
)
from trovabenzina.core.api import geocode, call_api, fetch_address
from trovabenzina.core.db import (
    upsert_user,
    get_user,
    log_search,
    add_favorite,
    list_favorites,
    delete_favorite,
)
from trovabenzina.i18n import t

log = logging.getLogger(__name__)

# conversation states
STEP_LANG, STEP_FUEL, STEP_SERVICE = range(3)
STEP_FIND_LOC, STEP_FIND_RADIUS = range(3, 5)
STEP_FAV_ACTION, STEP_FAV_NAME, STEP_FAV_LOC, STEP_FAV_REMOVE = range(5, 9)


def _inline_kb(items: list[tuple[str, str]], per_row: int = 2) -> list[list[InlineKeyboardButton]]:
    """Return an InlineKeyboardMarkup layout with up to `per_row` buttons each row."""
    return [
        [InlineKeyboardButton(text, callback_data=data) for text, data in items[i: i + per_row]]
        for i in range(0, len(items), per_row)
    ]


async def _reverse_geocode_or_blank(lat: float, lng: float) -> str:
    return ""  # optional reverse-geocode


# ── /start ──────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = _inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await update.message.reply_text(
        t("ask_language_choice", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    ctx.user_data.clear()
    return STEP_LANG


async def language_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    code = query.data.split("_", 1)[1]
    ctx.user_data["lang"] = code

    kb = _inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_lang")])
    await query.edit_message_text(t("ask_fuel", code), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_FUEL


async def fuel_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fuel = query.data.split("_", 1)[1]
    lang = ctx.user_data["lang"]

    if fuel not in FUEL_MAP:
        return await query.answer(t("invalid_fuel", lang), show_alert=True)

    ctx.user_data["fuel"] = fuel
    kb = _inline_kb([(s, f"serv_{s}") for s in SERVICE_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_fuel")])
    await query.edit_message_text(t("ask_service", lang), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_SERVICE


async def service_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data.split("_", 1)[1]
    lang = ctx.user_data["lang"]

    if service not in SERVICE_MAP:
        return await query.answer(t("invalid_service", lang), show_alert=True)

    ctx.user_data["service"] = service
    await upsert_user(
        query.from_user.id,
        ctx.user_data["fuel"],
        ctx.user_data["service"],
        lang,
    )
    await query.edit_message_text(t("profile_saved", lang))
    ctx.user_data.clear()
    return ConversationHandler.END


async def back_to_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = _inline_kb([(name, f"lang_{code}") for code, name in LANGUAGES.items()])
    await query.edit_message_text(
        t("ask_language_choice", DEFAULT_LANGUAGE),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_LANG


async def back_to_fuel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = ctx.user_data.get("lang", DEFAULT_LANGUAGE)
    kb = _inline_kb([(fuel, f"fuel_{fuel}") for fuel in FUEL_MAP])
    kb.append([InlineKeyboardButton("↩", callback_data="back_lang")])
    await query.edit_message_text(
        t("ask_fuel", lang),
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return STEP_FUEL



# ── /find ───────────────────────────────────────────────────────────────────
async def find_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    _, _, lang = await get_user(uid) or (None, None, DEFAULT_LANGUAGE)

    favs = await list_favorites(uid)
    kb = _inline_kb([(name, f"favloc_{i}") for i, (name, _, _) in enumerate(favs)])
    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=InlineKeyboardMarkup(kb) if kb else None,
    )
    ctx.user_data["favs_cached"] = favs
    return STEP_FIND_LOC


async def find_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude
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


async def _ask_radius(chat_id: int, ctx: ContextTypes.DEFAULT_TYPE, edit=None):
    _, _, lang = await get_user(chat_id) or (None, None, DEFAULT_LANGUAGE)
    kb = _inline_kb([("2 km", "rad_2"), ("7 km", "rad_7")])
    if edit:
        await edit.edit_message_text(t("select_radius", lang), reply_markup=InlineKeyboardMarkup(kb))
    else:
        await ctx.bot.send_message(chat_id, t("select_radius", lang), reply_markup=InlineKeyboardMarkup(kb))
    return STEP_FIND_RADIUS


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


# ── /favorites ───────────────────────────────────────────────────────────────
async def favorites_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _, _, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    favs = await list_favorites(update.effective_user.id)
    if not favs:
        txt = t("no_favorites", lang)
    else:
        lines = [
            f"{i + 1}) {name} • {await _reverse_geocode_or_blank(lat, lng)}"
            for i, (name, lat, lng) in enumerate(favs)
        ]
        txt = f"{t('favorites_title', lang)}\n" + "\n".join(lines)

    kb = _inline_kb([(t("add_favorite_btn", lang), "fav_add")], per_row=2)
    if favs:
        kb += _inline_kb([(t("edit_favorite_btn", lang), "fav_edit")], per_row=2)
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    return STEP_FAV_ACTION


async def favorites_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    _, _, lang = await get_user(uid)

    if query.data == "fav_add":
        await query.edit_message_text(t("ask_fav_name", lang))
        return STEP_FAV_NAME

    if query.data == "fav_edit":
        favs = await list_favorites(uid)
        if not favs:
            return await query.edit_message_text(t("no_favorites", lang))
        kb = _inline_kb([(name, f"favdel_{name}") for name, _, _ in favs])
        await query.edit_message_text(t("which_fav_remove", lang), reply_markup=InlineKeyboardMarkup(kb))
        return STEP_FAV_REMOVE

    if query.data.startswith("favdel_"):
        name = query.data.split("_", 1)[1]
        await delete_favorite(uid, name)
        await query.edit_message_text(t("fav_removed", lang))
        return ConversationHandler.END

    if query.data.startswith("savefav:"):
        _, lat, lng = query.data.split(":")
        await add_favorite(uid, f"Pos {lat[:6]},{lng[:6]}", float(lat), float(lng))
        await query.edit_message_text(t("fav_saved", lang))
        return ConversationHandler.END


async def fav_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["fav_name"] = update.message.text
    _, _, lang = await get_user(update.effective_user.id)
    await update.message.reply_text(t("ask_fav_location", lang))
    return STEP_FAV_LOC


async def fav_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    _, _, lang = await get_user(uid)
    name = ctx.user_data["fav_name"]

    if update.message.location:
        lat, lng = update.message.location.latitude, update.message.location.longitude
    else:
        coords = await geocode(update.message.text)
        if not coords:
            await update.message.reply_text(t("invalid_address", lang))
            return STEP_FAV_LOC
        lat, lng = coords

    await add_favorite(uid, name, lat, lng)
    await update.message.reply_text(t("fav_saved", lang))
    ctx.user_data.clear()
    return ConversationHandler.END


# ── /profile ─────────────────────────────────────────────────────────────────
async def profile_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    fuel, service, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    kb = _inline_kb(
        [
            (t("edit_language", lang), "edit_language"),
            (t("edit_fuel", lang), "edit_fuel"),
            (t("edit_service", lang), "edit_service"),
            (t("edit_favorite_btn", lang), "fav_edit"),
        ]
    )
    text = t("profile_info", lang).format(fuel=fuel, service=service, language=LANGUAGES[lang])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


profile_callback = favorites_callback  # reuse handlers


# ── /help ────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _, _, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    await update.message.reply_text(t("help", lang))


# ── core search ──────────────────────────────────────────────────────────────
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
