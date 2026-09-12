import os
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# --- CONFIGURATION ---
BOT_TOKEN = "8644365577:AAHgF93PupGEMqFKaDUfXU1IpauRZHMJui8"

# آیدی مدیر کل
ADMIN_USERNAME = "alirezaaghdasii"

# لیست آیدی‌های مجاز (بدون @). آیدی کارمندان را اینجا اضافه کنید:
ALLOWED_USERS = ["alirezaaghdasii", "EMPLOYEE_USERNAME_1", "EMPLOYEE_USERNAME_2"]

# --- DUMMY WEB SERVER FOR RENDER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- TRANSLATIONS & DICTIONARY ---
LANGUAGES = {
    'fa': {
        'name': '🇮🇷 فارسی',
        'choose_lang': 'لطفاً زبان خود را انتخاب کنید:',
        'welcome': 'سلام {name} عزیز! به سیستم ثبت صندوق خوش آمدید.',
        'choose_branch': 'لطفاً شعبه مورد نظر را انتخاب کنید:',
        'main_menu': 'منوی اصلی:',
        'btn_register': '➕ ثبت صندوق جدید',
        'btn_report': '📊 گزارش امروز (مدیر)',
        'btn_lang': '🌐 تغییر زبان',
        'choose_shift': 'نوبت صندوق را انتخاب کنید:',
        'enter_amount': 'لطفاً مبلغ صندوق {shift} را به یورو وارد کنید (مثلاً 450.50):',
        'invalid_amount': '❌ مبلغ وارد شده معتبر نیست. لطفاً فقط عدد وارد کنید:',
        'success_reg': '✅ ثبت شد!\n\n📅 تاریخ: {date}\n📍 شعبه: {branch}\n📦 صندوق: {shift}\n💰 مبلغ: €{amount:.2f}\n👤 ثبت‌کننده: {user}',
        'daily_report': '📊 **گزارش صندوق‌های امروز ({date})**\n📍 شعبه: {branch}\n\n',
        'shift_item': '🔹 صندوق {shift}: €{amount:.2f}\n',
        'shift_empty': '🔹 صندوق {shift}: ثبت نشده\n',
        'total_amount': '\n💵 **جمع کل امروز: €{total:.2f}**',
        'no_records': 'هیچ رکوردی برای امروز ثبت نشده است.',
        'access_denied': '⛔️ شما اجازه استفاده از این ربات را ندارید.',
        'shift_1': 'صندوق ۱ (۱۸:۰۰)',
        'shift_2': 'صندوق ۲ (۲۴:۰۰)',
        'shift_3': 'صندوق ۳ (پایان کار)',
        'branches': ['Ludwigshafen', 'Mannheim']
    },
    'de': {
        'name': '🇩🇪 Deutsch',
        'choose_lang': 'Bitte wählen Sie Ihre Sprache:',
        'welcome': 'Hallo {name}! Willkommen beim Kassenbuch-System.',
        'choose_branch': 'Bitte wählen Sie die Filiale:',
        'main_menu': 'Hauptmenü:',
        'btn_register': '➕ Neue Kasse eingeben',
        'btn_report': '📊 Tagesbericht (Admin)',
        'btn_lang': '🌐 Sprache ändern',
        'choose_shift': 'Bitte Schicht wählen:',
        'enter_amount': 'Bitte Betrag für {shift} in Euro eingeben (z.B. 450.50):',
        'invalid_amount': '❌ Ungültiger Betrag. Bitte nur Zahlen eingeben:',
        'success_reg': '✅ Gespeichert!\n\n📅 Datum: {date}\n📍 Filiale: {branch}\n📦 Kasse: {shift}\n💰 Betrag: €{amount:.2f}\n👤 Benutzer: {user}',
        'daily_report': '📊 **Tagesbericht ({date})**\n📍 Filiale: {branch}\n\n',
        'shift_item': '🔹 Kasse {shift}: €{amount:.2f}\n',
        'shift_empty': '🔹 Kasse {shift}: Nicht erfasst\n',
        'total_amount': '\n💵 **Gesamtsumme heute: €{total:.2f}**',
        'no_records': 'Heute wurden noch keine Einträge gemacht.',
        'access_denied': '⛔️ Zugriff verweigert.',
        'shift_1': 'Kasse 1 (18:00)',
        'shift_2': 'Kasse 2 (24:00)',
        'shift_3': 'Kasse 3 (Feierabend)',
        'branches': ['Ludwigshafen', 'Mannheim']
    },
    'tr': {
        'name': '🇹🇷 Türkçe',
        'choose_lang': 'Lütfen dilinizi seçin:',
        'welcome': 'Merhaba {name}! Kasa kayıt sistemine hoş geldiniz.',
        'choose_branch': 'Lütfen şubeyi seçin:',
        'main_menu': 'Ana Menü:',
        'btn_register': '➕ Yeni Kasa Ekle',
        'btn_report': '📊 Günlük Rapor (Yönetici)',
        'btn_lang': '🌐 Dili Değiştir',
        'choose_shift': 'Kasa vardiyasını seçin:',
        'enter_amount': 'Lütfen {shift} miktarını Euro olarak girin (örnek: 450.50):',
        'invalid_amount': '❌ Geçersiz miktar. Lütfen sadece sayı girin:',
        'success_reg': '✅ Kaydedildi!\n\n📅 Tarih: {date}\n📍 Şube: {branch}\n📦 Kasa: {shift}\n💰 Miktar: €{amount:.2f}\n👤 Kaydeden: {user}',
        'daily_report': '📊 **Günlük Rapor ({date})**\n📍 Şube: {branch}\n\n',
        'shift_item': '🔹 Kasa {shift}: €{amount:.2f}\n',
        'shift_empty': '🔹 Kasa {shift}: Girilmedi\n',
        'total_amount': '\n💵 **Bugünkü Toplam: €{total:.2f}**',
        'no_records': 'Bugün için henüz kayıt bulunmamaktadır.',
        'access_denied': '⛔️ Bu botu kullanma izniniz yok.',
        'shift_1': 'Kasa 1 (18:00)',
        'shift_2': 'Kasa 2 (24:00)',
        'shift_3': 'Kasa 3 (Kapanış)',
        'branches': ['Ludwigshafen', 'Mannheim']
    },
    'ar': {
        'name': '🇸🇦 العربية',
        'choose_lang': 'الرجاء اختيار اللغة:',
        'welcome': 'مرحباً {name}! أهلاً بك في نظام تسجيل الصندوق.',
        'choose_branch': 'الرجاء اختيار الفرع:',
        'main_menu': 'القائمة الرئيسية:',
        'btn_register': '➕ تسجيل صندوق جديد',
        'btn_report': '📊 التقرير اليومي (المسؤول)',
        'btn_lang': '🌐 تغيير اللغة',
        'choose_shift': 'اختر وردية الصندوق:',
        'enter_amount': 'الرجاء إدخال مبلغ الصندوق {shift} باليورو (مثال: 450.50):',
        'invalid_amount': '❌ المبلغ غير صحيح. الرجاء إدخال أرقام فقط:',
        'success_reg': '✅ تم التسجيل!\n\n📅 التاريخ: {date}\n📍 الفرع: {branch}\n📦 الصندوق: {shift}\n💰 المبلغ: €{amount:.2f}\n👤 بواسطة: {user}',
        'daily_report': '📊 **تقرير اليوم ({date})**\n📍 الفرع: {branch}\n\n',
        'shift_item': '🔹 الصندوق {shift}: €{amount:.2f}\n',
        'shift_empty': '🔹 الصندوق {shift}: لم يسجل\n',
        'total_amount': '\n💵 **المجموع الكلي اليوم: €{total:.2f}**',
        'no_records': 'لا توجد سجلات لليوم.',
        'access_denied': '⛔️ ليس لديك صلاحية لاستخدام هذا البوت.',
        'shift_1': 'صندوق ۱ (۱۸:۰۰)',
        'shift_2': 'صندوق ۲ (۲۴:۰۰)',
        'shift_3': 'صندوق ۳ (الإغلاق)',
        'branches': ['Ludwigshafen', 'Mannheim']
    }
}

