import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# آیدی تلگرام شما برای دسترسی به گزارش PDF (آیدی عددی خود را وارد کنید)
ADMIN_TELEGRAM_ID = 7120489372  # Replace with your Telegram ID

# مراحل گفت‌وگو
BRANCH, CASSETTE, AMOUNT = range(3)

# دیتابیس رایگان SQLite برای ذخیره اطلاعات
conn = sqlite3.connect('kasse_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    user_name TEXT,
    user_id INTEGER,
    branch TEXT,
    cassette TEXT,
    amount REAL
)
''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['user_name'] = user.first_name + (f" ({user.username})" if user.username else "")
    context.user_data['user_id'] = user.id

    reply_keyboard = [['Ludwigshafen', 'Mitte', 'T1']]
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز 👋\nلطفاً شعبه مورد نظر را انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return BRANCH

async def select_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['branch'] = update.message.text
    reply_keyboard = [['صندوق ۱', 'صندوق ۲', 'صندوق ۳']]
    await update.message.reply_text(
        "نوبت صندوق را انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CASSETTE

async def select_cassette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cassette'] = update.message.text
    await update.message.reply_text(
        "لطفاً فقط مبلغ صندوق را به یورو وارد کن (مثلاً: 450.50):",
        reply_markup=ReplyKeyboardRemove()
    )
    return AMOUNT

async def save_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text("❌ مبلغ وارد شده معتبر نیست. لطفاً فقط عدد وارد کن:")
        return AMOUNT

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    cursor.execute('''
    INSERT INTO records (date, time, user_name, user_id, branch, cassette, amount)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date_str, time_str, context.user_data['user_name'], context.user_data['user_id'],
          context.user_data['branch'], context.user_data['cassette'], amount))
    conn.commit()

    await update.message.reply_text(
        f"✅ ثبت شد!\n\n"
        f"📍 شعبه: {context.user_data['branch']}\n"
        f"📦 {context.user_data['cassette']}\n"
        f"💰 مبلغ: {amount:.2f} €\n"
        f"👤 ثبت‌کننده: {context.user_data['user_name']}"
    )
    return ConversationHandler.END

async def pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("❌ شما دسترسی به دریافت گزارش را ندارید.")
        return

    cursor.execute('SELECT date, time, branch, cassette, user_name, amount FROM records ORDER BY id DESC')
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("هنوز هیچ داده‌ای ثبت نشده است.")
        return

    pdf_filename = "Kassenbericht.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("<b>Kassenprotokoll / گزارش صندوق‌ها</b>", styles['Title']))
    elements.append(Spacer(1, 15))

    data = [["Datum", "Uhrzeit", "Filiale", "Kasse", "Person", "Betrag (€)"]]
    total = 0
    for r in rows:
        data.append([r[0], r[1], r[2], r[3], r[4], f"{r[5]:.2f} €"])
        total += r[5]

    data.append(["GESAMT", "", "", "", "", f"{total:.2f} €"])

    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EDF2F7')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))

    elements.append(t)
    doc.build(elements)

    with open(pdf_filename, 'rb') as f:
        await update.message.reply_document(document=f, filename=pdf_filename)

if __name__ == '__main__':
    # توکن ربات خود را اینجا وارد کنید
    app = ApplicationBuilder().token("8644365577:AAGd6r0jnYq4gmh81EAHz5MV6orQ7akEs6U").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_branch)],
            CASSETTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_cassette)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_amount)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('pdf', pdf_report))

    print("Bot is running...")
    app.run_polling()
