# bot.py
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from config import TELEGRAM_TOKEN, INITIAL_ADMIN_ID, DEFAULT_PANEL, DB_PATH

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------------
# Helper functions
# -----------------------------
def init_db():
    """ایجاد جدول‌ها در صورت عدم وجود"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS panels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            base_url TEXT,
            api_key TEXT
        )
    """)
    # اضافه کردن ادمین اولیه اگر موجود نباشد
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (INITIAL_ADMIN_ID,))
    if not c.fetchone():
        c.execute("INSERT INTO admins (user_id, first_name) VALUES (?, ?)", (INITIAL_ADMIN_ID, "Admin"))
    conn.commit()
    conn.close()

async def is_admin(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_panels():
    """دریافت لیست پنل‌ها از دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM panels")
    panels = c.fetchall()
    conn.close()
    return panels

# -----------------------------
# Handlers
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    admin = await is_admin(user.id)

    if admin:
        text = f"سلام ادمین {user.first_name}!\nمدیریت ربات در دسترس است."
        keyboard = [
            [InlineKeyboardButton("مدیریت محصولات", callback_data="manage_products")],
            [InlineKeyboardButton("مدیریت پنل‌ها", callback_data="manage_panels")]
        ]
    else:
        text = f"سلام {user.first_name}!\nبرای مشاهده پنل‌ها از دکمه‌ها استفاده کنید."
        panels = get_panels()
        keyboard = [[InlineKeyboardButton(p[1], callback_data=f"panel_{p[0]}")] for p in panels]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    admin = await is_admin(user.id)

    data = query.data

    if admin:
        if data == "manage_products":
            await query.edit_message_text("🛒 صفحه مدیریت محصولات (در حال توسعه)")
        elif data == "manage_panels":
            await query.edit_message_text("🖥 صفحه مدیریت پنل‌ها\nبرای اضافه کردن پنل جدید /addpanel را تایپ کنید")
    else:
        if data.startswith("panel_"):
            panel_id = int(data.split("_")[1])
            await query.edit_message_text(f"🔹 اطلاعات پنل شماره {panel_id} نمایش داده شد (در حال توسعه)")

async def add_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        await update.message.reply_text("🚫 شما ادمین نیستید!")
        return

    try:
        name = context.args[0]
        base_url = context.args[1]
        api_key = context.args[2]
    except IndexError:
        await update.message.reply_text("❌ استفاده: /addpanel <name> <base_url> <api_key>")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO panels (name, base_url, api_key) VALUES (?, ?, ?)", (name, base_url, api_key))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ پنل {name} اضافه شد!")

# -----------------------------
# Main
# -----------------------------
def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("addpanel", add_panel))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
