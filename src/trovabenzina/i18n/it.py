# IT - Italiano
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "it",
    "language_name": "Italiano",
    "gasoline": "Benzina",
    "diesel": "Gasolio",
    "cng": "Metano",
    "lpg": "GPL",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Seleziona lingua 🌐️",
    "invalid_language": "⚠️ Lingua non valida!",
    "select_fuel": "Seleziona carburante ⛽",
    "invalid_fuel": "⚠️ Carburante non valido!",
    "profile_saved": "✅ Profilo salvato correttamente!\n\nUtilizza il comando /search per avviare una ricerca.",
    "user_already_registered": "⚠️ Utente già registrato!\n\nUtilizza il comando /profile per modificare le preferenze o il comando /search per avviare una ricerca.",

    # ─────────── /help ───────────
    "help": (
        "/start – configura il profilo\n"
        "/search – cerca i distributori più economici\n"
        "/profile – modifica il profilo\n"
        "/help – mostra questo messaggio"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Lingua",
    "fuel": "⛽ Carburante",
    "edit_language": "Modifica lingua 🌐️",
    "edit_fuel": "Modifica carburante ⛽",
    "language_updated": "✅ Lingua aggiornata correttamente!",
    "fuel_updated": "✅ Carburante aggiornato correttamente!",

    # ─────────── /search ───────────
    "ask_location": "Digita un indirizzo oppure invia la tua posizione 📍",
    "send_location": "Invia posizione GPS 🌍",
    "geocode_cap_reached": "⚠️ Riconoscimento indirizzo al momento non disponibile!\n.Per favore riprova più tardi, oppure invia la tua posizione.",
    "invalid_address": "⚠️ Indirizzo non valido",
    "processing_search": "Ricerca in corso...🔍",
    "no_stations": "❌ Nessun distributore trovato",
    "near_label": "Distributori nel raggio di 2 km",
    "far_label": "Distributori nel raggio di 7 km",
    "stations_analyzed": "stazioni analizzate",
    "average_zone_price": "Prezzo medio della zona",
    "address": "Indirizzo",
    "no_address": "-",
    "price": "Prezzo",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "più economico della media",
    "equal_average": "in linea con la media",
    "last_update": "Ultimo aggiornamento",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Nessuna statistica disponibile!\n\nUtilizza il comando /search per avviare una ricerca.",
    "statistics": (
        "<b><u>Statistiche {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} ricerche</b> effettuate.\n"
        "<b>{num_stations} distributori</b> analizzati.\n"
        "Risparmio medio: <b>{avg_eur_save_per_unit} {price_unit}</b>, ovvero il <b>{avg_pct_save}%</b>.\n"
        "Risparmio annuo stimato: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>ℹ️ Come abbiamo calcolato questi dati?</i>\n"
                       "• Il risparmio medio è calcolato ipotizzando di effettuare sempre il rifornimento presso il distributore più economico proposto dal bot, confrontandone il prezzo con il prezzo medio della zona.\n"
                       "• Il risparmio annuo è calcolato ipotizzando una percorrenza di 10.000km annui con un consumo medio di: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} ogni 100km",
    "reset_statistics": "Azzera le statistiche ♻️",
    "statistics reset": "✅ Statistiche resettate correttamente!\n\nUtilizza il comando /search per avviare una ricerca.",

}
