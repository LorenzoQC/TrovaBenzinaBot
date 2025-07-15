from config import DEFAULT_LANGUAGE

MSG = {
    # ─────────── /start ───────────
    "ask_language_choice": {
        "it": "Seleziona lingua 🌐️",
        "en": "Choose language 🌐️",
    },
    "invalid_language": {
        "it": "⚠️ Lingua non valida",
        "en": "⚠️ Invalid language",
    },
    "ask_fuel": {
        "it": "Seleziona carburante 🛢️",
        "en": "Choose fuel 🛢️",
    },
    "invalid_fuel": {
        "it": "⚠️ Carburante non valido",
        "en": "⚠️ Invalid fuel",
    },
    "ask_service": {
        "it": "Seleziona servizio ⛽",
        "en": "Choose service ⛽",
    },
    "invalid_service": {
        "it": "⚠️ Servizio non valido",
        "en": "⚠️ Invalid service",
    },
    "profile_saved": {
        "it": "✅ Profilo salvato correttamente",
        "en": "✅ Profile saved correctly",
    },

    # ─────────── /find ───────────
    "select_radius": {
        "it": "Seleziona raggio di ricerca 📏",
        "en": "Select search radius 📏",
    },
    "invalid_radius": {
        "it": "⚠️ Raggio non valido",
        "en": "⚠️ Invalid radius",
    },
    "send_location": {
        "it": "Invia posizione GPS 📍",
        "en": "Send GPS location 📍",
    },
    "ask_location": {
        "it": "➤ Invia la tua posizione o scegli un luogo preferito",
        "en": "➤ Send your location or pick a favourite place",
    },
    "invalid_address": {
        "it": "⚠️ Indirizzo non valido",
        "en": "⚠️ Invalid address",
    },
    "no_stations": {
        "it": "❌ Nessun distributore trovato",
        "en": "❌ No stations found",
    },

    # price notes
    "note_cheaper": {
        "it": "Risparmi {pct}%!",
        "en": "Save {pct}%!",
    },
    "note_equal": {
        "it": "In linea con la media",
        "en": "In line with average",
    },
    "note_more_expensive": {
        "it": "Costa {pct}% in più",
        "en": "Costs {pct}% more",
    },
    "compared_to_avg": {
        "it": "(media: {avg:.3f} €/L)",
        "en": "(average: {avg:.3f} €/L)",
    },
    "lets_go": {
        "it": "Andiamo!",
        "en": "Let's go!",
    },
    "no_address": {
        "it": "Indirizzo non disponibile",
        "en": "Address not available",
    },

    # ─────────── /favorites ───────────
    "favorites_title": {
        "it": "Luoghi preferiti salvati:",
        "en": "Saved favourite places:",
    },
    "add_favorite_btn": {
        "it": "➕ Aggiungi preferito",
        "en": "➕ Add favourite",
    },
    "edit_favorite_btn": {
        "it": "🗑️ Modifica preferiti",
        "en": "🗑️ Edit favourites",
    },
    "which_fav_remove": {
        "it": "Quale preferito vuoi rimuovere?",
        "en": "Which favourite do you want to remove?",
    },
    "fav_removed": {
        "it": "Preferito eliminato",
        "en": "Favourite removed",
    },
    "fav_saved": {
        "it": "✅ Preferito salvato con successo",
        "en": "✅ Favourite saved successfully",
    },
    "no_favorites": {
        "it": "Nessun luogo preferito salvato",
        "en": "No favourite places saved",
    },
    "ask_fav_name": {
        "it": "Assegna un nome al luogo preferito",
        "en": "Give a name to the favourite place",
    },
    "ask_fav_location": {
        "it": "Invia posizione o indirizzo per il preferito",
        "en": "Send location or address for the favourite",
    },

    # ─────────── /profile ───────────
    "edit_language": {
        "it": "Modifica lingua 🌐️",
        "en": "Edit language 🌐️",
    },
    "edit_fuel": {
        "it": "Modifica carburante 🛢️",
        "en": "Edit fuel 🛢️",
    },
    "edit_service": {
        "it": "Modifica servizio ⛽",
        "en": "Edit service ⛽",
    },
    "profile_info": {
        "it": "Profilo:\nCarburante: {fuel}\nServizio: {service}\nLingua: {language}",
        "en": "Profile:\nFuel: {fuel}\nService: {service}\nLanguage: {language}",
    },

    # ─────────── /help ───────────
    "help": {
        "it": (
            "/start – configura il profilo\n"
            "/find – cerca i distributori più economici\n"
            "/favorites – gestisci i preferiti\n"
            "/profile – modifica profilo\n"
            "/help – mostra questo messaggio"
        ),
        "en": (
            "/start – set up your profile\n"
            "/find – cheapest stations nearby\n"
            "/favorites – manage favourites\n"
            "/profile – edit profile\n"
            "/help – show this message"
        ),
    },

    # ─────────── generics ───────────
    "use_commands": {
        "it": "⛔ Usa i comandi, per favore",
        "en": "⛔ Please use commands",
    },
}


def t(key: str, lang: str) -> str:
    """Return translated message for `key` in `lang`."""
    return MSG.get(key, {}).get(lang, MSG.get(key, {}).get(DEFAULT_LANGUAGE, ""))
