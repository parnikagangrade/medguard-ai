import os
import sqlite3
import re
import base64

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from rapidfuzz import process, fuzz


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "indian_medicines.db")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found.")

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

def get_database_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM medicines")

    names = [row[0] for row in cursor.fetchall()]

    conn.close()

    return names


def get_composition(medicine_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT short_composition1, short_composition2
        FROM medicines
        WHERE name = ?
        """,
        (medicine_name,),
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return [
            c.strip()
            for c in row
            if c and c.strip()
        ]

    return []


def check_duplicate_ingredients(matched_medicines):

    ingredient_map = {}
    risks = []

    for medicine in matched_medicines:

        compositions = get_composition(medicine)

        for composition in compositions:

            ingredient = (
                composition
                .split("(")[0]
                .strip()
                .lower()
            )

            if ingredient in ingredient_map:

                risks.append(
                    {
                        "ingredient": ingredient,
                        "medicines": [
                            ingredient_map[ingredient],
                            medicine,
                        ],
                    }
                )

            else:
                ingredient_map[ingredient] = medicine

    return risks


# ============================================================
# MEDICINE SEARCH
# ============================================================

@app.get("/search-medicine")
def search_medicine(q: str):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            name,
            short_composition1,
            short_composition2
        FROM medicines
        WHERE LOWER(name) LIKE ?
        LIMIT 20
        """,
        (f"%{q.lower()}%",),
    )

    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:

        results.append(
            {
                "name": row[0],
                "composition1": row[1],
                "composition2": row[2],
            }
        )

    return {
        "success": True,
        "query": q,
        "results": results,
    }


# ============================================================
# AI ASSISTANT
# ============================================================

@app.post("/ask-ai")
def ask_ai(data: dict):

    question = data.get(
        "question",
        "",
    ).strip()

    if not question:

        return {
            "success": False,
            "answer": "Please enter a question.",
        }

    try:

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        words = question.lower().split()

        database_results = []

        # Search complete question first
        search_terms = [question.lower()]

        # Search individual words
        for word in words:

            clean_word = word.strip(
                ".,?!:;()[]{}"
            )

            if len(clean_word) >= 3:

                search_terms.append(
                    clean_word
                )

        for term in search_terms:

            cursor.execute(
                """
                SELECT
                    name,
                    short_composition1,
                    short_composition2
                FROM medicines
                WHERE LOWER(name) LIKE ?
                   OR LOWER(short_composition1) LIKE ?
                   OR LOWER(short_composition2) LIKE ?
                LIMIT 10
                """,
                (
                    f"%{term}%",
                    f"%{term}%",
                    f"%{term}%",
                ),
            )

            rows = cursor.fetchall()

            for row in rows:

                result = {
                    "name": row[0],
                    "composition1": row[1],
                    "composition2": row[2],
                }

                if result not in database_results:
                    database_results.append(result)

        conn.close()

        if database_results:

            medicine_context = "\n".join(
                [
                    f"""
Medicine: {r['name']}
Composition 1: {r['composition1'] or 'N/A'}
Composition 2: {r['composition2'] or 'N/A'}
"""
                    for r in database_results[:10]
                ]
            )

        else:

            medicine_context = """
No matching medicine was found in the
MedGuard medicine database.
"""

        prompt = f"""
You are MedGuard AI, a medicine information assistant.

User question:
{question}

Information retrieved from the MedGuard medicine database:

{medicine_context}

Instructions:

- Answer clearly and simply.
- Use database information when available.
- Do not invent medicine composition or facts.
- If no relevant medicine was found, clearly say that
  it was not found in the MedGuard database.
- Do not diagnose medical conditions.
- Do not prescribe medicines.
- Do not recommend changing or stopping medication.
- For personal medical decisions, recommend consulting
  a doctor or pharmacist.
"""

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        return {
            "success": True,
            "answer": response.text,
            "database_matches": database_results[:10],
        }

    except Exception as e:

        print("AI error:", e)

        return {
            "success": False,
            "answer": "Sorry, I couldn't process your request right now.",
        }


# ============================================================
# PRESCRIPTION ANALYSIS — GEMINI VISION
# ============================================================

@app.post("/analyze-prescription")
async def analyze_prescription(
    file: UploadFile = File(...)
):

    try:

        image_bytes = await file.read()

        if not image_bytes:

            return {
                "success": False,
                "answer": "No image was uploaded.",
            }

        # Determine MIME type
        content_type = file.content_type or "image/jpeg"

        # Send image directly to Gemini
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": image_bytes,
                    }
                },
                """
Read this prescription image carefully.

Extract all medicine names and dosages.

For every medicine you identify, output ONE line using exactly:

FORM | MEDICINE NAME | DOSAGE

Examples:

TAB | PARACETAMOL | 500 MG
CAP | AMOXICILLIN | 250 MG
SYP | CROCIN | 5 ML

Important:
- Read the image carefully.
- Do not invent medicines.
- If a medicine name is unclear, still provide your best reading.
- Output ONLY the medicine lines.
""",
            ],
        )

        raw_text = response.text.strip()

        # ====================================================
        # PARSE GEMINI OUTPUT
        # ====================================================

        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        medicine_lines = []

        for line in lines:

            if "|" in line:

                parts = [
                    p.strip()
                    for p in line.split("|")
                ]

                if len(parts) >= 2:

                    form = parts[0]
                    name = parts[1]
                    dosage = (
                        parts[2]
                        if len(parts) >= 3
                        else ""
                    )

                    medicine_lines.append(
                        {
                            "form": form,
                            "name": name,
                            "dosage": dosage,
                        }
                    )

        # ====================================================
        # DATABASE MATCHING
        # ====================================================

        all_names = get_database_names()

        results = []

        for medicine in medicine_lines:

            ocr_name = medicine["name"]

            candidates = all_names

            # Fuzzy matching
            results_fuzzy = process.extract(
                ocr_name.lower(),
                [n.lower() for n in candidates],
                scorer=fuzz.token_set_ratio,
                limit=5,
            )

            if results_fuzzy:

                best_lower, best_score, _ = (
                    results_fuzzy[0]
                )

                lower_map = {
                    n.lower(): n
                    for n in candidates
                }

                best_match = lower_map[
                    best_lower
                ]

            else:

                best_match = None
                best_score = 0

            verified = best_score >= 65

            results.append(
                {
                    "ocr_name": ocr_name,
                    "form": medicine["form"],
                    "dosage": medicine["dosage"],
                    "match": (
                        best_match
                        if verified
                        else None
                    ),
                    "confidence": best_score,
                    "verified": verified,
                }
            )

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        verified_medicines = [
            r["match"]
            for r in results
            if r["verified"]
        ]

        risks = check_duplicate_ingredients(
            verified_medicines
        )

        return {
            "success": True,
            "raw_text": raw_text,
            "results": results,
            "risks": risks,
        }

    except Exception as e:

        print(
            "Prescription analysis error:",
            e,
        )

        return {
            "success": False,
            "answer": "Could not analyze the prescription.",
            "results": [],
            "risks": [],
        }


# ============================================================
# VERCEL ENTRYPOINT
# ============================================================

# Vercel detects the FastAPI `app` object above.
