import logging

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from api import geocode, call_api, fetch_address
from config import FUEL_MAP, SERVICE_MAP, LOC_STATE, DEFAULT_RADIUS_NEAR, DEFAULT_RADIUS_FAR
from db import upsert_user, get_user, log_search
from utils import analyse, fmt

log = logging.getLogger(__name__)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [["Benzina", "Gasolio"], ["Metano", "GPL"], ["L-GNC", "GNL"]]
    await update.message.reply_text(
        "Che carburante preferisci?",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )
    ctx.user_data["step"] = "fuel"


async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("step")
    text = update.message.text

    if step == "fuel":
        if text in FUEL_MAP:
            ctx.user_data["fuel"] = text
            kb = [["Self-service", "Servito"], ["Indifferente"]]
            await update.message.reply_text(
                "Tipo di servizio?",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
            )
            ctx.user_data["step"] = "service"
        else:
            kb = [["Benzina", "Gasolio"], ["Metano", "GPL"], ["L-GNC", "GNL"]]
            await update.message.reply_text(
                "Select fuel via buttons ⛽",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
            )
        return

    if step == "service":
        if text in SERVICE_MAP:
            await upsert_user(update.effective_user.id, ctx.user_data["fuel"], text)
            await update.message.reply_text(
                "Profile saved. Use /trova to find stations ⛽",
                reply_markup=ReplyKeyboardMarkup([["/trova"]], resize_keyboard=True)
            )
            ctx.user_data.clear()
        else:
            kb = [["Self-service", "Servito"], ["Indifferente"]]
            await update.message.reply_text(
                "Select service via buttons 🛠️",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
            )
        return

    await update.message.reply_text("Use /start to configure or /trova to search.")


async def profilo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("step"):
        await update.message.reply_text("Complete setup first.")
        return
    user = await get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("No profile found. Use /start.")
    else:
        fuel, service = user
        await update.message.reply_text(f"Fuel: {fuel}\nService: {service}")


async def trova(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("step"):
        await update.message.reply_text("Complete setup first.")
        return ConversationHandler.END
    if not await get_user(update.effective_user.id):
        await update.message.reply_text("No profile. Use /start.")
        return ConversationHandler.END

    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("Invia posizione 📍", request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text("Send location or address:", reply_markup=kb)
    return LOC_STATE


async def handle_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    await process_coords(update, ctx, loc.latitude, loc.longitude)
    return ConversationHandler.END


async def handle_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    coords = await geocode(update.message.text)
    if not coords:
        await update.message.reply_text(
            "Address too generic. Add street/city or send GPS."
        )
        return LOC_STATE
    await process_coords(update, ctx, *coords)
    return ConversationHandler.END


async def process_coords(update: Update, ctx: ContextTypes.DEFAULT_TYPE, lat: float, lng: float):
    fuel, service = await get_user(update.effective_user.id)
    ft = f"{FUEL_MAP[fuel]}-{SERVICE_MAP[service]}"
    d1 = await call_api(lat, lng, DEFAULT_RADIUS_NEAR, ft)
    d2 = await call_api(lat, lng, DEFAULT_RADIUS_FAR, ft)

    if not d1["results"] and not d2["results"]:
        return await update.message.reply_text("No stations found!")
    if not d1["results"]:
        d1, d2 = d2, {"results": []}

    (s1, price1), avg1 = analyse(d1["results"], int(FUEL_MAP[fuel]))
    sec_text = None
    if d2["results"]:
        (s2, price2), avg2 = analyse(d2["results"], int(FUEL_MAP[fuel]))
        if s1["id"] != s2["id"]:
            sec_text = fmt(s2, price2, avg2, fuel)

    if not s1.get("address"):
        s1["address"] = await fetch_address(s1["id"]) or "Address not available"

    parts = ["Il distributore più economico è:", fmt(s1, price1, avg1, fuel)]
    if sec_text:
        parts += ["", "A maggiore distanza trovi anche:", sec_text]

    await log_search(update.effective_user.id, avg1, price1)
    await update.message.reply_text(
        "\n".join(parts),
        reply_markup=ReplyKeyboardMarkup([["/trova"]], resize_keyboard=True),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    return None
