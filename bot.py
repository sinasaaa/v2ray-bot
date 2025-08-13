from config import TELEGRAM_TOKEN
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import sqlite3

DB_PATH = "database.db"
ADMIN_IDS = [6133982340]  # شناسه ادمین اولیه

async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if await is_admin(user.id):
        keyboard = [[InlineKeyboardButton("افزودن پنل", callback_data="add_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("سلام ادمین!", reply_markup=reply_markup)
    else:
        await update.message.reply_text("سلام کاربر!")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "add_panel" and await is_admin(user.id):
        await query.edit_message_text(
            "لطفا اطلاعات پنل را به این شکل ارسال کنید:\n\n"
            "نام پنل | لینک پنل | نام کاربری | رمز عبور"
        )
        context.user_data["adding_panel"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if context.user_data.get("adding_panel") and await is_admin(user.id):
        text = update.message.text
        try:
            parts = [x.strip() for x in text.split("|")]
            if len(parts) < 4:
                await update.message.reply_text(
                    "فرمت اشتباه است، لطفا دوباره ارسال کنید.\n\n"
                    "مثال:\nپنل تست | https://example.com | user | pass"
                )
                return

            name = parts[0]
            base_url = parts[1]
            username = parts[2]
            password = "|".join(parts[3:])  # پشتیبانی از | در رمز عبور

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO panels (name, base_url, username, password) VALUES (?, ?, ?, ?)",
                (name, base_url, username, password)
            )
            conn.commit()
            conn.close()

            await update.message.reply_text(f"پنل {name} با موفقیت اضافه شد ✅")
        except Exception as e:
            await update.message.reply_text(
                f"خطا در افزودن پنل ❌\n{e}\n"
                "لطفا فرمت درست را استفاده کنید."
            )
        finally:
            context.user_data["adding_panel"] = False

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
