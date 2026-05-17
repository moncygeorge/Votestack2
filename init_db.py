import sqlite3

conn = sqlite3.connect('votestack2.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE NOT NULL
)
''')

conn.commit()
conn.close()

print("Database initialized.")