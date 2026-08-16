import cv2
import pytesseract
import re
import sqlite3
from rapidfuzz import process, fuzz

# ============================================================
# STEP 1: Image Preprocessing
# ============================================================
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    scale_percent = 200
    width = int(gray.shape[1] * scale_percent / 100)
    height = int(gray.shape[0] * scale_percent / 100)
    resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)

    denoised = cv2.fastNlMeansDenoising(resized, h=30)

    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 15
    )
    return thresh

# ============================================================
# STEP 2: OCR
# ============================================================
def run_ocr(image_path):
    processed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_img, config='--psm 6')
    return text

# ============================================================
# STEP 3: Detect medicine lines (SYP/TAB/CAP/SUSP)
# ============================================================
def detect_medicine_lines(raw_text):
    lines = raw_text.split("\n")
    medicine_lines = []
    for line in lines:
        if re.search(r'\b(SYP|TAB|CAP|SUSP)\b', line, re.IGNORECASE):
            medicine_lines.append(line.strip())
    return medicine_lines

# ============================================================
# STEP 4: Extract medicine name + form (CLEAN name only, no dosage attached)
# ============================================================
def extract_medicine_info(line):
    form_match = re.search(r'\b(SYP|TAB|CAP|SUSP)\b', line, re.IGNORECASE)
    form = form_match.group(1).upper() if form_match else None

    remainder = line[form_match.end():].strip() if form_match else line

    # Only grab LETTERS and hyphens for the name — stop at first digit, parenthesis, or symbol
    name_match = re.match(r'([A-Za-z\-]+)', remainder)
    name = name_match.group(1).upper().strip('-') if name_match else remainder

    dosage = remainder[len(name_match.group(1)):].strip() if name_match else ""

    return {"form": form, "name": name, "dosage": dosage}

# ============================================================
# STEP 5: Fuzzy match against the Indian medicine database
# ============================================================
FORM_MAP = {
    "SYP": ["syrup", "suspension", "oral suspension"],
    "SUSP": ["suspension", "oral suspension"],
    "TAB": ["tablet"],
    "CAP": ["capsule"]
}

def get_database_names(db_path="../data/indian_medicines.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM medicines")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names

def match_medicine(ocr_name, form, all_names, confidence_threshold=65):
    candidates = all_names
    if form and form in FORM_MAP:
        keywords = FORM_MAP[form]
        filtered = [n for n in all_names if any(k in n.lower() for k in keywords)]
        if filtered:
            candidates = filtered

    # FIX: lowercase both sides before comparing — token_set_ratio is case-sensitive,
    # and OCR names are always uppercase while the database has mixed-case names.
    # Without this, correct matches were scoring as low as 7-9% instead of near 100%.
    ocr_name_lower = ocr_name.lower()
    candidates_lower = [c.lower() for c in candidates]
    lower_to_original = {c.lower(): c for c in candidates}

    print(f"[DEBUG] Matching cleaned name: '{ocr_name}' | candidates count: {len(candidates)}")

    results = process.extract(ocr_name_lower, candidates_lower, scorer=fuzz.token_set_ratio, limit=5)

    # Map matched lowercase strings back to their original-case database names
    results_original_case = [(lower_to_original[match], score, idx) for match, score, idx in results]

    best_match, best_score, _ = results_original_case[0]

    if best_score >= confidence_threshold:
        return {"match": best_match, "confidence": best_score, "candidates": results_original_case, "verified": True}
    else:
        return {"match": None, "confidence": best_score, "candidates": results_original_case, "verified": False}

# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline(image_path):
    print("=== Running OCR ===")
    raw_text = run_ocr(image_path)
    print(raw_text)

    print("\n=== Detecting Medicine Lines ===")
    medicine_lines = detect_medicine_lines(raw_text)
    for line in medicine_lines:
        print(line)

    print("\n=== Extracting + Matching Each Medicine ===")
    all_names = get_database_names()

    results = []
    for line in medicine_lines:
        info = extract_medicine_info(line)
        match_result = match_medicine(info["name"], info["form"], all_names)

        print(f"\nOCR Name: {info['name']} | Form: {info['form']} | Dosage: {info['dosage']}")
        if match_result["verified"]:
            print(f"✅ MATCHED: {match_result['match']} (confidence: {match_result['confidence']:.1f}%)")
        else:
            print(f"⚠️ UNCERTAIN — top candidates:")
            for cand, score, _ in match_result["candidates"]:
                print(f"   {cand} → {score:.1f}%")
            print("   Manual verification required.")

        results.append({**info, **match_result})

    return results

if __name__ == "__main__":
    run_pipeline("../data/real_prescription.png")