from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import sys

sys.path.append('.')
from extract_medicines import (
    run_ocr, detect_medicine_lines, extract_medicine_info,
    match_medicine, get_database_names, check_duplicate_ingredients
)

load_dotenv("../.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ============================================================
# Tools the agent can call
# ============================================================
def extract_and_match_medicines(image_path: str) -> str:
    """
    Runs OCR on a prescription image, detects medicine lines, and fuzzy-matches
    each one against the Indian medicine database. Returns matched medicines
    with confidence scores as a string.
    """
    print(f"[TOOL CALLED] extract_and_match_medicines('{image_path}')")
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
            "confidence": round(match_result["confidence"], 1),
            "verified": match_result["verified"]
        })
    print(f"[TOOL RESULT] {results}")
    return str(results)

def check_ingredient_overlap(matched_medicine_names: list[str]) -> str:
    """
    Checks a list of confirmed medicine names for overlapping active ingredients,
    which could indicate an unintentional double-dose risk.
    """
    print(f"[TOOL CALLED] check_ingredient_overlap({matched_medicine_names})")
    risks = check_duplicate_ingredients(matched_medicine_names)
    result = str(risks) if risks else "No overlapping ingredient risks found."
    print(f"[TOOL RESULT] {result}")
    return result

# ============================================================
# Create the agent
# ============================================================
chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        tools=[extract_and_match_medicines, check_ingredient_overlap],
        http_options=types.HttpOptions(timeout=60000),
        system_instruction=(
            "You are MedGuard, a careful prescription safety assistant. "
            "When given a prescription image path, first extract and match the medicines. "
            "Then, if 2 or more medicines were confidently matched, check them for ingredient overlap risks. "
            "Clearly state which medicines were confidently matched vs uncertain (needing manual verification). "
            "Never guess a medicine name if confidence is low. "
            "Summarize findings in simple, clear language."
        )
    )
)

print("Sending message to agent...")
response = chat.send_message(
    "Please analyze this prescription image: ../data/real_prescription.png"
)
print("\n=== FINAL AGENT RESPONSE ===")
print(response.text)