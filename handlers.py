import logging

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from api import geocode, call_api, fetch_address
from config import (
    FUEL_MAP,
    SERVICE_MAP,
    DEFAULT_RADIUS_NEAR,
    DEFAULT_RADIUS_FAR,
    LANGUAGES,
    DEFAULT_LANGUAGE,
)
from db import (
    upsert_user,
    get_user,
    log_search,
    add_favorite,
    list_favorites,
    delete_favorite,
)
from translations import t

log = logging.getLogger(__name__)

# ---- STEP indices ----
STEP_LANG, STEP_FUEL, STEP_SERVICE = range(3)  # /start
STEP_FIND_LOC, STEP_FIND_RADIUS = range(3, 5)  # /find
STEP_FAV_ACTION, STEP_FAV_NAME, STEP_FAV_LOC, STEP_FAV_REMOVE = range(5, 9)


# -----------------------------------------------------------
#  /START
# -----------------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [[f"{code} - {name}" for code, name in LANGUAGES.items()]]
    await update.message.reply_text(
        t("ask_language_choice", DEFAULT_LANGUAGE),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data.clear()
    ctx.user_data["step"] = STEP_LANG
    return STEP_LANG


async def language_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.split(" - ")[0]
    if code not in LANGUAGES:
        return await update.message.reply_text(t("invalid_language", DEFAULT_LANGUAGE))
    ctx.user_data["lang"] = code
    kb = [[name for name in FUEL_MAP.keys()]]
    await update.message.reply_text(
        t("ask_fuel", code),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data["step"] = STEP_FUEL
    return STEP_FUEL


async def fuel_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data["lang"]
    fuel = update.message.text
    if fuel not in FUEL_MAP:
        return await update.message.reply_text(t("invalid_fuel", lang))
    ctx.user_data["fuel"] = fuel
    kb = [[name for name in SERVICE_MAP.keys()]]
    await update.message.reply_text(
        t("ask_service", lang),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data["step"] = STEP_SERVICE
    return STEP_SERVICE


async def service_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data["lang"]
    service = update.message.text
    if service not in SERVICE_MAP:
        return await update.message.reply_text(t("invalid_service", lang))
    ctx.user_data["service"] = service

    # Salva tutto e termina /start
    await upsert_user(
        update.effective_user.id,
        ctx.user_data["fuel"],
        ctx.user_data["service"],
        ctx.user_data["lang"],
    )
    await update.message.reply_text(t("profile_saved", lang))
    ctx.user_data.clear()
    return ConversationHandler.END


# -----------------------------------------------------------
#  /FIND
# -----------------------------------------------------------
async def find_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    fuel, service, lang = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    kb = [[KeyboardButton(t("send_location", lang), request_location=True)]]
    # aggiungi bottoni preferiti
    favs = await list_favorites(update.effective_user.id)
    kb += [[fav[0]] for fav in favs]  # un bottone per riga
    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data["step"] = STEP_FIND_LOC
    return STEP_FIND_LOC


async def find_receive_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    ctx.user_data["search_lat"] = loc.latitude
    ctx.user_data["search_lng"] = loc.longitude
    return await _ask_radius(update, ctx)


async def find_receive_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = (await get_user(uid))[2]
    text = update.message.text

    # se corrisponde a un preferito
    fav = next((f for f in await list_favorites(uid) if f[0] == text), None)
    if fav:
        ctx.user_data["search_lat"], ctx.user_data["search_lng"] = fav[1], fav[2]
        return await _ask_radius(update, ctx)

    # altrimenti prova geocode
    coords = await geocode(text)
    if not coords:
        return await update.message.reply_text(t("invalid_address", lang))
    ctx.user_data["search_lat"], ctx.user_data["search_lng"] = coords
    return await _ask_radius(update, ctx)


async def _ask_radius(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = (await get_user(update.effective_user.id))[2]
    kb = [["2 km", "7 km"]]
    await update.message.reply_text(
        t("select_radius", lang),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data["step"] = STEP_FIND_RADIUS
    return STEP_FIND_RADIUS


async def find_radius_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = (await get_user(update.effective_user.id))[2]
    text = update.message.text
    if text == "2 km":
        ctx.user_data["radius"] = DEFAULT_RADIUS_NEAR
    elif text == "7 km":
        ctx.user_data["radius"] = DEFAULT_RADIUS_FAR
    else:
        return await update.message.reply_text(t("invalid_radius", lang))

    # fai la ricerca vera e propria
    msg = await _process_search(
        update, ctx, ctx.user_data["search_lat"], ctx.user_data["search_lng"]
    )

    # aggiungi bottone "Salva tra i preferiti"
    name_cb = f"savefav:{ctx.user_data['search_lat']}:{ctx.user_data['search_lng']}"
    await msg.reply_text(
        "⭐",
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("⭐ Salva tra i preferiti", callback_data=name_cb)
        ),
    )
    ctx.user_data.clear()
    return ConversationHandler.END


# -----------------------------------------------------------
#  /FAVORITES
# -----------------------------------------------------------
async def favorites_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = (await get_user(update.effective_user.id))[2]
    favs = await list_favorites(update.effective_user.id)
    if not favs:
        txt = t("no_favorites", lang)
    else:
        lines = [
            f"{i + 1}) {name} • {await _reverse_geocode_or_blank(lat, lng)}"
            for i, (name, lat, lng) in enumerate(favs)
        ]
        txt = f"{t('favorites_title', lang)}\n" + "\n".join(lines)
    kb = [
        [InlineKeyboardButton(t("add_favorite_btn", lang), callback_data="fav_add")],
    ]
    if favs:
        kb.append([InlineKeyboardButton(t("edit_favorite_btn", lang), callback_data="fav_edit")])
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    ctx.user_data["step"] = STEP_FAV_ACTION
    return STEP_FAV_ACTION


async def favorites_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = (await get_user(uid))[2]

    if query.data == "fav_add":
        await query.edit_message_text(t("ask_fav_name", lang))
        ctx.user_data["step"] = STEP_FAV_NAME
        return STEP_FAV_NAME

    if query.data == "fav_edit":
        favs = await list_favorites(uid)
        if not favs:
            return await query.edit_message_text(t("no_favorites", lang))
        kb = [
            [InlineKeyboardButton(name, callback_data=f"favdel_{name}")] for name, _, _ in favs
        ]
        await query.edit_message_text(
            t("which_fav_remove", lang), reply_markup=InlineKeyboardMarkup(kb)
        )
        ctx.user_data["step"] = STEP_FAV_REMOVE
        return STEP_FAV_REMOVE

    if query.data.startswith("favdel_"):
        name = query.data.split("_", 1)[1]
        await delete_favorite(uid, name)
        await query.edit_message_text(t("fav_removed", lang))
        ctx.user_data.clear()
        return ConversationHandler.END

    if query.data.startswith("savefav:"):
        _, lat, lng = query.data.split(":")
        await add_favorite(uid, f"Pos {lat[:6]},{lng[:6]}", float(lat), float(lng))
        await query.edit_message_text(t("fav_saved", lang))
        return ConversationHandler.END


async def fav_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["fav_name"] = update.message.text
    lang = (await get_user(update.effective_user.id))[2]
    await update.message.reply_text(t("ask_fav_location", lang))
    ctx.user_data["step"] = STEP_FAV_LOC
    return STEP_FAV_LOC


async def fav_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = (await get_user(uid))[2]
    name = ctx.user_data["fav_name"]
    if update.message.location:
        lat, lng = update.message.location.latitude, update.message.location.longitude
    else:
        coords = await geocode(update.message.text)
        if not coords:
            return await update.message.reply_text(t("invalid_address", lang))
        lat, lng = coords
    await add_favorite(uid, name, lat, lng)
    await update.message.reply_text(t("fav_saved", lang))
    ctx.user_data.clear()
    return ConversationHandler.END


# -----------------------------------------------------------
#  /PROFILE
# -----------------------------------------------------------
async def profile_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    fuel, service, lang = (await get_user(update.effective_user.id)) or (None, None, DEFAULT_LANGUAGE)
    kb = [
        [InlineKeyboardButton(t("edit_language", lang), callback_data="edit_language")],
        [InlineKeyboardButton(t("edit_fuel", lang), callback_data="edit_fuel")],
        [InlineKeyboardButton(t("edit_service", lang), callback_data="edit_service")],
        [InlineKeyboardButton(t("edit_favorite_btn", lang), callback_data="fav_edit")],
    ]
    text = t("profile_info", lang).format(
        fuel=fuel, service=service, language=LANGUAGES[lang]
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


profile_callback = favorites_callback  # riusa la stessa logica


# -----------------------------------------------------------
#  /HELP
# -----------------------------------------------------------
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = (await get_user(update.effective_user.id))[2] if await get_user(
        update.effective_user.id) else DEFAULT_LANGUAGE
    await update.message.reply_text(t("help", lang))


# -----------------------------------------------------------
#  UTILITIES
# -----------------------------------------------------------
async def _reverse_geocode_or_blank(lat, lng):
    """Potresti usare Nominatim o lasciare vuoto per ora"""
    return ""


async def _process_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE, lat: float, lng: float):
    uid = update.effective_user.id
    fuel, service, lang = await get_user(uid)
    radius = ctx.user_data.get("radius", DEFAULT_RADIUS_NEAR)
    ft = f"{FUEL_MAP[fuel]}-{SERVICE_MAP[service]}"

    res = await call_api(lat, lng, radius, ft)
    results = res.get("results", []) if res else []
    if not results:
        return await update.message.reply_text(t("no_stations", lang))

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
        link = f"https://www.google.com/maps/dir/?api=1&destination={dest}"

        if price < avg:
            note = t("note_cheaper", lang).format(pct=pct)
        elif price > avg:
            note = t("note_more_expensive", lang).format(pct=pct)
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
    msg = await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
    return msg
