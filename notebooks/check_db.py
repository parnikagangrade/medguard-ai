import sqlite3

conn = sqlite3.connect("../data/drugs.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM drugs")
rows = cursor.fetchall()

for row in rows:
    print("Drug:", row[0])
    print("Purpose:", row[1][:100])  # first 100 chars, just to preview
    print("---")

conn.close()