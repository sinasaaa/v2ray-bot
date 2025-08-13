# db_init.py
import sqlite3
from config import DB_PATH, INITIAL_ADMIN_ID

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # جداول
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS panels(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            base_url TEXT,
            api_key TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            title TEXT,
            price REAL,
            duration_days INTEGER,
            traffic_mb INTEGER,
            panel_id INTEGER,
            external_plan_id TEXT,
            enabled INTEGER DEFAULT 1,
            FOREIGN KEY(category_id) REFERENCES categories(id),
            FOREIGN KEY(panel_id) REFERENCES panels(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            status TEXT, -- created/paid/active/cancelled
            created_at TEXT,
            panel_account_id TEXT,
            details TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT
        )
    ''')

    # اگر ادمین اولیه تعریف شده، اضافه کن
    if INITIAL_ADMIN_ID:
        c.execute("INSERT OR IGNORE INTO admins(id) VALUES(?)", (INITIAL_ADMIN_ID,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
