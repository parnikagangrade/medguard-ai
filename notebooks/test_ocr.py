import pytesseract
from PIL import Image

img = Image.open("../data/sample_prescription.png")
text = pytesseract.image_to_string(img)
print("Extracted text:")
print(text)