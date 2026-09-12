import os
import io
import sqlite3
import threading
from datetime import datetime, date
from zoneinfo import ZoneInfo
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputFile
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)


# ============================================================
# CONFIGURATION
# ============================================================

# توکن ربات: اولویت با متغیر محیطی BOT_TOKEN (در سرور یا فایل .env) است
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8644365577:AAG8u6IaL0XESA_mfBWmdn-7sJo_C13qtSo")

# لیست ادمین‌ها: می‌تواند شامل شناسه عددی تلگرام یا نام کاربری (با یا بدون @) باشد
# همچنین از متغیر محیطی ADMIN_USERS (جداشده با کاما) در سرور Render پشتیبانی می‌کند
ADMIN_USERS = [
    "alirezaaghdasii",
]

ADMIN_USERNAME = "alirezaaghdasii"  # جهت سازگاری

# لیست کاربران مجاز به ثبت صندوق: شامل شناسه عددی تلگرام یا نام کاربری
# (توجه: کلیه ادمین‌ها به صورت خودکار مجاز هستند)
# همچنین از متغیر محیطی ALLOWED_USERS (جداشده با کاما) در سرور Render پشتیبانی می‌کند
ALLOWED_USERS = [
    "alirezaaghdasii",
]

# سه شعبه واقعی
BRANCHES = [
    "Ludwigshafen",
    "Mittel",
    "T1"
]

# زمان آلمان
GERMANY_TZ = ZoneInfo("Europe/Berlin")


# ============================================================
# DATABASE
# ============================================================

# اگر Render Persistent Disk روی /data تنظیم شده باشد،
# دیتابیس اینجا ذخیره می‌شود و بعد از Restart باقی می‌ماند.
#
# اگر /data وجود نداشته باشد، کنار فایل برنامه ذخیره می‌شود.
# روی Render بدون Persistent Disk ممکن است با Redeploy/Restart پاک شود.

if os.path.exists("/data"):
    DB_PATH = "/data/kasse.db"
