import pytesseract
from PIL import Image
import re

# Get the raw OCR text (reusing Phase 1 logic)
img = Image.open("../data/sample_prescription.png")
raw_text = pytesseract.image_to_string(img)

print("=== RAW TEXT ===")
print(raw_text)

# Look for lines that look like medicine entries
# Pattern: starts with a number, then TAB/CAP/TAS (OCR typo), then a name in caps
lines = raw_text.split("\n")
medicine_lines = []

for line in lines:
    if re.search(r'(TAB|CAP|TAS)[.,]?\s+', line, re.IGNORECASE):
        medicine_lines.append(line.strip())

print("\n=== DETECTED MEDICINE LINES ===")
for m in medicine_lines:
    print(m)
    print("\n=== EXTRACTED MEDICINE NAMES ===")
for line in medicine_lines:
    # Remove the leading number and TAB/CAP/TAS marker
    cleaned = re.sub(r'^\d+\)?\s*', '', line)  # remove leading number like "1)"
    cleaned = re.sub(r'(TAB|CAP|TAS)[.,]?\s*', '', cleaned, flags=re.IGNORECASE)  # remove TAB/CAP marker
    print(cleaned)