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
    LANGUAGES,
    DEFAULT_LANGUAGE,
)
from db import (
    upsert_user,
    get_user,
    log_search,
    add_favorite,
    list_favorites,
)
from translations import t

log = logging.getLogger(__name__)

# Stati di conversazione
STEP_LANG, STEP_FUEL, STEP_SERVICE, STEP_RADIUS, STEP_FAV_NAME, STEP_FAV_LOC, STEP_LOC = range(7)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/start → scegli lingua"""
    kb = [[f"{code} - {name}" for code, name in LANGUAGES.items()]]
    await update.message.reply_text(
        t("ask_language_choice", DEFAULT_LANGUAGE),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data["step"] = STEP_LANG
    return STEP_LANG


async def language_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Gestisci scelta lingua → chiedi carburante"""
    text = update.message.text.split(" - ")[0]
    if text not in LANGUAGES:
        return await update.message.reply_text(t("invalid_language", DEFAULT_LANGUAGE))
    # Salva lingua (mantieni fuel/service se già impostati)
    prev = await get_user(update.effective_user.id) or (None, None, DEFAULT_LANGUAGE)
    fuel, service, _ = prev
    await upsert_user(update.effective_user.id,
                      fuel or list(FUEL_MAP.keys())[0],
                      service or list(SERVICE_MAP.keys())[0],
                      text)
    ctx.user_data["lang"] = text

    # Chiedi carburante
    kb = [[name for name in FUEL_MAP.keys()]]
    await update.message.reply_text(
        t("ask_fuel", text),
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    ctx.user_data["step"] = STEP_FUEL
    return STEP_FUEL

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Fuel, service e nome preferito"""
    step = ctx.user_data.get("step")
    text = update.message.text
    lang = ctx.user_data.get("lang") or (await get_user(update.effective_user.id))[2]

    if step == STEP_FUEL:
        if text in FUEL_MAP:
            ctx.user_data["fuel"] = text
            kb = [[name for name in SERVICE_MAP.keys()]]
            await update.message.reply_text(
                t("ask_service", lang),
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
            ctx.user_data["step"] = STEP_SERVICE
            return STEP_SERVICE
        else:
            return await update.message.reply_text(t("invalid_fuel", lang))

    if step == STEP_SERVICE:
        if text in SERVICE_MAP:
            ctx.user_data["service"] = text
            kb = [["Cerca entro 2km", "Cerca entro 7km"]]
            await update.message.reply_text(
                t("select_radius", lang) if "select_radius" in t.__code__.co_consts else "Seleziona raggio di ricerca:",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
            ctx.user_data["step"] = STEP_RADIUS
            return STEP_RADIUS
        else:
            return await update.message.reply_text(t("invalid_service", lang))

    if step == STEP_FAV_NAME:
        ctx.user_data["fav_name"] = text
        await update.message.reply_text(t("ask_fav_location", lang))
        ctx.user_data["step"] = STEP_FAV_LOC
        return STEP_FAV_LOC

    # fallback generale
    return await update.message.reply_text(t("use_commands", lang))

async def profilo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/profilo → mostra profilo con bottoni inline"""
    fuel, service, lang = (await get_user(update.effective_user.id)) or (None, None, DEFAULT_LANGUAGE)
    kb = [
        [InlineKeyboardButton(t("edit_fuel", lang), callback_data="edit_fuel")],
        [InlineKeyboardButton(t("edit_service", lang), callback_data="edit_service")],
        [InlineKeyboardButton(t("edit_language", lang), callback_data="edit_language")],
    ]
    text = t("profile_info", lang).format(
        fuel=fuel, service=service, language=LANGUAGES[lang]
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


async def profile_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Inline callback per modifiche profilo"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    fuel, service, lang = (await get_user(uid)) or (None, None, DEFAULT_LANGUAGE)

    if query.data == "edit_fuel":
        kb = [[name for name in FUEL_MAP.keys()]]
        await query.edit_message_text(
            t("ask_fuel", lang),
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        ctx.user_data["step"] = STEP_FUEL
        return STEP_FUEL

    if query.data == "edit_service":
        kb = [[name for name in SERVICE_MAP.keys()]]
        await query.edit_message_text(
            t("ask_service", lang),
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        ctx.user_data["step"] = STEP_SERVICE
        return STEP_SERVICE

    if query.data == "edit_language":
        kb = [[f"{code} - {name}" for code, name in LANGUAGES.items()]]
        await query.edit_message_text(
            t("ask_language_choice", lang),
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        ctx.user_data["step"] = STEP_LANG
        return STEP_LANG

async def trova(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/trova → scegli raggio o mostra preferiti"""
    fuel, service, lang = (await get_user(update.effective_user.id)) or (None, None, DEFAULT_LANGUAGE)
    kb = [
        [KeyboardButton(t("send_location", lang), request_location=True)],
        [InlineKeyboardButton(t("favorites", lang), callback_data="show_favorites")],
    ]
    await update.message.reply_text(
        t("ask_location", lang),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    ctx.user_data["step"] = STEP_LOC
    return STEP_LOC

async def handle_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Process GPS per ricerca o salvataggio preferito."""
    loc = update.message.location
    return await _process_search(update, ctx, loc.latitude, loc.longitude)

async def handle_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Process testo geocoding per ricerca o salvataggio preferito."""
    coords = await geocode(update.message.text)
    lang = (await get_user(update.effective_user.id))[2]
    if not coords:
        return await update.message.reply_text(t("invalid_address", lang))
    return await _process_search(update, ctx, *coords)


async def show_favorites(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Inline callback: mostra lista preferiti."""
    uid = update.callback_query.from_user.id
    lang = (await get_user(uid))[2]
    favs = await list_favorites(uid)
    if not favs:
        return await update.callback_query.message.reply_text(t("no_favorites", lang))
    buttons = [[InlineKeyboardButton(n, callback_data=f"fav_{n}")] for n, _, _ in favs]
    await update.callback_query.message.reply_text(
        t("choose_favorite", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def favorite_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Inline callback: utente ha scelto uno dei preferiti."""
    uid = update.callback_query.from_user.id
    _, lat, lng = next(f for f in await list_favorites(uid) if f[0] == update.callback_query.data.split("_", 1)[1])
    return await _process_search(update, ctx, lat, lng)


async def addfav(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/addfav → chiedi nome del preferito."""
    lang = (await get_user(update.effective_user.id))[2]
    await update.message.reply_text(t("ask_fav_name", lang))
    ctx.user_data["step"] = STEP_FAV_NAME
    return STEP_FAV_NAME


async def handle_fav_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Riceve il nome e chiede la posizione."""
    lang = (await get_user(update.effective_user.id))[2]
    ctx.user_data["fav_name"] = update.message.text
    await update.message.reply_text(t("ask_fav_location", lang))
    ctx.user_data["step"] = STEP_FAV_LOC
    return STEP_FAV_LOC


async def handle_fav_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Salva il preferito dopo invio posizione o indirizzo."""
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


async def _process_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE, lat: float, lng: float):
    """Logica unificata per ricerca top 3 distributori."""
    uid = update.effective_user.id
    fuel, service, lang = await get_user(uid)
    radius = ctx.user_data.get("radius", DEFAULT_RADIUS_NEAR) if "radius" in ctx.user_data else DEFAULT_RADIUS_NEAR
    ft = f"{FUEL_MAP[fuel]}-{SERVICE_MAP[service]}"

    res = await call_api(lat, lng, radius, ft)
    results = res.get("results", []) if res else []
    if not results:
        return await update.message.reply_text(t("no_stations", lang))

    # Calcola media
    fid = int(FUEL_MAP[fuel])
    prices = [f["price"] for r in results for f in r["fuels"] if f["fuelId"] == fid]
    avg = sum(prices) / len(prices)

    # Ordina e prendi primi 3
    sorted_res = sorted(results, key=lambda r: next(f["price"] for f in r["fuels"] if f["fuelId"] == fid))
    medals = ["🥇", "🥈", "🥉"]
    Lines = []
    for i, station in enumerate(sorted_res[:3]):
        price = next(f["price"] for f in station["fuels"] if f["fuelId"] == fid)
        pct = int(round((avg - price) / avg * 100))
        if price < avg:
            note = t("note_cheaper", lang).format(pct=pct)
        elif price > avg:
            note = t("note_more_expensive", lang).format(pct=pct)
        else:
            note = t("note_equal", lang)
        if not station.get("address"):
            station["address"] = await fetch_address(station["id"]) or t("no_address", lang)
        Lines.append(
            f"{medals[i]} *Distributore*: {station['brand']} • {station['name']} • {station['address']}\n"
            f"*Costo {fuel}*: {price:.3f} € al L, {note} {t('compared_to_avg', lang).format(avg=avg):s}\n"
            f"*Andiamo!*"
        )

    await log_search(uid, avg, prices[0])
    await update.message.reply_text(
        "\n\n".join(Lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
