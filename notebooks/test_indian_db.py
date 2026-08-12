import sqlite3

DB_PATH = "../data/indian_medicines.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
SELECT name, manufacturer_name, short_composition1, short_composition2
FROM medicines
WHERE name LIKE '%Dolo 650%'
""")

results = cursor.fetchall()

for row in results:
    print(row)

conn.close()