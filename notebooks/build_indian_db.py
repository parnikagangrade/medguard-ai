import pandas as pd
import sqlite3

CSV_PATH = "../data/A_Z_medicines_dataset_of_India.csv"
DB_PATH = "../data/indian_medicines.db"

# Load dataset
df = pd.read_csv(CSV_PATH)

# Remove completely empty rows
df = df.dropna(how="all")

# Remove duplicate records
df = df.drop_duplicates()

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)

# Store the dataset
df.to_sql("medicines", conn, if_exists="replace", index=False)

conn.close()

print("Indian medicine database created successfully!")
print("Total records:", len(df))
print("Database:", DB_PATH)