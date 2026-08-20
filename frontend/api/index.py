import os
import sqlite3

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from rapidfuzz import process, fuzz


# ============================================================
# CONFIGURATION
# ============================================================

# index.py is now:
# medguard-ai/frontend/api/index.py
#
# We need to go:
# api -> frontend -> medguard-ai
#
# Therefore BASE_DIR becomes the repository root.

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "indian_medicines.db"
)


# ============================================================
# GEMINI SETUP
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found.")
else:
    print("Gemini API key loaded.")

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI()


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME
# ============================================================

@app.get("/api")
def root():
    return {
        "message": "MedGuard API is running"
    }


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_database_names():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM medicines"
    )

    names = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return names


def get_composition(medicine_name):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            short_composition1,
            short_composition2
        FROM medicines
        WHERE name = ?
        """,
        (medicine_name,)
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return [
            composition.strip()
            for composition in row
            if composition
            and composition.strip()
        ]

    return []


# ============================================================
# DUPLICATE INGREDIENT CHECK
# ============================================================

def check_duplicate_ingredients(
    matched_medicines
):

    ingredient_map = {}
    risks = []

    for medicine in matched_medicines:

        compositions = get_composition(
            medicine
        )

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
                            medicine
                        ]
                    }
                )

            else:

                ingredient_map[
                    ingredient
                ] = medicine

    return risks


# ============================================================
# MEDICINE SEARCH
# ============================================================

@app.get("/api/search-medicine")
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
        (f"%{q.lower()}%",)
    )

    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:

        results.append(
            {
                "name": row[0],
                "composition1": row[1],
                "composition2": row[2]
            }
        )

    return {
        "success": True,
        "query": q,
        "results": results
    }


# ============================================================
# AI ASSISTANT
# ============================================================

@app.post("/api/ask-ai")
def ask_ai(data: dict):

    question = data.get(
        "question",
        ""
    ).strip()

    if not question:

        return {
            "success": False,
            "answer": "Please enter a question."
        }

    try:

        # ----------------------------------------------------
        # DATABASE SEARCH
        # ----------------------------------------------------

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        search_terms = [
            question.lower()
        ]

        words = question.lower().split()

        for word in words:

            clean_word = word.strip(
                ".,?!:;()[]{}"
            )

            if len(clean_word) >= 3:

                search_terms.append(
                    clean_word
                )

        database_results = []

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
                    f"%{term}%"
                )
            )

            rows = cursor.fetchall()

            for row in rows:

                result = {
                    "name": row[0],
                    "composition1": row[1],
                    "composition2": row[2]
                }

                if result not in database_results:

                    database_results.append(
                        result
                    )

        conn.close()

        # ----------------------------------------------------
        # MEDICINE CONTEXT
        # ----------------------------------------------------

        if database_results:

            medicine_context = "\n".join(
                [
                    f"""
Medicine: {result['name']}
Composition 1: {
    result['composition1'] or 'N/A'
}
Composition 2: {
    result['composition2'] or 'N/A'
}
"""
                    for result
                    in database_results[:10]
                ]
            )

        else:

            medicine_context = """
No matching medicine was found in the
MedGuard medicine database.
"""

        # ----------------------------------------------------
        # GEMINI PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are MedGuard AI, a medicine information assistant.

User question:
{question}

Information retrieved from the MedGuard medicine database:

{medicine_context}

Instructions:

- Answer the user's question clearly and simply.
- Use the database information when it is available.
- Do not invent medicine composition or facts.
- If relevant medicine information was found in the database,
  explain it using that information.
- If no relevant medicine was found, clearly say that it was
  not found in the MedGuard database.
- Do not diagnose medical conditions.
- Do not prescribe medicines.
- Do not recommend changing or stopping medication.
- For personal medical decisions, recommend consulting
  a qualified doctor or pharmacist.
"""

        # ----------------------------------------------------
        # GEMINI
        # ----------------------------------------------------

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return {
            "success": True,
            "answer": response.text,
            "database_matches":
                database_results[:10]
        }

    except Exception as error:

        print(
            "AI/database error:",
            error
        )

        return {
            "success": False,
            "answer":
                "Sorry, I couldn't process your request right now."
        }


# ============================================================
# PRESCRIPTION ANALYSIS
# ============================================================

@app.post("/api/analyze-prescription")
async def analyze_prescription(
    file: UploadFile = File(...)
):

    try:

        # ----------------------------------------------------
        # READ IMAGE
        # ----------------------------------------------------

        image_bytes = await file.read()

        if not image_bytes:

            return {
                "success": False,
                "answer": "No image was uploaded.",
                "results": [],
                "risks": []
            }

        content_type = (
            file.content_type
            or "image/jpeg"
        )

        # ----------------------------------------------------
        # GEMINI VISION
        # ----------------------------------------------------

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[
                {
                    "inline_data": {
                        "mime_type": content_type,
                        "data": image_bytes
                    }
                },
                """
Read this prescription image carefully.

Extract all medicine names and dosages.

For every medicine identified, output exactly ONE line:

FORM | MEDICINE NAME | DOSAGE

Examples:

TAB | PARACETAMOL | 500 MG
CAP | AMOXICILLIN | 250 MG
SYP | CROCIN | 5 ML

Important:

- Read the prescription carefully.
- Do not invent medicines.
- If a medicine name is unclear, provide your best reading.
- Output ONLY medicine lines.
"""
            ]
        )

        raw_text = (
            response.text or ""
        ).strip()

        # ----------------------------------------------------
        # PARSE GEMINI RESPONSE
        # ----------------------------------------------------

        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        medicine_lines = []

        for line in lines:

            if "|" not in line:
                continue

            parts = [
                part.strip()
                for part in line.split("|")
            ]

            if len(parts) < 2:
                continue

            form = parts[0]
            name = parts[1]

            dosage = ""

            if len(parts) >= 3:
                dosage = parts[2]

            # Ignore obvious non-medicine lines
            if (
                not name
                or name.lower()
                in {
                    "medicine name",
                    "name",
                    "medicine"
                }
            ):
                continue

            medicine_lines.append(
                {
                    "form": form,
                    "name": name,
                    "dosage": dosage
                }
            )

        # ----------------------------------------------------
        # DATABASE MATCHING
        # ----------------------------------------------------

        all_names = get_database_names()

        results = []

        lower_to_original = {
            name.lower(): name
            for name in all_names
        }

        lower_names = [
            name.lower()
            for name in all_names
        ]

        for medicine in medicine_lines:

            ocr_name = medicine["name"]

            fuzzy_results = process.extract(
                ocr_name.lower(),
                lower_names,
                scorer=fuzz.token_set_ratio,
                limit=5
            )

            if fuzzy_results:

                best_lower = (
                    fuzzy_results[0][0]
                )

                best_score = (
                    fuzzy_results[0][1]
                )

                best_match = (
                    lower_to_original[
                        best_lower
                    ]
                )

            else:

                best_match = None
                best_score = 0

            verified = (
                best_score >= 65
            )

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
                    "verified": verified
                }
            )

        # ----------------------------------------------------
        # SAFETY CHECK
        # ----------------------------------------------------

        verified_medicines = [
            result["match"]
            for result in results
            if result["verified"]
            and result["match"]
        ]

        risks = check_duplicate_ingredients(
            verified_medicines
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {
            "success": True,
            "raw_text": raw_text,
            "results": results,
            "risks": risks
        }

    except Exception as error:

        print(
            "Prescription analysis error:",
            error
        )

        return {
            "success": False,
            "answer":
                "Could not analyze the prescription.",
            "results": [],
            "risks": []
        }
