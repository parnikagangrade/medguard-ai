import sqlite3

DB_PATH = "../data/indian_medicines.db"

def lookup_medicine(medicine_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, manufacturer_name, type,
               pack_size_label, short_composition1, short_composition2
        FROM medicines
        WHERE LOWER(name) = LOWER(?)
    """, (medicine_name,))

    result = cursor.fetchone()
    conn.close()

    return result


# Test
result = lookup_medicine("Dolo 650 Tablet")

if result:
    print("Medicine:", result[0])
    print("Manufacturer:", result[1])
    print("Type:", result[2])
    print("Pack:", result[3])
    print("Composition 1:", result[4])
    print("Composition 2:", result[5])
else:
    print("Medicine not found")