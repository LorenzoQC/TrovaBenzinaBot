from sqlalchemy import select, func
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from trovabenzina.config import DEFAULT_LANGUAGE
from trovabenzina.db.crud import get_user_stats, get_user
from trovabenzina.db.models import Fuel, Search, User
from trovabenzina.db.session import AsyncSession
from trovabenzina.i18n import t

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
        # no statistics to show
        await update.effective_message.reply_text(
            t("no_statistics", lang)
        )
        return

    # open a session to fetch consumption values
    async with AsyncSession() as session:
        # preload consumption for all fuels
        fuel_ids = [s["fuel_id"] for s in stats]
        rows = await session.execute(
            select(Fuel).where(Fuel.id.in_(fuel_ids))
        )
        fuels = {f.id: f for f in rows.scalars().all()}

    # send one message per fuel
    for s in stats:
        fuel_name = s.get("fuel_name")
        num_searches = s.get("num_searches")
        num_stations = s.get("num_stations")
        avg_eur = s.get("avg_eur_save_per_unit")
        avg_pct = s.get("avg_pct_save") * 100  # fraction → percent
        est_annual = s.get("estimated_annual_save_eur")
        fid = s.get("fuel_id")

        # determine price unit (€/l or €/kg)
        price_unit = f"{t('eur_symbol', lang)}{t('slash_symbol', lang)}{t('liter_symbol', lang)}"
        # assume fuelId 3 = CNG
        if str(s.get("fuel_code")) == "3":
            price_unit = f"{t('eur_symbol', lang)}{t('slash_symbol', lang)}{t('kilo_symbol', lang)}"

        # consumption and unit of measure
        consumption = fuels.get(fid).avg_consumption_per_100km if fuels.get(fid) else None
        uom = t('liter_symbol', lang) if consumption and consumption > 0 else t('kilo_symbol', lang)

        message = t(
            "statistics",
            lang,
            fuel_name=fuel_name,
            num_searches=num_searches,
            num_stations=num_stations,
            avg_eur_save_per_unit=f"{avg_eur:.3f}",
            price_unit=price_unit,
            avg_pct_save=f"{avg_pct:.1f}",
            avg=f"{est_annual:.2f} {t('eur_symbol', lang)}",
            avg_consumption_per_100km=f"{consumption:.1f}",
            uom=uom
        )
        await update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    # button to reset statistics
    reset_button = InlineKeyboardButton(
        t("reset_statistics", lang), callback_data="reset_stats"
    )
    kb = InlineKeyboardMarkup([[reset_button]])
    await update.effective_message.reply_text(
        t("reset_statistics", lang),
        reply_markup=kb
    )


async def reset_stats_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Callback for resetting the user's search statistics (soft-delete).
    """
    query = update.callback_query
    await query.answer()
    tg_id = update.effective_user.id
    # fetch internal user id and lang
    user_row = await get_user(tg_id)
    if user_row:
        _, lang = user_row
    else:
        lang = DEFAULT_LANGUAGE

    async with AsyncSession() as session:
        # get internal id
        res = await session.execute(
            select(User.id).where(User.tg_id == tg_id)
        )
        user_id = res.scalar_one()
        # mark all searches as deleted
        await session.execute(
            update(Search)
            .where(Search.user_id == user_id)
            .values(del_ts=func.now())
        )
        await session.commit()

    # confirm reset
    await query.edit_message_text(
        t("statistics reset", lang)
    )


# handler registrations
statistics_handler = [
    CommandHandler("statistics", statistics_ep),
    CallbackQueryHandler(reset_stats_cb, pattern="^reset_stats$")
]
