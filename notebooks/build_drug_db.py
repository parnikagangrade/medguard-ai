import requests
import sqlite3

conn = sqlite3.connect("../data/drugs.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS drugs (
    name TEXT PRIMARY KEY,
    purpose TEXT,
    dosage TEXT,
    warnings TEXT
)
""")

def fetch_and_store(drug_name):
    url = "https://api.fda.gov/drug/label.json"
    params = {"search": f'openfda.brand_name:"{drug_name}"', "limit": 1}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "results" in data:
            drug = data["results"][0]
            purpose = " ".join(drug.get("purpose", drug.get("indications_and_usage", ["N/A"])))
            dosage = " ".join(drug.get("dosage_and_administration", ["N/A"]))
            warnings = " ".join(drug.get("warnings", ["N/A"]))

            cursor.execute("""
            INSERT OR REPLACE INTO drugs (name, purpose, dosage, warnings)
            VALUES (?, ?, ?, ?)
            """, (drug_name, purpose, dosage, warnings))
            conn.commit()
            print(f"Stored: {drug_name}")
        else:
            print(f"No data found for {drug_name}")
    else:
        print(f"Error fetching {drug_name}: {response.status_code}")

common_drugs = ["Tylenol", "Advil", "Amoxicillin", "Aspirin"]

for drug in common_drugs:
    fetch_and_store(drug)

print("\nDone! Database saved to data/drugs.db")