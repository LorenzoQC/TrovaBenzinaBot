from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from trovabenzina.config import DEFAULT_LANGUAGE
from trovabenzina.i18n import t
from ..db import (
    get_user_stats,
    get_user,
    get_fuels_by_ids_map,
    soft_delete_user_searches_by_tg_id,
)

__all__ = ["statistics_handler"]

async def statistics_ep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /statistics command: shows per-fuel stats or a no-data message.
    """
    tg_id = update.effective_user.id
    # fetch user language
    user_row = await get_user(tg_id)
    _, lang = user_row if user_row else (None, DEFAULT_LANGUAGE)

    stats = await get_user_stats(tg_id)
    if not stats:
        await update.effective_message.reply_text(
            t("no_statistics", lang)
        )
        return

    # preload consumption values
    fuel_ids = [s["fuel_id"] for s in stats]
    fuels = await get_fuels_by_ids_map(fuel_ids)

    # build per-fuel blocks and collect consumption info
    blocks = []
    consumption_lines = []
    for s in stats:
        fuel_name = t(s.get("fuel_name"), lang)
        num_searches = s.get("num_searches")
        num_stations = s.get("num_stations")
        avg_eur = s.get("avg_eur_save_per_unit")
        avg_pct = s.get("avg_pct_save") * 100
        est_save = s.get("estimated_annual_save_eur")
        code = str(s.get("fuel_code"))
        fid = s.get("fuel_id")

        # determine price unit (€/l or €/kg)
        if code == "3":  # CNG
            pu = f"{t('eur_symbol', lang)}{t('slash_symbol', lang)}{t('kilo_symbol', lang)}"
        else:
            pu = f"{t('eur_symbol', lang)}{t('slash_symbol', lang)}{t('liter_symbol', lang)}"

        # consumption and unit of measure
        cons = fuels.get(fid).avg_consumption_per_100km if fuels.get(fid) else 0
        uom = t('kilo_symbol', lang) if code == "3" else t('liter_symbol', lang)
        # collect consumption line for later
        consumption_lines.append(
            t(
                "fuel_consumption", lang,
                fuel_name=fuel_name,
                avg_consumption_per_100km=f"{cons:.1f}",
                uom=uom
            )
        )

        # build block without info
        blocks.append(
            t(
                "statistics", lang,
                fuel_name=fuel_name,
                num_searches=num_searches,
                num_stations=num_stations,
                avg_eur_save_per_unit=f"{avg_eur:.3f}",
                price_unit=pu,
                avg_pct_save=f"{avg_pct:.1f}",
                estimated_annual_save_eur=f"{est_save:.2f} {t('eur_symbol', lang)}"
            )
        )

    # combine fuel blocks
    combined = "\n\n".join(blocks)
    # append info and consumption lines
    combined += "\n\n\n" + t("statistics_info", lang)
    combined += "\n".join(consumption_lines)

    # reset button under combined message
    reset_btn = InlineKeyboardButton(
        t("reset_statistics", lang), callback_data="reset_stats"
    )
    kb = InlineKeyboardMarkup([[reset_btn]])

    await update.effective_message.reply_text(
        combined,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=kb
    )

async def reset_stats_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Callback for resetting the user's search statistics (soft-delete).
    """
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    user_row = await get_user(tg_id)
    if user_row:
        _, lang = user_row
    else:
        lang = DEFAULT_LANGUAGE

    await soft_delete_user_searches_by_tg_id(tg_id)

    await query.edit_message_text(
        t("statistics reset", lang)
    )

statistics_handler = [
    CommandHandler("statistics", statistics_ep),
    CallbackQueryHandler(reset_stats_cb, pattern="^reset_stats$")
]
