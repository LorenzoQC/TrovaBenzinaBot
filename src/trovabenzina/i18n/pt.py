# PT - Português
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "pt",
    "language_name": "Português",
    "gasoline": "Gasolina",
    "diesel": "Gasóleo",
    "cng": "GNV",
    "lpg": "GLP",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "Selecionar idioma 🌐️",
    "invalid_language": "⚠️ Idioma inválido!",
    "select_fuel": "Selecionar combustível ⛽",
    "invalid_fuel": "⚠️ Combustível inválido!",
    "profile_saved": "✅ Perfil salvo com sucesso!\n\nUse o comando /search para iniciar uma busca.",
    "user_already_registered": "⚠️ Usuário já registrado!\n\nUse o comando /profile para alterar as preferências ou o comando /search para iniciar uma busca.",

    # ─────────── /help ───────────
    "help": (
        "🚀 /start – iniciar o bot e configurar o perfil\n"
        "🔍 /search – buscar os postos mais baratos\n"
        "👤 /profile – ver e editar suas configurações\n"
        "📊 /statistics – ver suas estatísticas\n"
        "📢 /help – mostrar esta mensagem\n\n"
    ),
    "disclaimer": (
        "ℹ️ Dados dos postos fornecidos pelo <b>Ministério das Empresas e do Made in Italy (MISE)</b>.\n"
        "Não se garante a precisão ou a atualização das informações exibidas pelo bot."
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
    "geocode_cap_reached": "⚠️ Reconhecimento de endereço indisponível no momento!\n\nTente novamente mais tarde, ou envie sua localização.",
    "invalid_address": "⚠️ Endereço inválido!\n\nDigite outro endereço ou envie sua localização.",
    "processing_search": "Busca em andamento.🔍",
    "please_wait": "Processando, aguarde um instante.⏳",
    "no_stations": "❌ Nenhum posto encontrado",
    "area_label": "Postos num raio de {radius} km",
    "stations_analyzed": "postos analisados",
    "average_zone_price": "Preço médio de {fuel_name} na zona",
    "address": "Endereço",
    "no_address": "-",
    "price": "Preço",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "mais barato que a média",
    "equal_average": "em linha com a média",
    "last_update": "Última atualização",
    "btn_narrow": "Repetir busca com raio de {radius} km 🔄",
    "btn_widen": "Repetir busca com raio de {radius} km 🔄",
    "search_session_expired": "⚠️ Sessão expirada!\n\nUse o comando /search para iniciar uma nova busca.",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ Nenhuma estatística disponível!\n\nUse o comando /search para iniciar uma busca.",
    "statistics": (
        "<b><u>Estatísticas {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} buscas</b> realizadas.\n"
        "<b>{num_stations} postos</b> analisados.\n"
        "Economia média: <b>{avg_eur_save_per_unit} {price_unit}</b>, ou <b>{avg_pct_save}%</b>.\n"
        "Economia anual estimada: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>❓ Como calculamos estes números?</i>\n"
                       "• A economia média é a média, em todas as buscas, da diferença entre o preço médio da zona e o preço do posto mais barato encontrado pelo bot.\n"
                       "• A economia anual considera 10.000km por ano com um consumo médio de: \n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} por 100km",
    "reset_statistics": "Redefinir estatísticas ♻️",
    "statistics_reset": "✅ Estatísticas redefinidas com sucesso!\n\nUse o comando /search para iniciar uma busca.",

}
