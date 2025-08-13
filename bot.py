# bot.py
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from config import TELEGRAM_TOKEN, BOT_NAME
from db_init import init_db
import admin as admin_mod
import user as user_mod
from v2ray_api import V2RayPanel, V2RayPanelError
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# initialize DB if needed
init_db()

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_mod.ensure_user(user)
    text = f"سلام {user.first_name}!\nاین ربات فروش کانفیگ V2Ray است."
    if admin_mod.is_admin(user.id):
        text += "\nشما ادمین هستید. /admin برای مدیریت"
    text += "\n/shops برای دیدن محصولات"
    update.message.reply_text(text)

# admin panel entry
def admin_panel(update: Update, context: CallbackContext):
    user = update.effective_user
    if not admin_mod.is_admin(user.id):
        update.message.reply_text("دسترسی ادمین ندارید.")
        return
    keyboard = [
        [InlineKeyboardButton("مدیریت پنل‌ها", callback_data="adm_panels")],
        [InlineKeyboardButton("دسته‌ها", callback_data="adm_cats")],
        [InlineKeyboardButton("محصولات", callback_data="adm_products")],
        [InlineKeyboardButton("ارسال به همه", callback_data="adm_broadcast")]
    ]
    update.message.reply_text("منوی ادمین:", reply_markup=InlineKeyboardMarkup(keyboard))

def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    query.answer()
    data = query.data

    if data == "adm_panels":
        rows = admin_mod.list_panels()
        if not rows:
            query.edit_message_text("پنلی تعریف نشده. از /addpanel استفاده کنید.\nفرمت: /addpanel name|https://panel|APIKEY")
            return
        text = "پنل‌ها:\n" + "\n".join([f"{r[0]} - {r[1]} ({r[2]})" for r in rows])
        query.edit_message_text(text)
    elif data == "adm_cats":
        cats = admin_mod.get_categories()
        if not cats:
            query.edit_message_text("دسته‌ای وجود ندارد. /addcat <name>")
            return
        s = "دسته‌ها:\n" + "\n".join([f"{c[0]} - {c[1]}" for c in cats])
        query.edit_message_text(s)
    elif data == "adm_products":
        cats = admin_mod.get_categories()
        if not cats:
            query.edit_message_text("ابتدا دسته اضافه کنید. /addcat <name>")
            return
        text = "برای افزودن محصول از دستور زیر استفاده کنید:\n/addproduct category_id|title|price|duration_days|traffic_mb|panel_id(optional)|external_plan_id(optional)\n\nدسته‌ها:\n" + "\n".join([f"{c[0]} - {c[1]}" for c in cats])
        query.edit_message_text(text)
    elif data == "adm_broadcast":
        query.edit_message_text("برای ارسال پست به همه از دستور زیر استفاده کنید:\n/broadcast <متن>")
    else:
        query.edit_message_text("دستور ناشناخته.")

# add panel via command
def addpanel_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not admin_mod.is_admin(user.id):
        update.message.reply_text("فقط ادمین‌ها می‌تونن پنل اضافه کنن.")
        return
    text = update.message.text.partition(" ")[2].strip()
    # فرمت: /addpanel name|https://base|APIKEY
    try:
        name, base, key = [x.strip() for x in text.split("|", 2)]
    except Exception:
        update.message.reply_text("فرمت درست: /addpanel name|https://base|APIKEY")
        return
    pid = admin_mod.add_panel(name, base, key)
    update.message.reply_text(f"پنل اضافه شد: id={pid}")

def addcat_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not admin_mod.is_admin(user.id):
        update.message.reply_text("فقط ادمین‌ها.")
        return
    name = update.message.text.partition(" ")[2].strip()
    if not name:
        update.message.reply_text("فرمت: /addcat <name>")
        return
    cid = admin_mod.add_category(name)
    update.message.reply_text(f"دسته اضافه شد: id={cid}")

def addproduct_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not admin_mod.is_admin(user.id):
        update.message.reply_text("فقط ادمین‌ها.")
        return
    text = update.message.text.partition(" ")[2].strip()
    # فرمت: category_id|title|price|duration_days|traffic_mb|panel_id(optional)|external_plan_id(optional)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 5:
        update.message.reply_text("فرمت: /addproduct category_id|title|price|duration_days|traffic_mb|panel_id(optional)|external_plan_id(optional)")
        return
    category_id = int(parts[0])
    title = parts[1]
    price = float(parts[2])
    duration_days = int(parts[3])
    traffic_mb = int(parts[4])
    panel_id = int(parts[5]) if len(parts) > 5 and parts[5] else None
    external_plan_id = parts[6] if len(parts) > 6 else None
    pid = admin_mod.add_product(category_id, title, price, duration_days, traffic_mb, panel_id, external_plan_id)
    update.message.reply_text(f"محصول افزوده شد: id={pid}")

def shops_cmd(update: Update, context: CallbackContext):
    cats = admin_mod.get_categories()
    if not cats:
        update.message.reply_text("فعلا محصولی موجود نیست.")
        return
    keyboard = []
    for c in cats:
        keyboard.append([InlineKeyboardButton(c[1], callback_data=f"cat_{c[0]}")])
    update.message.reply_text("دسته‌ها:", reply_markup=InlineKeyboardMarkup(keyboard))

