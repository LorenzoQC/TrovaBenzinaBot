import asyncio
import datetime as dt
import logging
import os

import aiohttp
import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, ConversationHandler, filters
)

DB = os.getenv("DB_PATH", "/data/data.db")
GEOCODE_HARD_CAP = 10_000
ENABLE_DONATION = os.getenv("ENABLE_DONATION", "true").lower() == "true"

FUEL_MAP = {"Benzina": "1", "Gasolio": "2", "Metano": "3", "GPL": "4", "L-GNC": "323", "GNL": "324"}
SERVICE_MAP = {"Self-service": "1", "Servito": "0", "Indifferente": "x"}
LOC_STATE = 1

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("benzina")

# ── DB helpers ────────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,fuel TEXT,service TEXT);
        CREATE TABLE IF NOT EXISTS searches(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,ts DATETIME,price_avg REAL,price_min REAL);
        CREATE TABLE IF NOT EXISTS geocache(query TEXT PRIMARY KEY,lat REAL,lng REAL,ts DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS geostats(month TEXT PRIMARY KEY,cnt INTEGER);
        """);
        await db.commit()


async def upsert_user(uid: int, fuel: str, service: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO users(user_id,fuel,service)VALUES(?,?,?) "
            "ON CONFLICT(user_id)DO UPDATE SET fuel=excluded.fuel,service=excluded.service",
            (uid, fuel, service));
        await db.commit()


async def get_user(uid: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT fuel,service FROM users WHERE user_id=?", (uid,));
        return await cur.fetchone()


async def log_search(uid: int, avg: float, minimum: float):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO searches(user_id,ts,price_avg,price_min)VALUES(?,?,?,?)",
                         (uid, dt.datetime.now(), avg, minimum));
        await db.commit()


# ── Geocoding ─────────────────────────────────────────────────────────────
async def geocode(addr: str):
    async with aiosqlite.connect(DB) as db:
        row = await (await db.execute("SELECT lat,lng FROM geocache WHERE query=?", (addr,))).fetchone()
        if row: return row
        month = dt.date.today().strftime("%Y-%m")
        cnt_row = await (await db.execute("SELECT cnt FROM geostats WHERE month=?", (month,))).fetchone()
        if cnt_row and cnt_row[0] >= GEOCODE_HARD_CAP: return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": addr, "components": "country:IT", "language": "it", "key": os.getenv("GOOGLE_API_KEY")}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params, timeout=10) as r:
            if r.status != 200: return None
            data = await r.json()
    res = data.get("results", [])
    if not res: return None
    best = next((x for x in res if not x.get("partial_match")), res[0])
    comps = {c["types"][0]: c for c in best.get("address_components", [])}
    if not {"street_number", "locality"} <= comps.keys() or best["geometry"]["location_type"] != "ROOFTOP":
        return None
    latlng = best["geometry"]["location"]
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR REPLACE INTO geocache(query,lat,lng)VALUES(?,?,?)",
                         (addr, latlng["lat"], latlng["lng"]))
        await db.execute("INSERT INTO geostats(month,cnt)VALUES(?,1) ON CONFLICT(month)DO UPDATE SET cnt=cnt+1",
                         (month,))
        await db.commit()
    return latlng["lat"], latlng["lng"]


# ── detail address ────────────────────────────────────────────────────────
async def fetch_address(station_id: int):
    url = f"https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{station_id}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status != 200:
                    return None
                data = await r.json(content_type=None)
                if isinstance(data, dict):
                    return data.get("address")
    except Exception as e:
        log.warning("detail API id=%s err=%s", station_id, e)
    return None


# ── Mise API ──────────────────────────────────────────────────────────────
async def call_api(lat: float, lng: float, radius: float, fuel_type: str):
    url = "https://carburanti.mise.gov.it/ospzApi/search/zone"
    payload = {"points": [{"lat": lat, "lng": lng}], "radius": radius, "fuelType": fuel_type, "priceOrder": "asc"}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, timeout=10) as r:
            return await r.json() if r.status == 200 else None


def analyse(res, fid: int):
    prices = [f["price"] for r in res for f in r["fuels"] if f["fuelId"] == fid]
    avg = sum(prices) / len(prices)
    st = res[0];
    st_price = next(f["price"] for f in st["fuels"] if f["fuelId"] == fid)
    return (st, st_price), avg


def fmt(st, p, avg, fuel):
    perc = int(round((avg - p) / avg * 100))
    maps = f"https://www.google.com/maps/dir/?api=1&destination={st['location']['lat']},{st['location']['lng']}"
    saving_line = (f"<b>Risparmio:</b> {perc}% rispetto alla media ({avg:.3f} € al L)"
                   if perc else f"<b>Risparmio:</b> in linea con la media ({avg:.3f} € al L)")
    lines = [
        f"<b>Brand:</b> {st['brand']}",
        f"<b>Distributore:</b> {st['name']}",
        f"<b>Indirizzo:</b> {st['address']}",
        f"<b>Costo {fuel}:</b> {p} € al L",
        saving_line,
        f"<b><a href=\"{maps}\">Andiamo!</a></b>",
    ]
    return "\n".join(lines)


# ── Telegram flow ─────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [["Benzina", "Gasolio"], ["Metano", "GPL"], ["L-GNC", "GNL"]]
    await update.message.reply_text("Che carburante preferisci?",
                                    reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
    ctx.user_data["step"] = "fuel"


async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("step")
    txt = update.message.text

    if step == "fuel":
        if txt in FUEL_MAP:
            ctx.user_data["fuel"] = txt
            kb = [["Self-service", "Servito"], ["Indifferente"]]
            await update.message.reply_text(
                "Tipo di servizio?",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
            ctx.user_data["step"] = "service"
        else:
            kb = [["Benzina", "Gasolio"], ["Metano", "GPL"], ["L-GNC", "GNL"]]
            await update.message.reply_text(
                "Per favore seleziona il carburante usando i pulsanti qui sotto ⛽",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
        return

    if step == "service":
        if txt in SERVICE_MAP:
            await upsert_user(update.effective_user.id, ctx.user_data["fuel"], txt)
            await update.message.reply_text(
                "Profilo salvato. Usa /trova quando vuoi risparmiare ⛽",
                reply_markup=ReplyKeyboardMarkup([["/trova"]], resize_keyboard=True),
            )
            ctx.user_data.clear()
        else:
            kb = [["Self-service", "Servito"], ["Indifferente"]]
            await update.message.reply_text(
                "Per favore seleziona il tipo di servizio usando i pulsanti qui sotto 🛠️",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
        return

    await update.message.reply_text(
        "Digita /trova per cercare un distributore o /start per configurare il profilo.")


async def profilo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("step"):
        await update.message.reply_text("Completa prima la configurazione selezionando carburante e servizio.")
        return
    u = await get_user(update.effective_user.id)
    await update.message.reply_text("Nessun profilo. Usa /start." if not u else f"Fuel: {u[0]}\nServizio: {u[1]}")


async def trova(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("step"):
        await update.message.reply_text("Completa prima la configurazione selezionando carburante e servizio.")
        return ConversationHandler.END
    if not await get_user(update.effective_user.id):
        await update.message.reply_text("Prima configura il profilo con /start.");
        return ConversationHandler.END
    kb = ReplyKeyboardMarkup([[KeyboardButton("Invia posizione 📍", request_location=True)]],
                             resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Mandami la posizione o scrivi un indirizzo preciso:", reply_markup=kb)
    return LOC_STATE


async def handle_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    await process_coords(update, ctx, loc.latitude, loc.longitude);
    return ConversationHandler.END


async def handle_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    coords = await geocode(update.message.text)
    if not coords:
        await update.message.reply_text("Indirizzo troppo generico. Aggiungi civico/città o invia GPS.")
        return LOC_STATE
    await process_coords(update, ctx, *coords);
    return ConversationHandler.END


async def process_coords(update: Update, ctx: ContextTypes.DEFAULT_TYPE, lat: float, lng: float):
    fuel, service = await get_user(update.effective_user.id)
    fuel_type = f"{FUEL_MAP[fuel]}-{SERVICE_MAP[service]}"
    d1 = await call_api(lat, lng, 2, fuel_type);
    d2 = await call_api(lat, lng, 7, fuel_type)
    if not d1["results"] and not d2["results"]:
        await update.message.reply_text("Nessun distributore trovato!");
        return
    if not d1["results"]: d1, d2 = d2, {"results": []}
    s1, avg1 = analyse(d1["results"], int(FUEL_MAP[fuel]));
    s2, avg2 = (None, None)
    if d2["results"]:
        s2, avg2 = analyse(d2["results"], int(FUEL_MAP[fuel]))
        if s1[0]["id"] == s2[0]["id"]: s2 = None
    if not s1[0]["address"]:
        s1[0]["address"] = await fetch_address(s1[0]["id"]) or "Indirizzo non disponibile"
    if s2 and not s2[0]["address"]:
        s2[0]["address"] = await fetch_address(s2[0]["id"]) or "Indirizzo non disponibile"
    parts = ["Il distributore più economico è:", fmt(s1[0], s1[1], avg1, fuel)]
    if s2: parts += ["", "A maggiore distanza trovi anche:", fmt(s2[0], s2[1], avg2, fuel)]
    await log_search(update.effective_user.id, avg2 or avg1, s1[1])
    await update.message.reply_text("\n".join(parts),
                                    reply_markup=ReplyKeyboardMarkup([["/trova"]], resize_keyboard=True),
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True)


# ── Scheduler ─────────────────────────────────────────────────────────────
async def clear_cache():
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM geocache WHERE ts < date('now','-90 days')");
        await db.commit()
    log.info("Cache cleaned")

async def monthly_report(app):
    if not ENABLE_DONATION: return
    today = dt.date.today().replace(day=1);
    start_prev = (today - dt.timedelta(days=1)).replace(day=1)
    end_prev = today - dt.timedelta(days=1)
    async with aiosqlite.connect(DB) as db:
        rows = await (await db.execute("SELECT DISTINCT user_id FROM searches")).fetchall()
        for (uid,) in rows:
            vals = await (await db.execute(
                "SELECT price_avg,price_min FROM searches WHERE user_id=? AND ts BETWEEN ? AND ?",
                (uid, start_prev, end_prev))).fetchall()
            saving = sum((a - m) * 50 for a, m in vals)
            if saving <= 0: continue
            msg = (f"Grazie a TrovaBenzinaBot, lo scorso mese hai risparmiato: {saving:.2f}€*.\n\n"
                   "Potresti offrirmi un caffè?\n"
                   f"{os.getenv('PAYPAL_LINK', 'https://www.paypal.com/donate')}\n\n"
                   "*Calcolo basato su 50 € di rifornimento ogni ricerca.")
            try:
                await app.bot.send_message(uid, msg)
            except Exception:
                log.warning("donation fail uid=%s", uid)


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    loop = asyncio.new_event_loop();
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db());
    log.info("DB ready")
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    sched = AsyncIOScheduler(event_loop=loop, timezone="Europe/Rome")
    sched.add_job(clear_cache, "cron", hour=4)
    if ENABLE_DONATION: sched.add_job(monthly_report, "cron", day=1, hour=9, args=[app])
    sched.start()
    conv = ConversationHandler(
        entry_points=[CommandHandler("trova", trova)],
        states={LOC_STATE: [
            MessageHandler(filters.LOCATION, handle_location),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address)]},
        fallbacks=[],
        block=True,
    )
    app.add_handlers([
        CommandHandler("start", start),
        CommandHandler("profilo", profilo),
        conv,
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
    ])
    log.info("Bot via webhook")
    app.run_webhook(listen="0.0.0.0",
                    port=int(os.getenv("PORT", "8080")),
                    url_path="webhook",
                    webhook_url=f"{os.getenv('BASE_URL')}/webhook")


if __name__ == "__main__":
    main()
