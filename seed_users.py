import sqlite3

phones = [
    "+12146836076",
    "+12142932728"
]

conn = sqlite3.connect('votestack2.db')

cursor = conn.cursor()

for phone in phones:

    try:
        cursor.execute(
            "INSERT INTO users (phone_number) VALUES (?)",
            (phone,)
        )

        print(f"Added: {phone}")

    except sqlite3.IntegrityError:

        print(f"Skipped duplicate: {phone}")

conn.commit()
conn.close()

print("Done.")