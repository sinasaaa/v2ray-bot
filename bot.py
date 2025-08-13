# bot.py
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN, INITIAL_ADMIN_ID, PANEL_LIST

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_PATH = "database.db"

async def is_admin(user_id: int) -> bool:
    """بررسی اینکه کاربر ادمین هست یا نه"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

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
        text = f"سلام {user.first_name}!\nبرای مشاهده محصولات از دکمه‌ها استفاده کنید."
        keyboard = [
            [InlineKeyboardButton("مشاهده محصولات", callback_data="show_products")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    admin = await is_admin(user.id)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if query.data == "manage_products" and admin:
        # نمایش لیست محصولات برای ادمین
        c.execute("SELECT id, name, price FROM products")
        products = c.fetchall()
        if products:
            text = "لیست محصولات:\n"
            for p in products:
                text += f"{p[0]} - {p[1]} ({p[2]} تومان)\n"
        else:
            text = "محصولی موجود نیست."
        await query.edit_message_text(text)
        
    elif query.data == "manage_panels" and admin:
        # نمایش لیست پنل‌ها برای ادمین
        c.execute("SELECT id, name, base_url FROM panels")
        panels = c.fetchall()
        if panels:
            text = "لیست پنل‌ها:\n"
            for p in panels:
                text += f"{p[0]} - {p[1]} ({p[2]})\n"
        else:
            text = "پنلی موجود نیست."
        await query.edit_message_text(text)
        
    elif query.data == "show_products":
        # نمایش محصولات به مشتری
        c.execute("SELECT name, price FROM products")
        products = c.fetchall()
        if products:
            text = "لیست محصولات:\n"
            for p in products:
                text += f"{p[0]} - {p[1]} تومان\n"
        else:
            text = "محصولی موجود نیست."
        await query.edit_message_text(text)
        
    else:
        await query.edit_message_text("دسترسی ندارید!")

    conn.close()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
