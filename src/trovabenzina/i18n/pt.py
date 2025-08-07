# PT - Português
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "pt",
    "language_name": "Português",
    "gasoline": "Gasolina",
    "diesel": "Diesel",
    "cng": "GNC",
    "lpg": "GLP",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Selecionar idioma 🌐️",
    "invalid_language": "⚠️ Idioma inválido!",
    "select_fuel": "Selecionar combustível ⛽",
    "invalid_fuel": "⚠️ Combustível inválido!",
    "profile_saved": "✅ Perfil salvo com sucesso!\n\nUse /search para iniciar uma busca.",
    "user_already_registered": "⚠️ Usuário já registrado!\n\nUse /profile para modificar preferências ou /search para iniciar uma busca.",

    # ─────────── /help ───────────
    "help": (
        "/start – configurar seu perfil\n"
        "/search – buscar os postos mais baratos\n"
        "/profile – modificar seu perfil\n"
        "/help – mostrar esta mensagem"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ Idioma",
    "fuel": "⛽ Combustível",
    "edit_language": "Editar idioma 🌐️",
    "edit_fuel": "Editar combustível ⛽",
    "language_updated": "✅ Idioma atualizado com sucesso!",
    "fuel_updated": "✅ Combustível atualizado com sucesso!",

    # ─────────── /search ───────────
    "ask_location": "Digite um endereço ou envie sua localização 📍",
    "send_location": "Enviar localização GPS 🌍",
    "geocode_cap_reached": "⚠️ Reconhecimento de endereço indisponível no momento!\nPor favor, tente novamente mais tarde ou envie sua localização.",
    "invalid_address": "⚠️ Endereço inválido",
    "processing_search": "Pesquisando...🔍",
    "no_stations": "❌ Nenhum posto encontrado",
    "near_label": "Postos dentro de 2 km",
    "far_label": "Postos dentro de 7 km",
    "stations_analyzed": "postos analisados",
    "average_zone_price": "Preço médio da área",
    "address": "Endereço",
    "no_address": "-",
    "price": "Preço",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "mais barato que a média",
    "equal_average": "em linha com a média",
    "last_update": "Última atualização",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Nenhuma estatística disponível!\n\nUse /search para iniciar uma busca.",
    "statistics": (
        "<b><u>Estatísticas {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} buscas</b> realizadas.\n"
        "<b>{num_stations} postos</b> analisados.\n"
        "Economia média: <b>{avg_eur_save_per_unit} {price_unit}</b>, ou <b>{avg_pct_save}%</b>.\n"
        "Economia anual estimada: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>ℹ️ Como esses números são calculados?</i>\n"
                       "• A economia média assume sempre abastecer no posto mais barato sugerido pelo bot em comparação com o preço médio da área.\n"
                       "• A economia anual assume 10.000 km por ano com consumo médio de:\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} por 100 km",
    "reset_statistics": "Redefinir estatísticas ♻️",
    "statistics_reset": "✅ Estatísticas redefinidas com sucesso!\n\nUse /search para iniciar uma busca.",


}
