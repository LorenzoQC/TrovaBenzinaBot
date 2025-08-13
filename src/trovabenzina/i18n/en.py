# EN - English
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "en",
    "language_name": "English",
    "gasoline": "Gasoline",
    "diesel": "Diesel",
    "cng": "CNG",
    "lpg": "LPG",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Select language 🌐️",
    "invalid_language": "⚠️ Invalid language!",
    "select_fuel": "Select fuel ⛽",
    "invalid_fuel": "⚠️ Invalid fuel!",
    "profile_saved": "✅ Profile saved successfully!\n\nUse /search to start a search.",
    "user_already_registered": "⚠️ User already registered!\n\nUse /profile to change preferences or /search to start a search.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – launch the bot and set up your profile\n"
        "🔍 /search – find the cheapest fuel stations\n"
        "👤 /profile – view and edit your settings\n"
        "📊 /statistics – view your statistics\n"
        "📢 /help – show this message\n\n"
    ),
    "disclaimer": (
        "ℹ️ Station data provided by the <b>Ministry of Enterprises and Made in Italy (MISE)</b>.\n"
        "The accuracy or timeliness of the information shown by the bot is not guaranteed."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Language",
    "fuel": "⛽ Fuel",
    "edit_language": "Edit language 🌐️",
    "edit_fuel": "Edit fuel ⛽",
    "language_updated": "✅ Language updated successfully!",
    "fuel_updated": "✅ Fuel updated successfully!",

    # ─────────── /search ───────────
    "ask_location": "Type an address or send your location 📍",
    "send_location": "Send GPS location 🌍",
    "geocode_cap_reached": "⚠️ Address recognition currently unavailable!\n\nPlease try again later, or send your location.",
    "invalid_address": "⚠️ Invalid address!\n\nType another address or send your location.",
    "processing_search": "Search in progress...🔍",
    "please_wait": "Working on it, please wait...⏳",
    "no_stations": "❌ No stations found",
    "area_label": "Stations within {radius} km",
    "stations_analyzed": "stations analyzed",
    "average_zone_price": "Average {fuel_name} price in the area",
    "address": "Address",
    "no_address": "-",
    "price": "Price",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "cheaper than the average",
    "equal_average": "in line with the average",
    "last_update": "Last update",
    "btn_narrow": "Repeat search with {radius} km radius 🔄",
    "btn_widen": "Repeat search with {radius} km radius 🔄",
    "search_session_expired": "⚠️ Session expired!\n\nUse /search to start a new search.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ No statistics available!\n\nUse /search to start a search.",
    "statistics": (
        "<b><u>{fuel_name} statistics</u></b> 📊\n"
        "<b>{num_searches} searches</b> performed.\n"
        "<b>{num_stations} stations</b> analyzed.\n"
        "Average saving: <b>{avg_eur_save_per_unit} {price_unit}</b>, i.e. <b>{avg_pct_save}%</b>.\n"
        "Estimated annual saving: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ How did we calculate these figures?</i>\n"
                       "• The average saving is computed as the average difference, for each search, between the area’s average price and the cheapest station found by the bot.\n"
                       "• The annual saving assumes 10,000km per year with an average consumption of: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} every 100km",
    "reset_statistics": "Reset statistics ♻️",
    "statistics_reset": "✅ Statistics reset successfully!\n\nUse /search to start a search.",

    "unknown_command_hint": "⚠️ Invalid command!\n\nUse the /help command for a list of available commands.",

}
