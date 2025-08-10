from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from ..db import (
    get_user_stats,
    get_fuels_by_ids_map,
    get_user_language_code_by_tg_id,
    soft_delete_user_searches_by_tg_id,
)
from ..i18n import t
from ..utils import (
    format_price_unit,
    symbol_kilo,
    symbol_liter,
    symbol_eur,
)

__all__ = ["statistics_handler"]


async def statistics_ep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /statistics command: shows per-fuel stats or a no-data message."""
    tg_id = update.effective_user.id
    lang = await get_user_language_code_by_tg_id(tg_id)

    stats = await get_user_stats(tg_id)
    if not stats:
        await update.effective_message.reply_text(t("no_statistics", lang))
        return

    fuel_ids = [s["fuel_id"] for s in stats]
    fuels = await get_fuels_by_ids_map(fuel_ids)

    blocks = []
    consumption_lines = []
    for s in stats:
        fuel_name = t(s.get("fuel_name"), lang)
        num_searches = s.get("num_searches") or 0
        num_stations = s.get("num_stations") or 0
        avg_eur = s.get("avg_eur_save_per_unit") or 0.0
        avg_pct = (s.get("avg_pct_save") or 0.0) * 100
        est_save = s.get("estimated_annual_save_eur") or 0.0
        fid = s.get("fuel_id")

        fmeta = fuels.get(fid)
        uom = getattr(fmeta, "uom", None).strip()
        cons = float(getattr(fmeta, "avg_consumption_per_100km", 0.0)) if fmeta else 0.0

        pu = format_price_unit(uom=uom, t=t, lang=lang)
        uom_symbol = symbol_kilo(t, lang) if uom.lower() in {"kg", "kilogram"} else symbol_liter(t, lang)

        consumption_lines.append(
            t(
                "fuel_consumption",
                lang,
                fuel_name=fuel_name,
                avg_consumption_per_100km=f"{cons:.1f}",
                uom=uom_symbol,
            )
        )

        blocks.append(
            t(
                "statistics",
                lang,
                fuel_name=fuel_name,
                num_searches=num_searches,
                num_stations=num_stations,
                avg_eur_save_per_unit=f"{avg_eur:.3f}",
                price_unit=pu,
                avg_pct_save=f"{avg_pct:.1f}",
                estimated_annual_save_eur=f"{est_save:.2f} {symbol_eur(t, lang)}",
            )
        )

    combined = "\n\n".join(blocks)
    combined += "\n\n\n" + t("statistics_info", lang) + "\n".join(consumption_lines)

    reset_btn = InlineKeyboardButton(t("reset_statistics", lang), callback_data="reset_stats")
    kb = InlineKeyboardMarkup([[reset_btn]])

    await update.effective_message.reply_text(
        combined,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=kb,
    )


async def reset_stats_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for resetting the user's search statistics (soft-delete)."""
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    lang = await get_user_language_code_by_tg_id(tg_id)

    await soft_delete_user_searches_by_tg_id(tg_id)
    await query.edit_message_text(t("statistics_reset", lang))


statistics_handler = [
    CommandHandler("statistics", statistics_ep),
    CallbackQueryHandler(reset_stats_cb, pattern="^reset_stats$"),
]
