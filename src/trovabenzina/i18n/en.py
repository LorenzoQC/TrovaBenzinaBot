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
    "user_already_registered": "⚠️ User already registered!\n\nUse /profile to modify preferences or /search to start a search.",

    # ─────────── /help ───────────
    "help": (
        "/start – set up your profile\n"
        "/search – search for the cheapest stations\n"
        "/profile – modify your profile\n"
        "/help – show this message"
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
    "geocode_cap_reached": "⚠️ Address recognition not available at the moment!\nPlease try again later, or send your location.",
    "invalid_address": "⚠️ Invalid address",
    "processing_search": "Searching...🔍",
    "no_stations": "❌ No stations found",
    "near_label": "Stations within 2 km",
    "far_label": "Stations within 7 km",
    "stations_analyzed": "stations analyzed",
    "average_zone_price": "Average zone price",
    "address": "Address",
    "no_address": "-",
    "price": "Price",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "cheaper than average",
    "equal_average": "in line with average",
    "last_update": "Last update",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ No statistics available!\n\nUse /search to start a search.",
    "statistics": (
        "<b><u>{fuel_name} Statistics</u></b> 📊\n"
        "<b>{num_searches} searches</b> performed.\n"
        "<b>{num_stations} stations</b> analyzed.\n"
        "Average savings: <b>{avg_eur_save_per_unit} {price_unit}</b>, or <b>{avg_pct_save}%</b>.\n"
        "Estimated annual savings: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>ℹ️ How are these figures calculated?</i>\n"
                       "• Average savings assumes always filling at the cheapest station offered by the bot compared to the zone average price.\n"
                       "• Annual savings assumes 10,000 km per year at an average consumption of:\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} per 100km",
    "reset_statistics": "Reset statistics ♻️",
    "statistics_reset": "✅ Statistics reset successfully!\n\nUse /search to start a search.",
}
