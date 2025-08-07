# FR - Français
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "fr",
    "language_name": "Français",
    "gasoline": "Essence",
    "diesel": "Diesel",
    "cng": "Gaz naturel",
    "lpg": "GPL",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Choisir la langue 🌐️",
    "invalid_language": "⚠️ Langue invalide !",
    "select_fuel": "Choisir le carburant ⛽",
    "invalid_fuel": "⚠️ Carburant invalide !",
    "profile_saved": "✅ Profil enregistré avec succès !\n\nUtilisez /search pour lancer une recherche.",
    "user_already_registered": "⚠️ Utilisateur déjà enregistré !\n\nUtilisez /profile pour modifier les préférences ou /search pour lancer une recherche.",

    # ─────────── /help ───────────
    "help": (
        "/start – configurer votre profil\n"
        "/search – rechercher les stations les moins chères\n"
        "/profile – modifier votre profil\n"
        "/help – afficher ce message"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Langue",
    "fuel": "⛽ Carburant",
    "edit_language": "Modifier la langue 🌐️",
    "edit_fuel": "Modifier le carburant ⛽",
    "language_updated": "✅ Langue mise à jour avec succès !",
    "fuel_updated": "✅ Carburant mis à jour avec succès !",

    # ─────────── /search ───────────
    "ask_location": "Entrez une adresse ou envoyez votre position 📍",
    "send_location": "Envoyer la position GPS 🌍",
    "geocode_cap_reached": "⚠️ La reconnaissance d'adresse n'est pas disponible pour le moment !\nVeuillez réessayer plus tard ou envoyer votre position.",
    "invalid_address": "⚠️ Adresse invalide",
    "processing_search": "Recherche en cours...🔍",
    "no_stations": "❌ Aucune station trouvée",
    "near_label": "Stations dans un rayon de 2 km",
    "far_label": "Stations dans un rayon de 7 km",
    "stations_analyzed": "stations analysées",
    "average_zone_price": "Prix moyen de la zone",
    "address": "Adresse",
    "no_address": "-",
    "price": "Prix",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "moins cher que la moyenne",
    "equal_average": "conforme à la moyenne",
    "last_update": "Dernière mise à jour",

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