def cat_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    if not data.startswith("cat_"):
        query.edit_message_text("خطا")
        return
    cat_id = int(data.split("_",1)[1])
    prods = admin_mod.get_products_by_category(cat_id)
    if not prods:
        query.edit_message_text("هیچ محصولی در این دسته نیست.")
        return
    kb = []
    text_lines = []
    for p in prods:
        pid, title, price, dur, traffic = p
        text_lines.append(f"{pid}. {title} - {price} تومان - {dur} روز - {traffic}MB")
        kb.append([InlineKeyboardButton(f"خرید {pid}", callback_data=f"buy_{pid}")])
    query.edit_message_text("\n".join(text_lines), reply_markup=InlineKeyboardMarkup(kb))

def buy_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    query.answer()
    if query.data.startswith("buy_"):
        pid = int(query.data.split("_",1)[1])
        oid = user_mod.create_order(user.id, pid)
        # در اینجا فرایند پرداخت را باید پیاده کنید — این نمونه فرض پرداخت موفق است.
        # برای شروع، به کاربر پیام می‌دهیم که سفارش ساخته شد و منتظر پرداخت است.
        query.edit_message_text(f"سفارش ساخته شد: {oid}\nبرای پرداخت از روش دلخواه استفاده کرده و سپس /markpaid {oid} را ارسال کنید (برای تست).")
    else:
        query.edit_message_text("خطا")

def markpaid_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text.partition(" ")[2].strip()
    # فقط ادمین یا خود کاربر میتونه مارک کنه؛ اینجا برای تست فقط ادمین اجازه داره
    if not text:
        update.message.reply_text("فرمت: /markpaid <order_id>")
        return
    order_id = int(text)
    # خواندن سفارش و اطلاعات محصول
    o = user_mod.get_order(order_id)
    if not o:
        update.message.reply_text("سفارش یافت نشد.")
        return
    # حالا باید ساخت اکانت در پنل انجام شود:
    # 1) از جدول products پنل و external_plan_id را بخوان
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, title, duration_days, traffic_mb, panel_id, external_plan_id FROM products WHERE id=?", (o[2],))
    prod = c.fetchone()
    if not prod:
        update.message.reply_text("محصول نامشخص.")
        conn.close()
        return
    product_id, title, duration_days, traffic_mb, panel_id, external_plan_id = prod
    # گرفتن پنل
    if not panel_id:
        update.message.reply_text("محصول به پنل متصل نشده؛ ابتدا پنل را تنظیم کنید.")
        conn.close()
        return
    c.execute("SELECT base_url, api_key FROM panels WHERE id=?", (panel_id,))
    p = c.fetchone()
    conn.close()
    if not p:
        update.message.reply_text("پنل مرتبط پیدا نشد.")
        return
    base_url, api_key = p
    panel = V2RayPanel(base_url, api_key)
    # تولید username یکتا:
    username = f"user{int(time.time())}{order_id}"
    try:
        resp = panel.create_account(username=username, inbound={}, traffic_mb=traffic_mb, duration_days=duration_days)
        # resp باید شامل id یا لینک config باشد
        panel_account_id = str(resp.get("id") or resp.get("account_id") or resp.get("uid") or "")
        details = str(resp)
        user_mod.set_order_paid(order_id, panel_account_id=panel_account_id, details=details)
        update.message.reply_text(f"سفارش {order_id} فعال شد.\nاطلاعات پنل: {details}")
    except Exception as e:
        update.message.reply_text(f"خطا در ساخت اکانت روی پنل: {e}")

def broadcast_cmd(update: Update, context: CallbackContext):
    user = update.effective_user
    if not admin_mod.is_admin(user.id):
        update.message.reply_text("فقط ادمین‌ها می‌توانند ارسال کنند.")
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        update.message.reply_text("فرمت: /broadcast <متن>")
        return
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = c.fetchall()
    conn.close()
    sent = 0
    for u in users:
        try:
            context.bot.send_message(chat_id=u[0], text=text)
            sent += 1
        except Exception:
            pass
    update.message.reply_text(f"ارسال شد به {sent} کاربر.")

def help_cmd(update: Update, context: CallbackContext):
    update.message.reply_text("/start\n/shops\n/admin (اگر ادمین هستید)\n")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CallbackQueryHandler(callback_query_handler, pattern="^adm_"))
    dp.add_handler(CallbackQueryHandler(cat_callback, pattern="^cat_"))
    dp.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_"))

    dp.add_handler(CommandHandler("addpanel", addpanel_cmd))
    dp.add_handler(CommandHandler("addcat", addcat_cmd))
    dp.add_handler(CommandHandler("addproduct", addproduct_cmd))
    dp.add_handler(CommandHandler("shops", shops_cmd))
    dp.add_handler(CommandHandler("markpaid", markpaid_cmd))
    dp.add_handler(CommandHandler("broadcast", broadcast_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))

    updater.start_polling()
    logger.info("Bot started")
    updater.idle()

if __name__ == "__main__":
    main()