else:
    DB_PATH = "kasse.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            branch TEXT NOT NULL,
            shift TEXT NOT NULL,
            amount REAL NOT NULL,
            user TEXT NOT NULL,
            telegram_user_id INTEGER
        )
    """)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# DUMMY WEB SERVER FOR RENDER
# ============================================================

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, format, *args):
        return


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(
        ("0.0.0.0", port),
        SimpleHTTPRequestHandler
    )
    server.serve_forever()


threading.Thread(
    target=run_web_server,
    daemon=True
).start()


# ============================================================
# TRANSLATIONS
# ============================================================

LANGUAGES = {

    "fa": {
        "name": "🇮🇷 فارسی",

        "choose_branch": "لطفاً شعبه مورد نظر را انتخاب کنید:",
        "welcome": "سلام {name} عزیز! به سیستم ثبت صندوق خوش آمدید.",
        "main_menu": "منوی اصلی:",

        "btn_register": "➕ ثبت صندوق جدید",
        "btn_report": "📊 گزارش صندوق",
        "btn_excel": "📥 دریافت فایل اکسل",
        "btn_lang": "🌐 تغییر زبان",

        "choose_shift": "نوبت صندوق را انتخاب کنید:",

        "shift_1": "صندوق ۱ (۱۸:۰۰)",
        "shift_2": "صندوق ۲ (۲۴:۰۰)",
        "shift_3": "صندوق ۳ (پایان کار)",

        "enter_amount":
            "لطفاً مبلغ {shift} را به یورو وارد کنید:\n"
            "مثلاً: 450.50",

        "invalid_amount":
            "❌ مبلغ وارد شده معتبر نیست.\n"
            "لطفاً فقط عدد وارد کنید، مثلاً 450.50",

        "success_reg":
            "✅ صندوق با موفقیت ثبت شد!\n\n"
            "📅 تاریخ: {date}\n"
            "⏰ ساعت: {time}\n"
            "📍 شعبه: {branch}\n"
            "📦 صندوق: {shift}\n"
            "💰 مبلغ: €{amount:.2f}\n"
            "👤 ثبت‌کننده: {user}",

        "report_menu":
            "نوع گزارش را انتخاب کنید:",

        "btn_summary":
            "📊 گزارش کلی",

        "btn_detail":
            "📋 گزارش جزئی",

        "btn_all_branches":
            "🏢 هر سه شعبه",

        "btn_back":
            "🔙 بازگشت",

        "ask_start_date":
            "📅 تاریخ شروع را وارد کنید:\n"
            "فرمت: DD.MM.YYYY\n"
            "مثال: 01.09.2026",

        "ask_end_date":
            "📅 تاریخ پایان را وارد کنید:\n"
            "فرمت: DD.MM.YYYY\n"
            "مثال: 10.09.2026",

        "invalid_date":
            "❌ تاریخ نامعتبر است.\n"
            "فرمت صحیح: DD.MM.YYYY\n"
            "مثال: 01.09.2026",

        "choose_report_branch":
            "🏢 شعبه مورد نظر را انتخاب کنید:",

        "summary_title":
            "📊 گزارش کلی\n"
            "📅 از {start} تا {end}\n\n",

        "branch_title":
            "🏢 شعبه: {branch}\n\n",

        "user_summary":
            "👤 {user}\n"
            "📦 تعداد صندوق: {count}\n"
            "💰 مجموع: €{total:.2f}\n\n",

        "grand_total":
            "━━━━━━━━━━━━━━\n"
            "📦 تعداد کل صندوق‌ها: {count}\n"
            "💰 جمع کل: €{total:.2f}",

        "detail_title":
            "📋 گزارش جزئی\n"
            "📅 از {start} تا {end}\n\n",

        "detail_item":
            "📅 {date}  ⏰ {time}\n"
            "🏢 {branch}\n"
            "📦 {shift}\n"
            "💰 €{amount:.2f}\n"
            "👤 {user}\n"
            "────────────\n",

        "no_records":
            "هیچ رکوردی در این بازه پیدا نشد.",

        "excel_caption":
            "📊 گزارش صندوق‌ها برای بازه انتخاب‌شده",

        "back_main":
            "🔙 به منوی اصلی برگشتید.",

        "branches":
            BRANCHES
    },


    "de": {
        "name": "🇩🇪 Deutsch",

        "choose_branch": "Bitte wählen Sie die Filiale:",
        "welcome": "Hallo {name}! Willkommen beim Kassenbuch-System.",
        "main_menu": "Hauptmenü:",

        "btn_register": "➕ Neue Kasse eingeben",
        "btn_report": "📊 Kassenbericht",
        "btn_excel": "📥 Excel-Datei herunterladen",
        "btn_lang": "🌐 Sprache ändern",

        "choose_shift": "Bitte Kasse wählen:",

        "shift_1": "Kasse 1 (18:00)",
        "shift_2": "Kasse 2 (24:00)",
        "shift_3": "Kasse 3 (Feierabend)",

        "enter_amount":
            "Bitte Betrag für {shift} in Euro eingeben:\n"
            "z.B. 450.50",

        "invalid_amount":
            "❌ Ungültiger Betrag.\n"
            "Bitte nur Zahlen eingeben, z.B. 450.50",

        "success_reg":
            "✅ Kasse erfolgreich gespeichert!\n\n"
            "📅 Datum: {date}\n"
            "⏰ Uhrzeit: {time}\n"
            "📍 Filiale: {branch}\n"
            "📦 Kasse: {shift}\n"
            "💰 Betrag: €{amount:.2f}\n"
            "👤 Benutzer: {user}",

        "report_menu": "Berichtsart auswählen:",

        "btn_summary": "📊 Gesamtbericht",
        "btn_detail": "📋 Detailbericht",
        "btn_all_branches": "🏢 Alle Filialen",
        "btn_back": "🔙 Zurück",

        "ask_start_date":
            "📅 Startdatum eingeben:\n"
            "Format: DD.MM.YYYY\n"
            "Beispiel: 01.09.2026",

        "ask_end_date":
            "📅 Enddatum eingeben:\n"
            "Format: DD.MM.YYYY\n"
            "Beispiel: 10.09.2026",

        "invalid_date":
            "❌ Ungültiges Datum.\n"
            "Format: DD.MM.YYYY",

        "choose_report_branch":
            "🏢 Filiale auswählen:",

        "summary_title":
            "📊 Gesamtbericht\n"
            "📅 {start} bis {end}\n\n",

        "branch_title":
            "🏢 Filiale: {branch}\n\n",

        "user_summary":
            "👤 {user}\n"
            "📦 Anzahl Kassen: {count}\n"
            "💰 Gesamt: €{total:.2f}\n\n",

        "grand_total":
            "━━━━━━━━━━━━━━\n"
            "📦 Kassen insgesamt: {count}\n"
            "💰 Gesamtsumme: €{total:.2f}",

        "detail_title":
            "📋 Detailbericht\n"
            "📅 {start} bis {end}\n\n",

        "detail_item":
            "📅 {date}  ⏰ {time}\n"
            "🏢 {branch}\n"
            "📦 {shift}\n"
            "💰 €{amount:.2f}\n"
            "👤 {user}\n"
            "────────────\n",

        "no_records": "Keine Einträge für diesen Zeitraum.",

        "excel_caption":
            "📊 Kassenbericht für den ausgewählten Zeitraum",

        "back_main": "🔙 Zurück zum Hauptmenü.",

        "branches": BRANCHES
    },


    "tr": {
        "name": "🇹🇷 Türkçe",

        "choose_branch": "Lütfen şubeyi seçin:",
        "welcome": "Merhaba {name}! Kasa kayıt sistemine hoş geldiniz.",
        "main_menu": "Ana Menü:",

        "btn_register": "➕ Yeni Kasa Ekle",
        "btn_report": "📊 Kasa Raporu",
        "btn_excel": "📥 Excel Dosyası İndir",
        "btn_lang": "🌐 Dili Değiştir",

        "choose_shift": "Kasa seçin:",

        "shift_1": "Kasa 1 (18:00)",
        "shift_2": "Kasa 2 (24:00)",
        "shift_3": "Kasa 3 (Kapanış)",

        "enter_amount":
            "Lütfen {shift} miktarını Euro olarak girin:\n"
            "Örnek: 450.50",

        "invalid_amount":
            "❌ Geçersiz miktar.\n"
            "Lütfen sadece sayı girin.",

        "success_reg":
            "✅ Kasa başarıyla kaydedildi!\n\n"
            "📅 Tarih: {date}\n"
            "⏰ Saat: {time}\n"
            "📍 Şube: {branch}\n"
            "📦 Kasa: {shift}\n"
            "💰 Miktar: €{amount:.2f}\n"
            "👤 Kaydeden: {user}",

        "report_menu": "Rapor türünü seçin:",

        "btn_summary": "📊 Genel Rapor",
        "btn_detail": "📋 Detaylı Rapor",
        "btn_all_branches": "🏢 Tüm Şubeler",
        "btn_back": "🔙 Geri",

        "ask_start_date":
            "📅 Başlangıç tarihini girin:\n"
            "Format: DD.MM.YYYY",

        "ask_end_date":
            "📅 Bitiş tarihini girin:\n"
            "Format: DD.MM.YYYY",

        "invalid_date":
            "❌ Geçersiz tarih.\n"
            "Format: DD.MM.YYYY",

        "choose_report_branch":
            "🏢 Şubeyi seçin:",

        "summary_title":
            "📊 Genel Rapor\n"
            "📅 {start} - {end}\n\n",

        "branch_title":
            "🏢 Şube: {branch}\n\n",

        "user_summary":
            "👤 {user}\n"
            "📦 Kasa sayısı: {count}\n"
            "💰 Toplam: €{total:.2f}\n\n",

        "grand_total":
            "━━━━━━━━━━━━━━\n"
            "📦 Toplam kasa: {count}\n"
            "💰 Genel toplam: €{total:.2f}",

        "detail_title":
            "📋 Detaylı Rapor\n"
            "📅 {start} - {end}\n\n",

        "detail_item":
            "📅 {date}  ⏰ {time}\n"
            "🏢 {branch}\n"
            "📦 {shift}\n"
            "💰 €{amount:.2f}\n"
            "👤 {user}\n"
            "────────────\n",

        "no_records": "Bu tarih aralığında kayıt bulunamadı.",

        "excel_caption":
            "📊 Seçilen tarih aralığı için kasa raporu",

        "back_main": "🔙 Ana menüye dönüldü.",

        "branches": BRANCHES
    },


    "ar": {
        "name": "🇸🇦 العربية",

        "choose_branch": "الرجاء اختيار الفرع:",
        "welcome": "مرحباً {name}! أهلاً بك في نظام تسجيل الصندوق.",
        "main_menu": "القائمة الرئيسية:",

        "btn_register": "➕ تسجيل صندوق جديد",
        "btn_report": "📊 تقرير الصندوق",
        "btn_excel": "📥 تحميل ملف إكسل",
        "btn_lang": "🌐 تغيير اللغة",

        "choose_shift": "اختر الصندوق:",

        "shift_1": "صندوق ۱ (۱۸:۰۰)",
        "shift_2": "صندوق ۲ (۲۴:۰۰)",
        "shift_3": "صندوق ۳ (الإغلاق)",

        "enter_amount":
            "الرجاء إدخال مبلغ {shift} باليورو:\n"
            "مثال: 450.50",

        "invalid_amount":
            "❌ المبلغ غير صحيح.\n"
            "الرجاء إدخال أرقام فقط.",

        "success_reg":
            "✅ تم تسجيل الصندوق بنجاح!\n\n"
            "📅 التاريخ: {date}\n"
            "⏰ الوقت: {time}\n"
            "📍 الفرع: {branch}\n"
            "📦 الصندوق: {shift}\n"
            "💰 المبلغ: €{amount:.2f}\n"
            "👤 بواسطة: {user}",

        "report_menu": "اختر نوع التقرير:",

        "btn_summary": "📊 التقرير الإجمالي",
        "btn_detail": "📋 التقرير التفصيلي",
        "btn_all_branches": "🏢 جميع الفروع",
        "btn_back": "🔙 رجوع",

        "ask_start_date":
            "📅 أدخل تاريخ البداية:\n"
            "الصيغة: DD.MM.YYYY",

        "ask_end_date":
            "📅 أدخل تاريخ النهاية:\n"
            "الصيغة: DD.MM.YYYY",

        "invalid_date":
            "❌ التاريخ غير صحيح.\n"
            "الصيغة: DD.MM.YYYY",

        "choose_report_branch":
            "🏢 اختر الفرع:",

        "summary_title":
            "📊 التقرير الإجمالي\n"
            "📅 من {start} إلى {end}\n\n",

        "branch_title":
            "🏢 الفرع: {branch}\n\n",

        "user_summary":
            "👤 {user}\n"
            "📦 عدد الصناديق: {count}\n"
            "💰 المجموع: €{total:.2f}\n\n",

        "grand_total":
            "━━━━━━━━━━━━━━\n"
            "📦 إجمالي الصناديق: {count}\n"
            "💰 المجموع الكلي: €{total:.2f}",

        "detail_title":
            "📋 التقرير التفصيلي\n"
            "📅 من {start} إلى {end}\n\n",

        "detail_item":
            "📅 {date}  ⏰ {time}\n"
            "🏢 {branch}\n"
            "📦 {shift}\n"
            "💰 €{amount:.2f}\n"
            "👤 بواسطة: {user}\n"
            "────────────\n",

        "no_records": "لا توجد سجلات في هذه الفترة.",

        "excel_caption":
            "📊 تقرير الصندوق للفترة المحددة",

        "back_main": "🔙 تم الرجوع إلى القائمة الرئيسية.",

        "branches": BRANCHES
    }
}


# ============================================================
# CONVERSATION STATES
# ============================================================

(
    SELECT_LANG,
    SELECT_BRANCH,
    MAIN_MENU,
    SELECT_SHIFT,
    ENTER_AMOUNT,
    REPORT_TYPE,
    REPORT_START_DATE,
    REPORT_END_DATE,
    REPORT_BRANCH,
    EXCEL_START_DATE,
    EXCEL_END_DATE,
    EXCEL_BRANCH
) = range(12)


# ============================================================
# USER HELPERS
# ============================================================

USER_LANGS = {}


def _normalize_identifier(val):
    if val is None:
        return ""
    return str(val).strip().lstrip("@").lower()


def get_all_admin_identifiers():
    admins = set(_normalize_identifier(x) for x in ADMIN_USERS if x is not None)
    if ADMIN_USERNAME:
        admins.add(_normalize_identifier(ADMIN_USERNAME))

    env_admins = os.environ.get("ADMIN_USERS", "")
    if env_admins:
        for a in env_admins.split(","):
            norm = _normalize_identifier(a)
            if norm:
                admins.add(norm)
    return admins


def get_all_allowed_identifiers():
    allowed = set(_normalize_identifier(x) for x in ALLOWED_USERS if x is not None)
    # کلیه ادمین‌ها به صورت خودکار مجاز هستند
    allowed.update(get_all_admin_identifiers())

    env_allowed = os.environ.get("ALLOWED_USERS", "")
    if env_allowed:
        for u in env_allowed.split(","):
            norm = _normalize_identifier(u)
            if norm:
                allowed.add(norm)
    return allowed


def is_admin(user_or_username=None, user_id=None):
    """
    بررسی دسترسی ادمین.
    پشتیبانی کامل از آبجکت User تلگرام، آیدی عددی و نام کاربری (با یا بدون @).
    """
    if user_or_username is None and user_id is None:
        return False

    u_name = None
    u_id = user_id

    if hasattr(user_or_username, "id"):
        u_id = user_or_username.id
        u_name = user_or_username.username
    elif isinstance(user_or_username, int):
        u_id = user_or_username
    elif isinstance(user_or_username, str):
        if user_or_username.isdigit():
            u_id = int(user_or_username)
        else:
            u_name = user_or_username

    admin_set = get_all_admin_identifiers()

    if u_id is not None and str(u_id) in admin_set:
        return True

    if u_name and _normalize_identifier(u_name) in admin_set:
        return True

    return False


def is_user_allowed(user_or_username=None, user_id=None):
    """
    بررسی مجاز بودن کاربر جهت ورود و ثبت صندوق.
    پشتیبانی کامل از آبجکت User تلگرام، آیدی عددی و نام کاربری (با یا بدون @).
    """
    if user_or_username is None and user_id is None:
        return False

    if is_admin(user_or_username, user_id):
        return True

    u_name = None
    u_id = user_id

    if hasattr(user_or_username, "id"):
        u_id = user_or_username.id
        u_name = user_or_username.username
    elif isinstance(user_or_username, int):
        u_id = user_or_username
    elif isinstance(user_or_username, str):
        if user_or_username.isdigit():
            u_id = int(user_or_username)
        else:
            u_name = user_or_username

    allowed_set = get_all_allowed_identifiers()

    if u_id is not None and str(u_id) in allowed_set:
        return True

    if u_name and _normalize_identifier(u_name) in allowed_set:
        return True

    return False


def get_menu_keyboard(lang, user_or_username=None):

    keyboard = [
        [LANGUAGES[lang]["btn_register"]]
    ]

    if is_admin(user_or_username):
        keyboard.append([
            LANGUAGES[lang]["btn_report"]
        ])

        keyboard.append([
            LANGUAGES[lang]["btn_excel"]
        ])

    keyboard.append([
        LANGUAGES[lang]["btn_lang"]
    ])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def get_report_type_keyboard(lang):

    keyboard = [
        [LANGUAGES[lang]["btn_summary"]],
        [LANGUAGES[lang]["btn_detail"]],
        [LANGUAGES[lang]["btn_back"]]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def get_branch_keyboard(lang):

    keyboard = [
        [branch]
        for branch in BRANCHES
    ]

    keyboard.append([
        LANGUAGES[lang]["btn_all_branches"]
    ])

    keyboard.append([
        LANGUAGES[lang]["btn_back"]
    ])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def parse_date(date_text):

    try:
        return datetime.strptime(
            date_text.strip(),
            "%d.%m.%Y"
        ).date()

    except ValueError:
        return None


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    if not user:
        return ConversationHandler.END

    if not is_user_allowed(user):
        user_id = user.id
        username_str = f"@{user.username}" if user.username else "ندارد"
        name_str = f"{user.first_name or ''} {user.last_name or ''}".strip() or "کاربر تلگرام"

        await update.message.reply_text(
            f"⛔️ **دسترسی شما مجاز نیست / Access Denied**\n\n"
            f"📋 **اطلاعات حساب تلگرام شما:**\n"
            f"🆔 **شناسه عددی (Telegram ID):** `{user_id}`\n"
            f"👤 **نام کاربری:** {username_str}\n"
            f"🏷 **نام حساب:** {name_str}\n\n"
            f"💡 لطفاً شناسه عددی بالا (`{user_id}`) را کپی کرده و برای مدیر ربات ارسال فرمایید تا دسترسی شما فعال شود.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    user_id = user.id

    if user_id in USER_LANGS:

        return await show_main_menu(
            update,
            context
        )

    keyboard = [
        [
            LANGUAGES["fa"]["name"],
            LANGUAGES["de"]["name"]
        ],
        [
            LANGUAGES["tr"]["name"],
            LANGUAGES["ar"]["name"]
        ]
    ]

    await update.message.reply_text(
        "Please select your language / "
        "لطفاً زبان خود را انتخاب کنید:",

        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

    return SELECT_LANG


# ============================================================
# LANGUAGE
# ============================================================

async def set_language(update, context):

    text = update.message.text

    user_id = update.effective_user.id

    selected_code = "fa"

    for code, lang_data in LANGUAGES.items():

        if lang_data["name"] == text:
            selected_code = code
            break

    USER_LANGS[user_id] = selected_code

    lang = selected_code

    keyboard = [
        [branch]
        for branch in BRANCHES
    ]

    await update.message.reply_text(

        LANGUAGES[lang]["welcome"].format(
            name=update.effective_user.first_name
        )
        + "\n\n"
        + LANGUAGES[lang]["choose_branch"],

        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

    return SELECT_BRANCH


# ============================================================
# BRANCH
# ============================================================

async def select_branch(update, context):

    branch = update.message.text

    if branch not in BRANCHES:

        await update.message.reply_text(
            "❌ شعبه نامعتبر است."
        )

        return SELECT_BRANCH

    context.user_data["branch"] = branch

    return await show_main_menu(
        update,
        context
    )


# ============================================================
# MAIN MENU
# ============================================================

async def show_main_menu(update, context):

    user_id = update.effective_user.id

    username = update.effective_user.username

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    await update.message.reply_text(

        LANGUAGES[lang]["main_menu"],

        reply_markup=get_menu_keyboard(
            lang,
            update.effective_user
        )
    )

    return MAIN_MENU


async def handle_main_menu(update, context):

    user_id = update.effective_user.id

    username = update.effective_user.username

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    text = update.message.text


    # --------------------------------------------------------
    # REGISTER NEW CASH
    # --------------------------------------------------------

    if text in [
        LANGUAGES[l]["btn_register"]
        for l in LANGUAGES
    ]:

        keyboard = [
            [LANGUAGES[lang]["shift_1"]],
            [LANGUAGES[lang]["shift_2"]],
            [LANGUAGES[lang]["shift_3"]]
        ]

        await update.message.reply_text(

            LANGUAGES[lang]["choose_shift"],

            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )

        return SELECT_SHIFT


    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    elif (
        text in [
            LANGUAGES[l]["btn_report"]
            for l in LANGUAGES
        ]
        and is_admin(update.effective_user)
    ):

        await update.message.reply_text(

            LANGUAGES[lang]["report_menu"],

            reply_markup=get_report_type_keyboard(
                lang
            )
        )

        return REPORT_TYPE


    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    elif (
        text in [
            LANGUAGES[l]["btn_excel"]
            for l in LANGUAGES
        ]
        and is_admin(update.effective_user)
    ):

        await update.message.reply_text(
            LANGUAGES[lang]["ask_start_date"]
        )

        return EXCEL_START_DATE


    # --------------------------------------------------------
    # CHANGE LANGUAGE
    # --------------------------------------------------------

    elif text in [
        LANGUAGES[l]["btn_lang"]
        for l in LANGUAGES
    ]:

        keyboard = [
            [
                LANGUAGES["fa"]["name"],
                LANGUAGES["de"]["name"]
            ],
            [
                LANGUAGES["tr"]["name"],
                LANGUAGES["ar"]["name"]
            ]
        ]

        await update.message.reply_text(

            "Please select your language / "
            "لطفاً زبان خود را انتخاب کنید:",

            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )

        return SELECT_LANG


    return MAIN_MENU


# ============================================================
# SELECT SHIFT
# ============================================================

async def select_shift(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    text = update.message.text

    valid_shifts = [
        LANGUAGES[lang]["shift_1"],
        LANGUAGES[lang]["shift_2"],
        LANGUAGES[lang]["shift_3"]
    ]

    if text not in valid_shifts:

        await update.message.reply_text(
            LANGUAGES[lang]["choose_shift"]
        )

        return SELECT_SHIFT

    context.user_data["shift"] = text

    await update.message.reply_text(

        LANGUAGES[lang]["enter_amount"].format(
            shift=text
        ),

        reply_markup=ReplyKeyboardRemove()
    )

    return ENTER_AMOUNT


# ============================================================
# ENTER AMOUNT
# ============================================================

async def enter_amount(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    text = update.message.text.strip()

    try:

        amount = float(
            text.replace(",", ".")
        )

        if amount < 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            LANGUAGES[lang]["invalid_amount"]
        )

        return ENTER_AMOUNT


    now = datetime.now(
        GERMANY_TZ
    )

    user_display = (
        update.effective_user.username
        or update.effective_user.first_name
        or str(user_id)
    )

    branch = context.user_data.get(
        "branch",
        "Ludwigshafen"
    )

    shift = context.user_data.get(
        "shift"
    )


    # --------------------------------------------------------
    # SAVE TO SQLITE
    # --------------------------------------------------------

    conn = get_db()

    conn.execute(
        """
        INSERT INTO records
        (
            date,
            time,
            branch,
            shift,
            amount,
            user,
            telegram_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,

        (
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            branch,
            shift,
            amount,
            user_display,
            user_id
        )
    )

    conn.commit()
    conn.close()


    await update.message.reply_text(

        LANGUAGES[lang]["success_reg"].format(

            date=now.strftime("%d.%m.%Y"),

            time=now.strftime("%H:%M"),

            branch=branch,

            shift=shift,

            amount=amount,

            user=user_display
        )
    )

    return await show_main_menu(
        update,
        context
    )


