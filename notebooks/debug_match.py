from rapidfuzz import fuzz

ocr_name = "CALPOL"

known_calpol_entries = [
    'Calpol 250mg Paediatric Oral Suspension Strawberry',
    'Calpol 250mg Paediatric Oral Suspension',
    'Calpol 120mg Suspension Strawberry',
    'Calpol 120mg Suspension',
    'Calpol Plus 400 mg/325 mg Suspension'
]

print("=== Direct score check ===")
for entry in known_calpol_entries:
    score = fuzz.token_set_ratio(ocr_name, entry)
    print(f"{entry} → {score:.1f}%")