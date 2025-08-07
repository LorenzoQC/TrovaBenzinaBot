# JA - 日本語
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "ja",
    "language_name": "日本語",
    "gasoline": "ガソリン",
    "diesel": "ディーゼル",
    "cng": "CNG",
    "lpg": "LPG",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "言語を選択 🌐️",
    "invalid_language": "⚠️ 無効な言語です！",
    "select_fuel": "燃料を選択 ⛽",
    "invalid_fuel": "⚠️ 無効な燃料です！",
    "profile_saved": "✅ プロファイルが正常に保存されました！\n\n/search を使用して検索を開始します。",
    "user_already_registered": "⚠️ 既に登録済みです！\n\n/profile で設定を変更するか /search で検索を開始します。",

    # ─────────── /help ───────────
    "help": (
        "/start – プロファイルを設定する\n"
        "/search – 最安値のガソリンスタンドを検索する\n"
        "/profile – プロファイルを編集する\n"
        "/help – このメッセージを表示する"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ 言語",
    "fuel": "⛽ 燃料",
    "edit_language": "言語を編集 🌐️",
    "edit_fuel": "燃料を編集 ⛽",
    "language_updated": "✅ 言語が正常に更新されました！",
    "fuel_updated": "✅ 燃料が正常に更新されました！",

    # ─────────── /search ───────────
    "ask_location": "住所を入力するか位置情報を送信してください 📍",
    "send_location": "GPS 位置情報を送信 🌍",
    "geocode_cap_reached": "⚠️ 現在アドレス認識を利用できません！\n後でもう一度試すか、位置情報を送信してください。",
    "invalid_address": "⚠️ 無効な住所",
    "processing_search": "検索中...🔍",
    "no_stations": "❌ スタンドが見つかりません",
    "near_label": "2km以内のスタンド",
    "far_label": "7km以内のスタンド",
    "stations_analyzed": "スタンドを分析しました",
    "average_zone_price": "エリアの平均価格",
    "address": "住所",
    "no_address": "-",
    "price": "価格",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "平均より安い",
    "equal_average": "平均と同じ",
    "last_update": "最終更新",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ 統計データがありません！\n\n/search で検索を開始してください。",
    "statistics": (
        "<b><u>{fuel_name} の統計</u></b> 📊\n"
        "<b>{num_searches} 件の検索</b> が行われました。\n"
        "<b>{num_stations} 箇所のスタンド</b> が分析されました。\n"
        "平均節約額：<b>{avg_eur_save_per_unit} {price_unit}</b>、つまり <b>{avg_pct_save}%</b>。\n"
        "推定年間節約額：<b>{estimated_annual_save_eur}</b>。"
    ),
    "statistics_info": "<i>ℹ️ これらの数値はどのように計算されていますか？</i>\n"
                       "• 平均節約額は、常にボットが提案する最安値のスタンドで給油した場合とエリア平均価格を比較して算出しています。\n"
                       "• 年間節約額は、年間 10,000 km を平均消費量で走行した場合を想定して算出しています。\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} /100km あたり",
    "reset_statistics": "統計をリセット ♻️",
    "statistics_reset": "✅ 統計がリセットされました！\n\n/search で再度検索を開始してください。",

}
