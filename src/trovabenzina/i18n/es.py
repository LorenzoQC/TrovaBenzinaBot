# ES - Español
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "es",
    "language_name": "Español",
    "gasoline": "Gasolina",
    "diesel": "Diésel",
    "cng": "GNC",
    "lpg": "GLP",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Seleccionar idioma 🌐️",
    "invalid_language": "⚠️ Idioma no válido!",
    "select_fuel": "Seleccionar combustible ⛽",
    "invalid_fuel": "⚠️ Combustible no válido!",
    "profile_saved": "✅ Perfil guardado con éxito!\n\nUsa /search para iniciar una búsqueda.",
    "user_already_registered": "⚠️ Usuario ya registrado!\n\nUsa /profile para modificar las preferencias o /search para iniciar una búsqueda.",

    # ─────────── /help ───────────
    "help": (
        "/start – configurar tu perfil\n"
        "/search – buscar las estaciones más baratas\n"
        "/profile – modificar tu perfil\n"
        "/help – mostrar este mensaje"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Idioma",
    "fuel": "⛽ Combustible",
    "edit_language": "Editar idioma 🌐️",
    "edit_fuel": "Editar combustible ⛽",
    "language_updated": "✅ Idioma actualizado con éxito!",
    "fuel_updated": "✅ Combustible actualizado con éxito!",

    # ─────────── /search ───────────
    "ask_location": "Escribe una dirección o envía tu ubicación 📍",
    "send_location": "Enviar ubicación GPS 🌍",
    "geocode_cap_reached": "⚠️ ¡Reconocimiento de direcciones no disponible en este momento!\nPor favor, inténtalo más tarde o envía tu ubicación.",
    "invalid_address": "⚠️ Dirección no válida",
    "processing_search": "Buscando...🔍",
    "no_stations": "❌ No se encontraron estaciones",
    "near_label": "Estaciones en un radio de 2 km",
    "far_label": "Estaciones en un radio de 7 km",
    "stations_analyzed": "estaciones analizadas",
    "average_zone_price": "Precio medio de la zona",
    "address": "Dirección",
    "no_address": "-",
    "price": "Precio",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "más barato que el promedio",
    "equal_average": "igual al promedio",
    "last_update": "Última actualización",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ ¡No hay estadísticas disponibles!\\n\\nUsa /search para iniciar una búsqueda.",
    "statistics": (
        "<b><u>Estadísticas {fuel_name}</u></b> 📊\\n"
        "<b>{num_searches} búsquedas</b> realizadas.\\n"
        "<b>{num_stations} estaciones</b> analizadas.\\n"
        "Ahorro medio: <b>{avg_eur_save_per_unit} {price_unit}</b>, es decir, <b>{avg_pct_save}%</b>.\\n"
        "Ahorro anual estimado: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>ℹ️ ¿Cómo se calculan estas cifras?</i>\\n"
                       "• El ahorro medio asume repostar siempre en la estación más barata que propone el bot en comparación con el precio medio de la zona.\\n"
                       "• El ahorro anual asume 10 000 km al año con un consumo medio de:\\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} cada 100 km",
    "reset_statistics": "Restablecer estadísticas ♻️",
    "statistics_reset": "✅ Estadísticas restablecidas correctamente!\\n\\nUsa /search para iniciar una búsqueda.",

}
