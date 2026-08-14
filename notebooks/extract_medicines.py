import pytesseract
from PIL import Image
import re
import sqlite3
from rapidfuzz import process, fuzz

IMAGE_PATH = "../data/real_prescription.png.png"
DB_PATH = "../data/indian_medicines.db"


# ---------- OCR ----------

img = Image.open(IMAGE_PATH)
raw_text = pytesseract.image_to_string(img)

print("=== RAW TEXT ===")
print(raw_text)


# ---------- Detect medicine lines ----------

lines = raw_text.split("\n")
medicine_lines = []

medicine_pattern = r'^\s*(?:\d+[\.\)]?\s*)?(TAB|CAP|SYP|SYRUP|TABS|CAPS|INJ)[\.,]?\s+'

for line in lines:
    line = line.strip()

    if re.search(medicine_pattern, line, re.IGNORECASE):
        medicine_lines.append(line)


print("\n=== DETECTED MEDICINE LINES ===")

for line in medicine_lines:
    print(line)


# ---------- Load database ----------

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT name, manufacturer_name, type,
           pack_size_label, short_composition1, short_composition2
    FROM medicines
""")

rows = cursor.fetchall()


# ---------- Helper functions ----------

def normalize(text):
    """Normalize text for comparison."""
    text = text.lower()
    text = text.replace("-", " ")
    text = re.sub(r'[^a-z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_form_words(form):
    return {
        "SYP": ["syrup", "suspension"],
        "SYRUP": ["syrup", "suspension"],
        "TAB": ["tablet"],
        "TABS": ["tablet"],
        "CAP": ["capsule"],
        "CAPS": ["capsule"],
        "INJ": ["injection"]
    }.get(form, [])


# ---------- Matching ----------

print("\n=== MEDICINE MATCHING ===")

for line in medicine_lines:

    # Get prescription form
    form_match = re.match(
        r'^\s*(TAB|CAP|SYP|SYRUP|TABS|CAPS|INJ)',
        line,
        re.IGNORECASE
    )

    form = form_match.group(1).upper() if form_match else ""

    # Remove form
    cleaned = re.sub(
        r'^\s*(?:\d+[\.\)]?\s*)?(TAB|CAP|SYP|SYRUP|TABS|CAPS|INJ)[\.,]?\s+',
        '',
        line,
        flags=re.IGNORECASE
    )

    parts = cleaned.split(maxsplit=1)

    if not parts:
        continue

    ocr_name = parts[0]
    dosage = parts[1] if len(parts) > 1 else ""

    print(f"\nOCR Medicine: {ocr_name}")
    print(f"Form: {form}")
    print(f"OCR Dosage: {dosage}")

    # Candidates based on dosage form
    allowed_forms = get_form_words(form)

    if allowed_forms:
        filtered_rows = [
            row for row in rows
            if any(word in row[0].lower() for word in allowed_forms)
        ]
    else:
        filtered_rows = rows

    if not filtered_rows:
        print("No candidates found.")
        continue

    candidate_names = [row[0] for row in filtered_rows]

    # Normalize OCR name
    normalized_ocr = normalize(ocr_name)

    # Fuzzy search
    matches = process.extract(
        normalized_ocr,
        [normalize(name) for name in candidate_names],
        scorer=fuzz.ratio,
        limit=10
    )

    # Reconstruct original database names
    scored_candidates = []

    for normalized_match, score, index in matches:
        original_name = candidate_names[index]
        scored_candidates.append((original_name, score))

    # Display top candidates
    print("\nTop candidates:")

    for name, score in scored_candidates[:5]:
        print(f"  {name}  → {score:.1f}%")

    # Don't automatically accept weak matches
    if not scored_candidates:
        print("No match found.")
        continue

    best_name, best_score = scored_candidates[0]

    if best_score < 75:
        print("\nRESULT: No reliable match.")
        print("Manual verification required.")
        continue

    # Get database information
    cursor.execute("""
        SELECT name, manufacturer_name, type,
               pack_size_label, short_composition1, short_composition2
        FROM medicines
        WHERE name = ?
    """, (best_name,))

    result = cursor.fetchone()

    if result:
        print("\nRESULT: Possible match")
        print("Medicine:", result[0])
        print("Confidence:", f"{best_score:.1f}%")
        print("Manufacturer:", result[1])
        print("Type:", result[2])
        print("Pack:", result[3])
        print("Composition 1:", result[4])
        print("Composition 2:", result[5])

        if best_score < 85:
            print("WARNING: Confidence is below 85%. Verify manually.")


conn.close()