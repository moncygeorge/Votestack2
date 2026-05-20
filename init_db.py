import os
import sqlite3

DB_FILE = 'votestack2.db'
CHOICES_FILE = 'choices.txt'
VOTES_FILE = 'votes.txt'
ROLE_FILE = 'roles.txt'


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS choices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        choice TEXT NOT NULL,
        UNIQUE(role, choice)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        choice TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, role)
    )
    ''')

    conn.commit()
    conn.close()


def set_current_role(conn, role):
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ('current_role', role)
    )


def migrate_role_from_file(conn):
    if os.path.exists(ROLE_FILE):
        with open(ROLE_FILE, 'r', encoding='utf-8') as f:
            role = f.read().strip()
            if role:
                set_current_role(conn, role)
                print(f"Migrated current role: {role}")
                return role
    return None


def migrate_choices_from_file(conn, role):
    if not role or not os.path.exists(CHOICES_FILE):
        return

    with open(CHOICES_FILE, 'r', encoding='utf-8') as f:
        choices = [line.strip() for line in f if line.strip()]

    if not choices:
        return

    conn.execute("DELETE FROM choices WHERE role=?", (role,))
    conn.executemany(
        "INSERT OR IGNORE INTO choices (role, choice) VALUES (?, ?)",
        [(role, choice) for choice in choices]
    )
    print(f"Migrated {len(choices)} choices for role: {role}")


def migrate_votes_from_file(conn):
    if not os.path.exists(VOTES_FILE):
        return

    with open(VOTES_FILE, 'r', encoding='utf-8') as f:
        rows = [line.strip() for line in f if line.strip()]

    if not rows:
        return

    migrated = 0
    for row in rows:
        parts = row.split(':')
        if len(parts) != 3:
            continue
        username, role, choice = parts
        try:
            conn.execute(
                "INSERT OR IGNORE INTO votes (username, role, choice) VALUES (?, ?, ?)",
                (username, role, choice)
            )
            migrated += 1
        except sqlite3.DatabaseError:
            continue

    print(f"Migrated {migrated} votes from file")


def migrate_files_to_db():
    conn = get_db_connection()

    current_role_row = conn.execute(
        "SELECT value FROM settings WHERE key='current_role'"
    ).fetchone()

    if current_role_row:
        role_value = current_role_row['value']
    else:
        role_value = migrate_role_from_file(conn)

    if role_value:
        migrate_choices_from_file(conn, role_value)

    migrate_votes_from_file(conn)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    create_tables()
    migrate_files_to_db()
    print('Database initialized and file migration complete.')