# ============================================================
# REPORT TYPE
# ============================================================

async def report_type(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    text = update.message.text


    if text == LANGUAGES[lang]["btn_back"]:

        return await show_main_menu(
            update,
            context
        )


    if text == LANGUAGES[lang]["btn_summary"]:

        context.user_data["report_type"] = "summary"

    elif text == LANGUAGES[lang]["btn_detail"]:

        context.user_data["report_type"] = "detail"

    else:

        return REPORT_TYPE


    await update.message.reply_text(
        LANGUAGES[lang]["ask_start_date"]
    )

    return REPORT_START_DATE


# ============================================================
# REPORT START DATE
# ============================================================

async def report_start_date(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    parsed = parse_date(
        update.message.text
    )

    if not parsed:

        await update.message.reply_text(
            LANGUAGES[lang]["invalid_date"]
        )

        return REPORT_START_DATE


    context.user_data["report_start"] = parsed

    await update.message.reply_text(
        LANGUAGES[lang]["ask_end_date"]
    )

    return REPORT_END_DATE


# ============================================================
# REPORT END DATE
# ============================================================

async def report_end_date(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    parsed = parse_date(
        update.message.text
    )

    if not parsed:

        await update.message.reply_text(
            LANGUAGES[lang]["invalid_date"]
        )

        return REPORT_END_DATE


    start = context.user_data["report_start"]

    if parsed < start:

        await update.message.reply_text(
            "❌ تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد."
        )

        return REPORT_END_DATE


    context.user_data["report_end"] = parsed

    await update.message.reply_text(

        LANGUAGES[lang]["choose_report_branch"],

        reply_markup=get_branch_keyboard(
            lang
        )
    )

    return REPORT_BRANCH


# ============================================================
# GENERATE REPORT
# ============================================================

async def report_branch(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    branch_selection = update.message.text


    if branch_selection == LANGUAGES[lang]["btn_back"]:

        return await show_main_menu(
            update,
            context
        )


    if (
        branch_selection not in BRANCHES
        and branch_selection != LANGUAGES[lang]["btn_all_branches"]
    ):

        return REPORT_BRANCH


    start = context.user_data["report_start"]
    end = context.user_data["report_end"]

    report_type_value = context.user_data[
        "report_type"
    ]


    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")


    # --------------------------------------------------------
    # DATABASE QUERY
    # --------------------------------------------------------

    conn = get_db()


    if branch_selection == LANGUAGES[lang]["btn_all_branches"]:

        rows = conn.execute(
            """
            SELECT *
            FROM records
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, time ASC, id ASC
            """,
            (
                start_str,
                end_str
            )
        ).fetchall()

    else:

        rows = conn.execute(
            """
            SELECT *
            FROM records
            WHERE date BETWEEN ?
              AND ?
              AND branch = ?
            ORDER BY date ASC, time ASC, id ASC
            """,
            (
                start_str,
                end_str,
                branch_selection
            )
        ).fetchall()


    conn.close()


    if not rows:

        await update.message.reply_text(
            LANGUAGES[lang]["no_records"]
        )

        return REPORT_BRANCH


    # ========================================================
    # SUMMARY REPORT
    # ========================================================

    if report_type_value == "summary":

        # گروه‌بندی بر اساس شعبه و کاربر
        branch_users = {}

        grand_count = 0
        grand_total = 0.0


        for row in rows:

            branch = row["branch"]
            user = row["user"]
            amount = row["amount"]

            if branch not in branch_users:
                branch_users[branch] = {}

            if user not in branch_users[branch]:
                branch_users[branch][user] = {
                    "count": 0,
                    "total": 0.0
                }

            branch_users[branch][user]["count"] += 1
            branch_users[branch][user]["total"] += amount

            grand_count += 1
            grand_total += amount


        message = LANGUAGES[lang][
            "summary_title"
        ].format(
            start=start.strftime("%d.%m.%Y"),
            end=end.strftime("%d.%m.%Y")
        )


        for branch, users in branch_users.items():

            message += LANGUAGES[lang][
                "branch_title"
            ].format(
                branch=branch
            )

            for user, data in users.items():

                message += LANGUAGES[lang][
                    "user_summary"
                ].format(
                    user=user,
                    count=data["count"],
                    total=data["total"]
                )


        message += LANGUAGES[lang][
            "grand_total"
        ].format(
            count=grand_count,
            total=grand_total
        )


        # Telegram message محدودیت حدود 4096 کاراکتر دارد.
        # اگر گزارش خیلی بزرگ باشد، چند قسمت می‌فرستیم.

        await send_long_message(
            update,
            message
        )


    # ========================================================
    # DETAIL REPORT
    # ========================================================

    else:

        message = LANGUAGES[lang][
            "detail_title"
        ].format(
            start=start.strftime("%d.%m.%Y"),
            end=end.strftime("%d.%m.%Y")
        )


        total = 0.0


        for row in rows:

            message += LANGUAGES[lang][
                "detail_item"
            ].format(
                date=datetime.strptime(
                    row["date"],
                    "%Y-%m-%d"
                ).strftime("%d.%m.%Y"),

                time=row["time"][:5],

                branch=row["branch"],

                shift=row["shift"],

                amount=row["amount"],

                user=row["user"]
            )

            total += row["amount"]


        message += "\n💰 TOTAL: €{:.2f}".format(
            total
        )


        await send_long_message(
            update,
            message
        )


    return REPORT_BRANCH


# ============================================================
# LONG MESSAGE HELPER
# ============================================================

async def send_long_message(update, text):

    max_length = 3900

    while len(text) > max_length:

        split_at = text.rfind(
            "\n",
            0,
            max_length
        )

        if split_at == -1:
            split_at = max_length

        await update.message.reply_text(
            text[:split_at]
        )

        text = text[split_at:].lstrip()


    if text:
        await update.message.reply_text(
            text
        )


# ============================================================
# EXCEL / CSV
# ============================================================

async def excel_start_date(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    parsed = parse_date(
        update.message.text
    )

    if not parsed:

        await update.message.reply_text(
            LANGUAGES[lang]["invalid_date"]
        )

        return EXCEL_START_DATE


    context.user_data["excel_start"] = parsed

    await update.message.reply_text(
        LANGUAGES[lang]["ask_end_date"]
    )

    return EXCEL_END_DATE


async def excel_end_date(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    parsed = parse_date(
        update.message.text
    )

    if not parsed:

        await update.message.reply_text(
            LANGUAGES[lang]["invalid_date"]
        )

        return EXCEL_END_DATE


    start = context.user_data["excel_start"]

    if parsed < start:

        await update.message.reply_text(
            "❌ تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد."
        )

        return EXCEL_END_DATE


    context.user_data["excel_end"] = parsed


    await update.message.reply_text(

        LANGUAGES[lang]["choose_report_branch"],

        reply_markup=get_branch_keyboard(
            lang
        )
    )

    return EXCEL_BRANCH


async def excel_branch(update, context):

    user_id = update.effective_user.id

    lang = USER_LANGS.get(
        user_id,
        "fa"
    )

    branch_selection = update.message.text


    if branch_selection == LANGUAGES[lang]["btn_back"]:

        return await show_main_menu(
            update,
            context
        )


    if (
        branch_selection not in BRANCHES
        and branch_selection != LANGUAGES[lang]["btn_all_branches"]
    ):

        return EXCEL_BRANCH


    start = context.user_data["excel_start"]
    end = context.user_data["excel_end"]

    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")


    conn = get_db()


    if branch_selection == LANGUAGES[lang]["btn_all_branches"]:

        rows = conn.execute(
            """
            SELECT *
            FROM records
            WHERE date BETWEEN ? AND ?
            ORDER BY date ASC, time ASC, id ASC
            """,
            (
                start_str,
                end_str
            )
        ).fetchall()

    else:

        rows = conn.execute(
            """
            SELECT *
            FROM records
            WHERE date BETWEEN ?
              AND ?
              AND branch = ?
            ORDER BY date ASC, time ASC, id ASC
            """,
            (
                start_str,
                end_str,
                branch_selection
            )
        ).fetchall()


    conn.close()


    if not rows:

        await update.message.reply_text(
            LANGUAGES[lang]["no_records"]
        )

        return EXCEL_BRANCH


    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    output = io.StringIO()

    # BOM برای باز شدن درست UTF-8 در Excel
    output.write("\ufeff")

    output.write(
        "ID,Date,Time,Branch,Shift,Amount,User\n"
    )


    for row in rows:

        output.write(
            f'{row["id"]},'
            f'{row["date"]},'
            f'{row["time"]},'
            f'"{row["branch"]}",'
            f'"{row["shift"]}",'
            f'{row["amount"]:.2f},'
            f'"{row["user"]}"\n'
        )


    file_bytes = io.BytesIO(
        output.getvalue().encode("utf-8")
    )

    filename = (
        f"Kasse_Report_"
        f"{start.strftime('%Y%m%d')}_"
        f"{end.strftime('%Y%m%d')}.csv"
    )


    await update.message.reply_document(

        document=InputFile(
            file_bytes,
            filename=filename
        ),

        caption=LANGUAGES[lang][
            "excel_caption"
        ]
    )


    return await show_main_menu(
        update,
        context
    )


async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور کمکی /id یا /myid برای دریافت شناسه عددی تلگرام کاربر"""
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    username_str = f"@{user.username}" if user.username else "ندارد"
    name_str = f"{user.first_name or ''} {user.last_name or ''}".strip() or "کاربر تلگرام"

    await update.message.reply_text(
        f"📋 **مشخصات حساب تلگرام شما:**\n\n"
        f"🆔 **شناسه عددی (Telegram ID):** `{user_id}`\n"
        f"👤 **نام کاربری (Username):** {username_str}\n"
        f"🏷 **نام:** {name_str}\n\n"
        f"💡 این شناسه عددی (`{user_id}`) را کپی کرده و برای مدیر ربات ارسال کنید تا دسترسی شما را ثبت کند.",
        parse_mode="Markdown"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )


    conv_handler = ConversationHandler(

        entry_points=[
            CommandHandler(
                "start",
                start
            )
        ],


        states={

            SELECT_LANG: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    set_language
                )
            ],

            SELECT_BRANCH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    select_branch
                )
            ],

            MAIN_MENU: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_main_menu
                )
            ],

            SELECT_SHIFT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    select_shift
                )
            ],

            ENTER_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    enter_amount
                )
            ],

            REPORT_TYPE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    report_type
                )
            ],

            REPORT_START_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    report_start_date
                )
            ],

            REPORT_END_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    report_end_date
                )
            ],

            REPORT_BRANCH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    report_branch
                )
            ],

            EXCEL_START_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    excel_start_date
                )
            ],

            EXCEL_END_DATE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    excel_end_date
                )
            ],

            EXCEL_BRANCH: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    excel_branch
                )
            ]
        },


        fallbacks=[
            CommandHandler(
                "start",
                start
            ),
            CommandHandler(
                ["id", "myid"],
                get_my_id
            )
        ]
    )

    app.add_handler(
        CommandHandler(["id", "myid"], get_my_id)
    )

    app.add_handler(
        conv_handler
    )


    print(
        "Bot starting..."
    )

    print(
        f"Database: {DB_PATH}"
    )

    app.run_polling()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
