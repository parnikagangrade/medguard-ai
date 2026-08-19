from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import sys

# Import your existing working functions
sys.path.append('.')
from extract_medicines import (
    run_ocr, detect_medicine_lines, extract_medicine_info,
    match_medicine, get_database_names, check_duplicate_ingredients
)

load_dotenv("../.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ============================================================
# Define tools the agent can call
# ============================================================
def extract_and_match_medicines(image_path: str) -> str:
    """
    Runs OCR on a prescription image, detects medicine lines, and fuzzy-matches
    each one against the Indian medicine database. Returns matched medicines
    with confidence scores.
    """
    raw_text = run_ocr(image_path)
    medicine_lines = detect_medicine_lines(raw_text)
    all_names = get_database_names()

    results = []
    for line in medicine_lines:
        info = extract_medicine_info(line)
        match_result = match_medicine(info["name"], info["form"], all_names)
        results.append({
            "ocr_name": info["name"],
            "matched_name": match_result["match"],
            "confidence": match_result["confidence"],
            "verified": match_result["verified"]
        })
    return str(results)

def check_ingredient_overlap(matched_medicine_names: list) -> str:
    """
    Checks a list of confirmed medicine names for overlapping active ingredients,
    which could indicate an unintentional double-dose risk.
    """
    risks = check_duplicate_ingredients(matched_medicine_names)
    return str(risks) if risks else "No overlapping ingredient risks found."

# ============================================================
# Create the agent chat with tools
# ============================================================
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        tools=[extract_and_match_medicines, check_ingredient_overlap],
        system_instruction=(
            "You are MedGuard, a careful prescription safety assistant. "
            "When given a prescription image path, extract and match the medicines, "
            "then check for ingredient overlap risks. "
            "Always clearly state which medicines were confidently matched vs uncertain. "
            "Never guess a medicine name if confidence is low — say it needs manual verification instead. "
            "Summarize findings in simple, clear language for a patient or caregiver."
        )
    )
)

# ============================================================
# Run the agent
# ============================================================
print("Starting agent...")

response = chat.send_message(
    "Please analyze this prescription: ../data/real_prescription.png"
)

print("Got response object")
print("Response text:", response.text)