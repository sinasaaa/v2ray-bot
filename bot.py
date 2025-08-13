from config import TELEGRAM_TOKEN
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import sqlite3
import aiohttp

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

async def panels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_admin(user.id):
        await update.message.reply_text("شما دسترسی ندارید.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS panels (id INTEGER PRIMARY KEY, name TEXT, base_url TEXT, username TEXT, password TEXT)")
    c.execute("SELECT name, base_url FROM panels")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("هیچ پنلی موجود نیست.")
    else:
        msg = "\n".join([f"{r[0]}: {r[1]}" for r in rows])
        await update.message.reply_text(f"لیست پنل‌ها:\n{msg}")

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

async def check_panel_login(base_url: str, username: str, password: str) -> bool:
    """
    این تابع سعی می‌کند با username و password وارد پنل شود.
    باید base_url فرم لاگین و پارامترها متناسب با پنل شما تغییر کند.
    """
    login_url = f"{base_url}/login"  # مسیر فرم لاگین معمولی
    data = {
        "username": username,
        "password": password
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(login_url, data=data) as resp:
                text = await resp.text()
                # بررسی ورود موفق (باید مطابق با پنل شما تغییر کند)
                if "Dashboard" in text or "Welcome" in text:
                    return True
                return False
    except Exception as e:
        print(f"Error checking panel login: {e}")
        return False

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

            # بررسی ورود به پنل
            success = await check_panel_login(base_url, username, password)
            if not success:
                await update.message.reply_text("مشخصات پنل اشتباه است ❌")
                context.user_data["adding_panel"] = False
                return

            # ذخیره در دیتابیس
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "CREATE TABLE IF NOT EXISTS panels (id INTEGER PRIMARY KEY, name TEXT, base_url TEXT, username TEXT, password TEXT)"
            )
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
    app.add_handler(CommandHandler("panels", panels))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
