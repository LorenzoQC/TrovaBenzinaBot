from config import DEFAULT_LANGUAGE

# Message keys
MSG = {
    "ask_language_choice": {
        "it": "Seleziona lingua 🌐️",
        "en": "Choose language 🌐",
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
        "it": "✅ Profilo salvato con successo",
        "en": "✅ Profile saved successfully",
    },
    "use_commands": {
        "it": "⛔ Usa i comandi per favore",
        "en": "⛔ Please use the commands",
    },
    "edit_fuel": {
        "it": "Modifica carburante 🛢️",
        "en": "Edit fuel 🛢️",
    },
    "edit_service": {
        "it": "Modifica servizio ⛽",
        "en": "Edit service ⛽",
    },
    "edit_language": {
        "it": "Modifica lingua 🌐️",
        "en": "Edit language 🌐",
    },
    "profile_info": {
        "it": "Profilo:\nCarburante: {fuel}\nServizio: {service}\nLingua: {language}",
        "en": "Profile:\nFuel: {fuel}\nService: {service}\nLanguage: {language}",
    },
    "send_location": {
        "it": "Invia posizione 📍",
        "en": "Send location 📍",
    },
    "favorites": {
        "it": "Preferiti ⭐",
        "en": "Favorites ⭐",
    },
    "ask_location": {
        "it": "➤ Invia posizione o scegli un preferito",
        "en": "➤ Send location or choose a favorite",
    },
    "invalid_address": {
        "it": "⚠️ Indirizzo non valido",
        "en": "⚠️ Invalid address",
    },
    "no_favorites": {
        "it": "Nessun preferito",
        "en": "No favorites"
    },
    "choose_favorite": {
        "it": "Seleziona preferito",
        "en": "Choose favorites"
    },
    "ask_fav_name": {
        "it": "Assegna un nome a questo preferito",
        "en": "Give a name for this favorite",
    },
    "ask_fav_location": {
        "it": "Invia posizione o indirizzo per il preferito",
        "en": "Send location or address for the favorite",
    },
    "no_stations": {
        "it": "❌ Nessun distributore trovato",
        "en": "❌ No station found"
    },
    "no_address": {

    },
    "primary_result": {

    },
    "secondary_result": {

    }
}


def t(key: str, lang: str) -> str:
    """Return translated message for `key` in `lang`."""
    return MSG.get(key, {}).get(lang, MSG[key][DEFAULT_LANGUAGE])
