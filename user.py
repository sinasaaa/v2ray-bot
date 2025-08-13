# user.py
import sqlite3
from datetime import datetime
from config import DB_PATH

def ensure_user(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(id, username, first_name, last_name) VALUES(?,?,?,?)",
              (user.id, user.username, user.first_name, user.last_name))
    conn.commit()
    conn.close()

def create_order(user_id, product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT INTO orders(user_id, product_id, status, created_at) VALUES(?,?,?,?)",
              (user_id, product_id, "created", now))
    oid = c.lastrowid
    conn.commit()
    conn.close()
    return oid

def set_order_paid(order_id, panel_account_id=None, details=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE orders SET status='paid', panel_account_id=?, details=? WHERE id=?", (panel_account_id, details, order_id))
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, product_id, status, created_at, panel_account_id, details FROM orders WHERE id=?", (order_id,))
    row = c.fetchone()
    conn.close()
    return row
