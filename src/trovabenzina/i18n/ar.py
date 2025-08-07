# AR - العربية
TRANSLATIONS = {
    # ─────────── config ───────────
    "language_code": "ar",
    "language_name": "العربية",
    "gasoline": "بنزين",
    "diesel": "ديزل",
    "cng": "غاز طبيعي مضغوط",
    "lpg": "غاز البترول المسال",
    "liter_symbol": "ل",
    "kilo_symbol": "كغ",

    # ─────────── /start ───────────
    "select_language": "اختر اللغة 🌐️",
    "invalid_language": "⚠️ لغة غير صالحة!",
    "select_fuel": "اختر الوقود ⛽",
    "invalid_fuel": "⚠️ وقود غير صالح!",
    "profile_saved": "✅ تم حفظ الملف الشخصي بنجاح!\n\nاستخدم /search لبدء البحث.",
    "user_already_registered": "⚠️ المستخدم مسجل بالفعل!\n\nاستخدم /profile لتعديل التفضيلات أو /search لبدء البحث.",

    # ─────────── /help ───────────
    "help": (
        "/start – إعداد ملفك الشخصي\n"
        "/search – البحث عن أرخص المحطات\n"
        "/profile – تعديل ملفك الشخصي\n"
        "/help – عرض هذه الرسالة"
    ),

    # ─────────── /profile ───────────
    "language": "🌐️ اللغة",
    "fuel": "⛽ الوقود",
    "edit_language": "تعديل اللغة 🌐️",
    "edit_fuel": "تعديل الوقود ⛽",
    "language_updated": "✅ تم تحديث اللغة بنجاح!",
    "fuel_updated": "✅ تم تحديث الوقود بنجاح!",

    # ─────────── /search ───────────
    "ask_location": "اكتب عنوانًا أو أرسل موقعك 📍",
    "send_location": "إرسال الموقع عبر GPS 🌍",
    "geocode_cap_reached": "⚠️ التعرف على العناوين غير متاح حاليًا!\nالرجاء المحاولة لاحقًا أو إرسال موقعك.",
    "invalid_address": "⚠️ عنوان غير صالح",
    "processing_search": "جاري البحث...🔍",
    "no_stations": "❌ لم يتم العثور على محطات",
    "near_label": "المحطات ضمن 2 كم",
    "far_label": "المحطات ضمن 7 كم",
    "stations_analyzed": "محطات تم تحليلها",
    "average_zone_price": "متوسط سعر المنطقة",
    "address": "العنوان",
    "no_address": "-",
    "price": "السعر",
    "eur_symbol": "€",
    "slash_symbol": "/\u200b",
    "below_average": "أرخص من المتوسط",
    "equal_average": "مطابق للمتوسط",
    "last_update": "آخر تحديث",

    # ─────────── /statistics ───────────
    "no_statistics": "⚠️ لا توجد إحصائيات متاحة!\n\nاستخدم /find لبدء البحث.",
    "statistics": (
        "<b><u>إحصائيات {fuel_name}</u></b> 📊\n"
        "<b>{num_searches} عمليات بحث</b> تمت.\n"
        "<b>{num_stations} محطة</b> تم تحليلها.\n"
        "المتوسط الموفر: <b>{avg_eur_save_per_unit} {price_unit}</b>، أي <b>{avg_pct_save}%</b>.\n"
        "التوفير السنوي التقديري: <b>{estimated_annual_save_eur}</b>."
    ),
    "statistics_info": "<i>ℹ️ كيف تم حساب هذه الأرقام؟</i>\n"
                       "• المتوسط الموفر محسوب على افتراض أنك دائمًا تعبئ عند أرخص محطة يقترحها البوت مقارنة بالسعر المتوسط للمنطقة.\n"
                       "• التوفير السنوي محسوب على افتراض 10,000 كم سنويًا مع متوسط استهلاك:\n",
    "fuel_consumption": "  - {fuel_name} = {avg_consumption_per_100km}{uom} لكل 100 كم",
    "reset_statistics": "إعادة تعيين الإحصائيات ♻️",
    "statistics_reset": "✅ تم إعادة تعيين الإحصائيات بنجاح!\n\nاستخدم /find لبدء البحث.",

}
