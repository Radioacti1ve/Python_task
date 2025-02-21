import sqlite3
from config import DATABASE_NAME

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id TEXT PRIMARY KEY,
                  user_id TEXT,
                  amount REAL,
                  status TEXT,
                  payment_method_id TEXT,
                  next_retry DATETIME)''')
    conn.commit()
    conn.close()

def get_payment(payment_id: str):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM payments WHERE id=?', (payment_id,))
    payment = c.fetchone()
    conn.close()
    return payment

def insert_payment(payment_data: tuple):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO payments VALUES (?,?,?,?,?,?)', payment_data)
    conn.commit()
    conn.close()

def update_payment(payment_id: str, status: str, payment_method_id: str):
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('UPDATE payments SET status=?, payment_method_id=? WHERE id=?', 
              (status, payment_method_id, payment_id))
    conn.commit()
    conn.close()
