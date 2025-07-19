from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from trovabenzina.core.db import (
    get_user,
    add_favorite,
    list_favorites,
    delete_favorite,
)
from trovabenzina.i18n import t
from trovabenzina.utils import (
    STEP_FAV_ACTION,
    STEP_FAV_NAME,
    STEP_FAV_LOC,
    STEP_FAV_REMOVE,
    inline_kb,
    reverse_geocode_or_blank,
)

__all__ = ["favorites_conv", "favorites_callback"]


# ── /favorites entry ──────────────────────────────────────────────────────
async def favorites_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    _, _, lang = await get_user(update.effective_user.id)
    favs = await list_favorites(update.effective_user.id)
    if not favs:
        txt = t("no_favorites", lang)
    else:
        lines = [
            f"{i + 1}) {name} • {await reverse_geocode_or_blank(lat, lng)}"
            for i, (name, lat, lng) in enumerate(favs)
        ]
        txt = f"{t('favorites_title', lang)}\n" + "\n".join(lines)

    kb = inline_kb([(t("add_favorite_btn", lang), "fav_add")], per_row=2)
    if favs:
        kb += inline_kb([(t("edit_favorite_btn", lang), "fav_edit")], per_row=2)
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
        kb = inline_kb([(name, f"favdel_{name}") for name, _, _ in favs])
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
        from trovabenzina.core.api import geocode  # local import to avoid loop
        coords = await geocode(update.message.text)
        if not coords:
            await update.message.reply_text(t("invalid_address", lang))
            return STEP_FAV_LOC
        lat, lng = coords

    await add_favorite(uid, name, lat, lng)
    await update.message.reply_text(t("fav_saved", lang))
    ctx.user_data.clear()
    return ConversationHandler.END


# ── ConversationHandler object ───────────────────────────────────────────
favorites_conv = ConversationHandler(
    entry_points=[("command", "favorites", favorites_cmd)],
    states={
        STEP_FAV_ACTION: [("callback", favorites_callback)],
        STEP_FAV_NAME: [("message_text", fav_name)],
        STEP_FAV_LOC: [
            ("message_location", fav_loc),
            ("message_text", fav_loc),
        ],
        STEP_FAV_REMOVE: [("callback", favorites_callback)],
    },
    fallbacks=[],
)
