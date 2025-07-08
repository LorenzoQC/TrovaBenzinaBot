import os
import asyncio
import datetime as dt
import logging
import aiohttp
import aiosqlite

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Settings ──────────────────────────────────────────────────────────────
DB = "data.db"
GEOCODE_HARD_CAP = 10_000
ENABLE_DONATION = os.getenv("ENABLE_DONATION", "true").lower() == "true"

FUEL_MAP = {
    "Benzina": "1",
    "Gasolio": "2",
    "Metano": "3",
    "GPL": "4",
    "L-GNC": "323",
    "GNL": "324",
}
SERVICE_MAP = {"Self-service": "1", "Servito": "0", "Indifferente": "x"}
LOC_STATE = 1

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("trova-benzina")

# ── DB helpers ────────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                fuel TEXT,
                service TEXT
            );
            CREATE TABLE IF NOT EXISTS searches(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ts DATETIME,
                price_avg REAL,
                price_min REAL
            );
            CREATE TABLE IF NOT EXISTS geocache(
                query TEXT PRIMARY KEY,
                lat REAL,
                lng REAL,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS geostats(
                month TEXT PRIMARY KEY,
                cnt INTEGER
            );
            """
        )
        await db.commit()


async def upsert_user(uid: int, fuel: str, service: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            """
            INSERT INTO users(user_id,fuel,service) VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE
            SET fuel=excluded.fuel, service=excluded.service
            """,
            (uid, fuel, service),
        )
        await db.commit()


async def get_user(uid: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT fuel,service FROM users WHERE user_id=?", (uid,))
        return await cur.fetchone()


async def log_search(uid: int, price_avg: float, price_min: float):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO searches(user_id,ts,price_avg,price_min) VALUES(?,?,?,?)",
            (uid, dt.datetime.now(), price_avg, price_min),
        )
        await db.commit()

# ── Geocoding with cache & quota ──────────────────────────────────────────
async def geocode(address: str):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT lat,lng FROM geocache WHERE query=?", (address,))
        row = await cur.fetchone()
        if row:
            return row

        month = dt.date.today().strftime("%Y-%m")
        cur = await db.execute("SELECT cnt FROM geostats WHERE month=?", (month,))
        row = await cur.fetchone()
        if row and row[0] >= GEOCODE_HARD_CAP:
            return None

    params = {
        "address": address,
        "components": "country:IT",
        "language": "it",
        "key": os.getenv("GOOGLE_API_KEY"),
    }
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params=params, timeout=10) as r:
            if r.status != 200:
                return None
            data = await r.json()

    results = data.get("results", [])
    if not results:
        return None
    best = next((res for res in results if not res.get("partial_match")), results[0])

    comps = {c["types"][0]: c for c in best.get("address_components", [])}
    if "street_number" not in comps or best["geometry"]["location_type"] != "ROOFTOP":
        return None

    latlng = best["geometry"]["location"]

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO geocache(query,lat,lng) VALUES(?,?,?)",
            (address, latlng["lat"], latlng["lng"]),
        )
        await db.execute(
            """
            INSERT INTO geostats(month,cnt) VALUES(?,1)
            ON CONFLICT(month) DO UPDATE SET cnt=cnt+1
            """,
            (month,),
        )
        await db.commit()
    return latlng["lat"], latlng["lng"]

# ── Detail API for missing address ─────────────────────────────────────────
async def fetch_address(station_id: int):
    url = f"https://carburanti.mise.gov.it/ospzSearch/dettaglio/{station_id}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=10) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("address")
    except Exception as e:
        log.warning("detail API error id=%s: %s", station_id, e)
    return None

# ── Mise API helpers ────────────────────────────────────────────────────────
async def call_api(lat: float, lng: float, radius: float, fuel_type: str):
    url = "https://carburanti.mise.gov.it/ospzApi/search/zone"
    payload = {
        "points": [{"lat": lat, "lng": lng}],
        "radius": radius,
        "fuelType": fuel_type,
        "priceOrder": "asc",
    }
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, timeout=10) as r:
            return await r.json() if r.status == 200 else None


def analyse(results, fuel_id: int):
    if not results:
        return None, None
    prices = []
    for r in results:
        for f in r["fuels"]:
            if f["fuelId"] == fuel_id:
                prices.append(f["price"])
                break
    avg = sum(prices) / len(prices)
    station = results[0]
    station_price = next(
        f["price"] for f in station["fuels"] if f["fuelId"] == fuel_id
    )
    return (station, station_price), avg


def fmt_html(st, p, avg, fuel_name):
    perc = int(round((avg - p) / avg * 100))
    maps = (
        f"https://www.google.com/maps/dir/?api=1&destination="
        f"{st['location']['lat']},{st['location']['lng']}"
    )
    return (
        f"<b>Brand:</b> {st['brand']}<br>"
        f"<b>Distributore:</b> {st['name']}<br>"
        f"<b>Indirizzo:</b> {st['address']}<br>"
        f"<b>Costo {fuel_name}:</b> {p} € al L<br>"
        f"<b>Risparmio:</b> {perc}% rispetto alla media ({avg:.3f} € al L)<br><br>"
        f"<b><a href=\"{maps}\">Andiamo!</a></b>"
    )

# ── Telegram handlers ───────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [["Benzina", "Gasolio"], ["Metano", "GPL"], ["L-GNC", "GNL"]]
    await update.message.reply_text(
        "Che carburante preferisci?",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True),
    )
    ctx.user_data["step"] = "fuel"


async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("step")
    text = update.message.text

    if step == "fuel" and text in FUEL_MAP:
        ctx.user_data["fuel"] = text
        kb = [["Self-service", "Servito"], ["Indifferente"]]
        await update.message.reply_text(
            "Tipo di servizio?",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True),
        )
        ctx.user_data["step"] = "service"
        return

    if step == "service" and text in SERVICE_MAP:
        await upsert_user(
            update.effective_user.id, ctx.user_data["fuel"], text
        )
        await update.message.reply_text(
            "Profilo salvato. Usa /trova quando vuoi risparmiare ⛽"
        )
        ctx.user_data.clear()
        return

    await update.message.reply_text(
        "Vuoi trovare il distributore più economico?\nDigita /trova oppure imposta /start."
    )


async def profilo(update: Update, _):
    u = await get_user(update.effective_user.id)
    txt = (
        "Nessun profilo trovato. Usa /start per configurarlo."
        if not u
        else f"Fuel preferito: {u[0]}\nServizio: {u[1]}"
    )
    await update.message.reply_text(txt)


async def trova(update: Update, _):
    if not await get_user(update.effective_user.id):
        await update.message.reply_text("Prima configura il profilo con /start.")
        return ConversationHandler.END
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("Invia posizione 📍", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Mandami la posizione o scrivi un indirizzo:", reply_markup=kb
    )
    return LOC_STATE


async def handle_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    await process_coords(update, ctx, loc.latitude, loc.longitude)
    return ConversationHandler.END


async def handle_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    res = await geocode(update.message.text)
    if not res:
        await update.message.reply_text(
            "Indirizzo troppo generico o non valido. Aggiungi civico/città oppure invia la posizione GPS."
        )
        return LOC_STATE
    lat, lng = res
    await process_coords(update, ctx, lat, lng)
    return ConversationHandler.END


async def process_coords(
    update: Update, ctx: ContextTypes.DEFAULT_TYPE, lat: float, lng: float
):
    user_pref = await get_user(update.effective_user.id)
    if not user_pref:
        await update.message.reply_text("Imposta prima il profilo con /start.")
        return

    fuel, service = user_pref
    fuel_type = f"{FUEL_MAP[fuel]}-{SERVICE_MAP[service]}"

    data1 = await call_api(lat, lng, 2.5, fuel_type)
    data2 = await call_api(lat, lng, 7.5, fuel_type)

    if not data1["results"] and not data2["results"]:
        await update.message.reply_text(
            "Nessun distributore trovato nella zona indicata!"
        )
        return

    if not data1["results"]:
        data1, data2 = data2, {"results": []}

    s1, avg1 = analyse(data1["results"], int(FUEL_MAP[fuel]))
    s2, avg2 = (None, None)
    if data2["results"]:
        s2, avg2 = analyse(data2["results"], int(FUEL_MAP[fuel]))
        if s1[0]["id"] == s2[0]["id"]:
            s2 = None

    if not s1[0]["address"]:
        s1[0]["address"] = await fetch_address(s1[0]["id"]) or "Indirizzo non disponibile"
    if s2 and not s2[0]["address"]:
        s2[0]["address"] = await fetch_address(s2[0]["id"]) or "Indirizzo non disponibile"

    msg_parts = [
        "<b>Il distributore più economico è:</b><br>",
        fmt_html(s1[0], s1[1], avg1, fuel),
    ]
    if s2:
        msg_parts += [
            "<br><br><b>A maggiore distanza trovi anche:</b><br>",
            fmt_html(s2[0], s2[1], avg2, fuel),
        ]
    await log_search(update.effective_user.id, avg2 or avg1, s1[1])
    await update.message.reply_text(
        "".join(msg_parts),
        reply_markup=ReplyKeyboardMarkup([["/trova"]], resize_keyboard=True),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

# ── Scheduler jobs ─────────────────────────────────────────────────────────
async def clear_cache():
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM geocache WHERE ts < date('now','-90 days')")
        await db.commit()
    log.info("Cache cleaned")


async def monthly_report(app):
    if not ENABLE_DONATION:
        return
    today = dt.date.today().replace(day=1)
    start_prev = (today - dt.timedelta(days=1)).replace(day=1)
    end_prev = today - dt.timedelta(days=1)

    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT DISTINCT user_id FROM searches")
        for (uid,) in await cur.fetchall():
            cur2 = await db.execute(
                """
                SELECT price_avg,price_min FROM searches
                WHERE user_id=? AND ts BETWEEN ? AND ?
                """,
                (uid, start_prev, end_prev),
            )
            rows = await cur2.fetchall()
            saving = sum((a - m) * 50 for a, m in rows)
            if saving <= 0:
                continue
            txt = (
                f"Grazie a TrovaBenzinaBot, lo scorso mese hai risparmiato: {saving:.2f}€*.\n\n"
                "Potresti ricambiare con una piccola donazione?\n"
                f"{os.getenv('PAYPAL_LINK','https://www.paypal.com/donate')}\n\n"
                "*Calcolato ipotizzando 50 € di rifornimento per ricerca."
            )
            try:
                await app.bot.send_message(uid, txt)
            except Exception:
                log.warning("donation message failed user=%s", uid)

# ── Main entry ─────────────────────────────────────────────────────────────
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    log.info("DB ready")

    app = (
        ApplicationBuilder()
        .token(os.getenv("BOT_TOKEN"))
        .parse_mode(ParseMode.HTML)
        .build()
    )

    scheduler = AsyncIOScheduler(event_loop=loop, timezone="Europe/Rome")
    scheduler.add_job(clear_cache, "cron", hour=4)
    if ENABLE_DONATION:
        scheduler.add_job(monthly_report, "cron", day=1, hour=9, args=[app])
    scheduler.start()

    conv = ConversationHandler(
        entry_points=[CommandHandler("trova", trova)],
        states={
            LOC_STATE: [
                MessageHandler(filters.LOCATION, handle_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_address),
            ]
        },
        fallbacks=[],
    )

    app.add_handlers(
        [
            CommandHandler("start", start),
            CommandHandler("profilo", profilo),
            conv,
            MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
        ]
    )

    log.info("Bot running /webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        url_path="webhook",
        webhook_url=f"{os.getenv('BASE_URL')}/webhook",
    )

if __name__ == "__main__":
    main()
