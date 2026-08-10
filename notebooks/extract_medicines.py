import pytesseract
from PIL import Image
import re

img = Image.open("../data/sample_prescription.png")
raw_text = pytesseract.image_to_string(img)

print("=== RAW TEXT ===")
print(raw_text)

lines = raw_text.split("\n")
medicine_lines = []

for line in lines:
    if re.search(r'(TAB|CAP|TAS)[.,]?\s+', line, re.IGNORECASE):
        medicine_lines.append(line.strip())

print("\n=== DETECTED MEDICINE LINES ===")
for m in medicine_lines:
    print(m)

print("\n=== MEDICINE NAME + DOSAGE (split) ===")
for line in medicine_lines:
    cleaned = re.sub(r'^\d+\)?\s*', '', line)
    cleaned = re.sub(r'(TAB|CAP|TAS)[.,]?\s*', '', cleaned, flags=re.IGNORECASE)
    match = re.match(r'([A-Za-z\s]+?)\s+(\d.*)', cleaned)
    if match:
        name = match.group(1).strip()
        dosage = match.group(2).strip()
        print(f"Name: {name} | Dosage/Timing: {dosage}")