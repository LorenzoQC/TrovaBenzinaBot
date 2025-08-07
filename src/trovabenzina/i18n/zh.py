# ZH - 中文
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "zh",
    "language_name": "中文",
    "gasoline": "汽油",
    "diesel": "柴油",
    "cng": "压缩天然气",
    "lpg": "液化石油气",
    "liter_symbol": "L",
    "kilo_symbol": "kg",

    # ─────────── /start ───────────
    "select_language": "选择语言 🌐️",
    "invalid_language": "⚠️ 无效的语言！",
    "select_fuel": "选择燃料 ⛽",
    "invalid_fuel": "⚠️ 无效的燃料！",
    "profile_saved": "✅ 配置文件已成功保存！\n\n使用 /search 开始搜索。",
    "user_already_registered": "⚠️ 用户已注册！\n\n使用 /profile 修改偏好或 /search 开始搜索。",

    # ─────────── /help ───────────
    "help": (
        "/start – 设置您的配置文件\n"
        "/search – 搜索最便宜的加油站\n"
        "/profile – 修改您的配置文件\n"
        "/help – 显示此消息"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ 语言",
    "fuel": "⛽ 燃料",
    "edit_language": "编辑语言 🌐️",
    "edit_fuel": "编辑燃料 ⛽",
    "language_updated": "✅ 语言更新成功！",
    "fuel_updated": "✅ 燃料更新成功！",

    # ─────────── /search ───────────
    "ask_location": "输入地址或发送您的位置 📍",
    "send_location": "发送 GPS 位置 🌍",
    "geocode_cap_reached": "⚠️ 地址识别暂不可用！\n请稍后再试或发送您的位置。",
    "invalid_address": "⚠️ 无效地址",
    "processing_search": "搜索中...🔍",
    "no_stations": "❌ 未找到加油站",
    "near_label": "2 公里范围内的加油站",
    "far_label": "7 公里范围内的加油站",
    "stations_analyzed": "已分析加油站",
    "average_zone_price": "区域平均价格",
    "address": "地址",
    "no_address": "-",
    "price": "价格",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "低于平均水平",
    "equal_average": "与平均水平持平",
    "last_update": "最后更新",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ 暂无可用统计数据！\n\n使用 /search 开启一次搜索。",
    "statistics": (
        "<b><u>{fuel_name} 统计</u></b> 📊\n"
        "<b>共进行 {num_searches} 次搜索</b>。\n"
        "<b>分析了 {num_stations} 个加油站</b>。\n"
        "平均节省：<b>{avg_eur_save_per_unit} {price_unit}</b>，即 <b>{avg_pct_save}%</b>。\n"
        "预计年节省：<b>{estimated_annual_save_eur}</b>。"
    ),
    "statistics_info": "<i>ℹ️ 这些数据如何计算？</i>\n"
                       "• 平均节省基于始终在 bot 推荐的最便宜加油站加油，与区域平均价格对比。\n"
                       "• 年节省基于每年行驶 10,000 公里，平均油耗为：\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} 每 100 公里",
    "reset_statistics": "重置统计数据 ♻️",
    "statistics_reset": "✅ 统计数据已重置！\n\n使用 /search 开启一次搜索。",
}
