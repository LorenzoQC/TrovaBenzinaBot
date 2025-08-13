# FR - Français
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "fr",
    "language_name": "Français",
    "gasoline": "Essence",
    "diesel": "Diesel",
    "cng": "GNV",
    "lpg": "GPL",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Choisir la langue 🌐️",
    "invalid_language": "⚠️ Langue non valide !",
    "select_fuel": "Choisir le carburant ⛽",
    "invalid_fuel": "⚠️ Carburant non valide !",
    "profile_saved": "✅ Profil enregistré avec succès !\n\nUtilisez /search pour lancer une recherche.",
    "user_already_registered": "⚠️ Utilisateur déjà enregistré !\n\nUtilisez /profile pour modifier les préférences ou /search pour lancer une recherche.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – démarrer le bot et configurer votre profil\n"
        "🔍 /search – trouver les stations les moins chères\n"
        "👤 /profile – afficher et modifier vos paramètres\n"
        "📊 /statistics – afficher vos statistiques\n"
        "📢 /help – afficher ce message\n\n"
    ),
    "disclaimer": (
        "ℹ️ Données sur les prix fournies par le <b>Ministère des Entreprises et du Made in Italy (MISE)</b>.\n"
        "L’exactitude ou l’actualité des informations affichées par le bot n’est pas garantie."
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Langue",
    "fuel": "⛽ Carburant",
    "edit_language": "Modifier la langue 🌐️",
    "edit_fuel": "Modifier le carburant ⛽",
    "language_updated": "✅ Langue mise à jour avec succès !",
    "fuel_updated": "✅ Carburant mis à jour avec succès !",

    # ─────────── /search ───────────
    "ask_location": "Saisissez une adresse ou envoyez votre position 📍",
    "send_location": "Envoyer la position GPS 🌍",
    "geocode_cap_reached": "⚠️ La reconnaissance d’adresse est actuellement indisponible !\n\nVeuillez réessayer plus tard ou envoyer votre position.",
    "invalid_address": "⚠️ Adresse non valide !\n\nSaisissez une autre adresse ou envoyez votre position.",
    "processing_search": "Recherche en cours...🔍",
    "please_wait": "Un instant, s’il vous plaît...⏳",
    "no_stations": "❌ Aucune station trouvée",
    "area_label": "Stations dans un rayon de {radius} km",
    "stations_analyzed": "stations analysées",
    "average_zone_price": "Prix moyen {fuel_name} dans la zone",
    "address": "Adresse",
    "no_address": "-",
    "price": "Prix",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "moins cher que la moyenne",
    "equal_average": "conforme à la moyenne",
    "last_update": "Dernière mise à jour",
    "btn_narrow": "Répéter la recherche avec un rayon de {radius} km 🔄",
    "btn_widen": "Répéter la recherche avec un rayon de {radius} km 🔄",
    "search_session_expired": "⚠️ Session expirée !\n\nUtilisez /search pour lancer une nouvelle recherche.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Aucune statistique disponible !\n\nUtilisez /search pour lancer une recherche.",
    "statistics": (
        "<b><u>Statistiques {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} recherches</b> effectuées.\n"
        "<b>{num_stations} stations</b> analysées.\n"
        "Économie moyenne : <b>{avg_eur_save_per_unit} {price_unit}</b>, soit <b>{avg_pct_save}%</b>.\n"
        "Économie annuelle estimée : <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ Comment avons-nous calculé ces chiffres ?</i>\n"
                       "• L’économie moyenne est calculée comme la différence moyenne, pour chaque recherche, entre le prix moyen de la zone et la station la moins chère proposée par le bot.\n"
                       "• L’économie annuelle suppose 10 000 km par an avec une consommation moyenne de : \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} par 100 km",
    "reset_statistics": "Réinitialiser les statistiques ♻️",
    "statistics_reset": "✅ Statistiques réinitialisées avec succès !\n\nUtilisez /search pour lancer une recherche.",

    "unknown_command_hint": "⚠️ Commande non valide !\n\nUtilisez la commande /help pour voir la liste des commandes disponibles.",

}
