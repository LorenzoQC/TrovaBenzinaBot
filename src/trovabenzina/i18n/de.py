# DE - Deutsch
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "de",
    "language_name": "Deutsch",
    "gasoline": "Benzin",
    "diesel": "Diesel",
    "cng": "Erdgas",
    "lpg": "Autogas",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Sprache auswählen 🌐️",
    "invalid_language": "⚠️ Ungültige Sprache!",
    "select_fuel": "Kraftstoff auswählen ⛽",
    "invalid_fuel": "⚠️ Ungültiger Kraftstoff!",
    "profile_saved": "✅ Profil erfolgreich gespeichert!\n\nVerwende /search, um eine Suche zu starten.",
    "user_already_registered": "⚠️ Benutzer bereits registriert!\n\nVerwende /profile, um die Einstellungen zu ändern oder /search für eine Suche.",

    # ─────────── /help ───────────
    "help": (
        "/start – Profil einrichten\n"
        "/search – Günstigste Tankstellen suchen\n"
        "/profile – Profil bearbeiten\n"
        "/help – Diese Hilfe anzeigen"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Sprache",
    "fuel": "⛽ Kraftstoff",
    "edit_language": "Sprache bearbeiten 🌐️",
    "edit_fuel": "Kraftstoff bearbeiten ⛽",
    "language_updated": "✅ Sprache erfolgreich aktualisiert!",
    "fuel_updated": "✅ Kraftstoff erfolgreich aktualisiert!",

    # ─────────── /search ───────────
    "ask_location": "Adresse eingeben oder deinen Standort senden 📍",
    "send_location": "GPS-Standort senden 🌍",
    "geocode_cap_reached": "⚠️ Adresserkennung momentan nicht verfügbar!\nBitte später erneut versuchen oder Standort senden.",
    "invalid_address": "⚠️ Ungültige Adresse",
    "processing_search": "Suche läuft...🔍",
    "no_stations": "❌ Keine Tankstellen gefunden",
    "near_label": "Tankstellen innerhalb von 2 km",
    "far_label": "Tankstellen innerhalb von 7 km",
    "stations_analyzed": "Stationen analysiert",
    "average_zone_price": "Durchschnittspreis der Zone",
    "address": "Adresse",
    "no_address": "-",
    "price": "Preis",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "günstiger als der Durchschnitt",
    "equal_average": "entspricht dem Durchschnitt",
    "last_update": "Letzte Aktualisierung",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Keine Statistiken verfügbar!\n\nVerwende /search, um eine Suche zu starten.",
    "statistics": (
        "<b><u>{fuel_name} Statistiken</u></b> 📊\n"
        "<b>{num_searches} Suchen</b> durchgeführt.\n"
        "<b>{num_stations} Stationen</b> analysiert.\n"
        "Durchschnittliche Einsparung: <b>{avg_eur_save_per_unit} {price_unit}</b>, bzw. <b>{avg_pct_save}%</b>.\n"
        "Geschätzte jährliche Einsparung: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>ℹ️ Wie wurden diese Daten berechnet?</i>\n"
                       "• Die durchschnittliche Einsparung basiert darauf, stets an der günstigsten vom Bot vorgeschlagenen Tankstelle im Vergleich zum Durchschnittspreis der Zone zu tanken.\n"
                       "• Die jährliche Einsparung basiert auf einer Fahrleistung von 10.000 km pro Jahr bei einem Durchschnittsverbrauch von:\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} pro 100 km",
    "reset_statistics": "Statistiken zurücksetzen ♻️",
    "statistics_reset": "✅ Statistiken erfolgreich zurückgesetzt!\n\nVerwende /search, um eine Suche zu starten.",
}