USER_LANGS = {}
RECORDS = []

SELECT_LANG, SELECT_BRANCH, MAIN_MENU, SELECT_SHIFT, ENTER_AMOUNT = range(5)

def is_user_allowed(username):
    if not username:
        return False
    return username.lower() in [u.lower() for u in ALLOWED_USERS]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if not is_user_allowed(username):
        await update.message.reply_text("⛔️ دسترسی شما به این ربات مجاز نیست / Access Denied.")
        return ConversationHandler.END

    user_id = update.effective_user.id
    if user_id in USER_LANGS:
        return await show_main_menu(update, context)
    
    keyboard = [[LANGUAGES['fa']['name'], LANGUAGES['de']['name']],
                [LANGUAGES['tr']['name'], LANGUAGES['ar']['name']]]
    await update.message.reply_text(
        "Please select your language / لطفاً زبان خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_LANG

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    selected_code = 'fa'
    for code, lang_data in LANGUAGES.items():
        if lang_data['name'] == text:
            selected_code = code
            break
            
    USER_LANGS[user_id] = selected_code
    
    lang = selected_code
    branches = LANGUAGES[lang]['branches']
    keyboard = [[b] for b in branches]
    await update.message.reply_text(
        LANGUAGES[lang]['welcome'].format(name=update.effective_user.first_name) + "\n\n" + LANGUAGES[lang]['choose_branch'],
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_BRANCH

async def select_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['branch'] = update.message.text
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    lang = USER_LANGS.get(user_id, 'fa')
    
    keyboard = [[LANGUAGES[lang]['btn_register']]]
    
    # فقط اگر کاربر مدیر اصلی باشد دکمه گزارش نشان داده می‌شود
    if username and username.lower() == ADMIN_USERNAME.lower():
        keyboard.append([LANGUAGES[lang]['btn_report']])
        
    keyboard.append([LANGUAGES[lang]['btn_lang']])
    
    await update.message.reply_text(
        LANGUAGES[lang]['main_menu'],
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    lang = USER_LANGS.get(user_id, 'fa')
    text = update.message.text

    if text == LANGUAGES[lang]['btn_register']:
        keyboard = [
            [LANGUAGES[lang]['shift_1']],
            [LANGUAGES[lang]['shift_2']],
            [LANGUAGES[lang]['shift_3']]
        ]
        await update.message.reply_text(
            LANGUAGES[lang]['choose_shift'],
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SELECT_SHIFT

    elif text == LANGUAGES[lang]['btn_report'] and username and username.lower() == ADMIN_USERNAME.lower():
        today_str = datetime.now().strftime("%Y-%m-%d")
        branch = context.user_data.get('branch', 'Ludwigshafen')
        
        today_records = [r for r in RECORDS if r['date'] == today_str and r['branch'] == branch]
        
        if not today_records:
            await update.message.reply_text(LANGUAGES[lang]['no_records'])
            return MAIN_MENU

        report_msg = LANGUAGES[lang]['daily_report'].format(date=today_str, branch=branch)
        total = 0.0
        
        shifts = [LANGUAGES[lang]['shift_1'], LANGUAGES[lang]['shift_2'], LANGUAGES[lang]['shift_3']]
        for s in shifts:
            found = False
            for r in today_records:
                if r['shift'] == s:
                    report_msg += LANGUAGES[lang]['shift_item'].format(shift=s, amount=r['amount'])
                    total += r['amount']
                    found = True
                    break
            if not found:
                report_msg += LANGUAGES[lang]['shift_empty'].format(shift=s)
                
        report_msg += LANGUAGES[lang]['total_amount'].format(total=total)
        await update.message.reply_text(report_msg, parse_mode='Markdown')
        return MAIN_MENU

    elif text == LANGUAGES[lang]['btn_lang']:
        keyboard = [[LANGUAGES['fa']['name'], LANGUAGES['de']['name']],
                    [LANGUAGES['tr']['name'], LANGUAGES['ar']['name']]]
        await update.message.reply_text(
            "Please select your language / لطفاً زبان خود را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SELECT_LANG

    return MAIN_MENU

async def select_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = USER_LANGS.get(user_id, 'fa')
    context.user_data['shift'] = update.message.text
    
    await update.message.reply_text(
        LANGUAGES[lang]['enter_amount'].format(shift=update.message.text),
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTER_AMOUNT

async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = USER_LANGS.get(user_id, 'fa')
    
    try:
        amount = float(update.message.text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text(LANGUAGES[lang]['invalid_amount'])
        return ENTER_AMOUNT

    now = datetime.now()
    user_display = update.effective_user.username or update.effective_user.first_name
    
    record = {
        'date': now.strftime("%Y-%m-%d"),
        'time': now.strftime("%H:%M"),
        'branch': context.user_data.get('branch', 'Ludwigshafen'),
        'shift': context.user_data.get('shift'),
        'amount': amount,
        'user': user_display
    }
    RECORDS.append(record)

    date_str = now.strftime("%Y-%m-%d %H:%M")
    await update.message.reply_text(
        LANGUAGES[lang]['success_reg'].format(
            date=date_str,
            branch=record['branch'],
            shift=record['shift'],
            amount=record['amount'],
            user=record['user']
        )
    )
    
    return await show_main_menu(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            SELECT_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_branch)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
            SELECT_SHIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_shift)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(conv_handler)
    print("Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
