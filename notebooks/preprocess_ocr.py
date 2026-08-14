import cv2
import pytesseract

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
    
    cv2.imwrite("../data/preprocessed_real.png", thresh)
    return thresh

processed_img = preprocess_image("../data/real_prescription.png")
text = pytesseract.image_to_string(processed_img, config='--psm 6')

print("=== OCR TEXT AFTER PREPROCESSING ===")
print(text)