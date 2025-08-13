# admin.py
import sqlite3
from config import DB_PATH

def is_admin(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM admins WHERE id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return bool(res)

def add_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (user_id,))
    conn.commit()
    conn.close()

def remove_admin(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

# پنل‌ها
def add_panel(name, base_url, api_key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO panels(name, base_url, api_key) VALUES(?,?,?)", (name, base_url, api_key))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def list_panels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,name,base_url FROM panels")
    rows = c.fetchall()
    conn.close()
    return rows

# دسته‌بندی و محصولات
def add_category(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO categories(name) VALUES(?)", (name,))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid

def add_product(category_id, title, price, duration_days, traffic_mb, panel_id=None, external_plan_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO products(category_id, title, price, duration_days, traffic_mb, panel_id, external_plan_id)
        VALUES(?,?,?,?,?,?,?)
    ''', (category_id, title, price, duration_days, traffic_mb, panel_id, external_plan_id))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid

def get_categories():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM categories")
    rows = c.fetchall()
    conn.close()
    return rows

def get_products_by_category(category_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, price, duration_days, traffic_mb FROM products WHERE category_id=? AND enabled=1", (category_id,))
    rows = c.fetchall()
    conn.close()
    return rows
