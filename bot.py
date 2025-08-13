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
    filters
)
from config import TELEGRAM_TOKEN, INITIAL_ADMIN_ID, DB_PATH
from pyxui import XUI
from pyxui.errors import BadLogin

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# بررسی اینکه کاربر ادمین هست
async def is_admin(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

# شروع ربات
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

# اتصال به پنل
def connect_panel(panel):
    xui = XUI(full_address=panel['base_url'])
    try:
        xui.login(panel['username'], panel['password'])
        return xui
    except BadLogin:
        return None

# فرمان اضافه کردن پنل
async def add_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return

    if len(context.args) != 4:
        await update.message.reply_text(
            "استفاده صحیح: /addpanel <name> <base_url> <username> <password>"
        )
        return

    name, base_url, username, password = context.args

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO panels (name, base_url, username, password) VALUES (?, ?, ?, ?)",
        (name, base_url, username, password)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(f"پنل {name} با موفقیت اضافه شد!")

# دکمه‌ها و مدیریت پنل‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    admin = await is_admin(user.id)

    if query.data == "manage_panels" and admin:
        # لیست پنل‌ها از DB
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name FROM panels")
        panels = c.fetchall()
        conn.close()

        keyboard = []
        for panel_id, name in panels:
            keyboard.append([InlineKeyboardButton(name, callback_data=f"panel_{panel_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("پنل‌ها:", reply_markup=reply_markup)

    elif query.data.startswith("panel_") and admin:
        panel_id = int(query.data.split("_")[1])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT name, base_url, username, password FROM panels WHERE id=?", (panel_id,))
        panel = c.fetchone()
        conn.close()

        if panel:
            name, base_url, username, password = panel
            xui = connect_panel({
                "base_url": base_url,
                "username": username,
                "password": password
            })
            if xui:
                await query.edit_message_text(f"پنل {name} با موفقیت وصل شد!\n(اینجا می‌تونی عملیات مدیریتی اضافه کنی)")
            else:
                await query.edit_message_text(f"اتصال به پنل {name} موفق نبود! نام کاربری یا رمز اشتباه است.")
        else:
            await query.edit_message_text("پنل پیدا نشد!")

    else:
        await query.edit_message_text("دسترسی ندارید!")

# اجرای ربات
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpanel", add_panel))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
