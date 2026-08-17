import sqlite3

def get_composition(medicine_name, db_path="../data/indian_medicines.db"):
    """Look up the active ingredients for a matched medicine name."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT short_composition1, short_composition2 FROM medicines WHERE name = ?",
        (medicine_name,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return [c.strip() for c in row if c and c.strip()]
    return []

def check_duplicate_ingredients(matched_medicines):
    """
    Checks if two or more matched medicines share the same active ingredient,
    which could mean the patient is unintentionally getting a double dose.
    """
    ingredient_map = {}  # ingredient -> list of medicines containing it
    risks = []

    for med_name in matched_medicines:
        compositions = get_composition(med_name)
        for comp in compositions:
            # Normalize (ignore dosage numbers in brackets for comparison)
            base_ingredient = comp.split('(')[0].strip().lower()
            if base_ingredient in ingredient_map:
                risks.append({
                    "ingredient": base_ingredient,
                    "medicines": [ingredient_map[base_ingredient], med_name]
                })
            else:
                ingredient_map[base_ingredient] = med_name

    return risks

matched_medicines = [
    "Calpol 250mg Paediatric Oral Suspension Strawberry",
    "Meftal-P Suspension"
]

print("=== Checking for duplicate/overlapping ingredients ===")
risks = check_duplicate_ingredients(matched_medicines)

if risks:
    for r in risks:
        print(f"⚠️ RISK: '{r['ingredient']}' appears in both {r['medicines'][0]} AND {r['medicines'][1]}")
else:
    print("✅ No duplicate ingredient risks found among matched medicines.")