import os
import sys
import shutil
import sqlite3

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai


# ============================================================
# IMPORT MEDICINE FUNCTIONS
# ============================================================

sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "notebooks"
    )
)

from extract_medicines import (
    run_ocr,
    run_ocr_with_gemini,
    detect_medicine_lines,
    extract_medicine_info,
    match_medicine,
    get_database_names,
    check_duplicate_ingredients,
)


# ============================================================
# GEMINI SETUP
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not found.")
else:
    print("✅ Gemini API key loaded.")

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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def root():
    return {
        "message": "MedGuard API is running"
    }


# ============================================================
# PRESCRIPTION ANALYSIS
# ============================================================

@app.post("/analyze-prescription")
async def analyze_prescription(
    file: UploadFile = File(...)
):

    temp_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "website_upload.png"
    )

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR
    raw_text = run_ocr(temp_path)

    medicine_lines = detect_medicine_lines(raw_text)

    # Gemini fallback
    if len(medicine_lines) < 2:
        raw_text = run_ocr_with_gemini(temp_path)
        medicine_lines = detect_medicine_lines(raw_text)

    # Database
    all_names = get_database_names()

    results = []

    for line in medicine_lines:

        info = extract_medicine_info(line)

        match_result = match_medicine(
            info["name"],
            info["form"],
            all_names
        )

        results.append({
            "ocr_name": info["name"],
            "form": info["form"],
            "dosage": info["dosage"],
            "match": match_result["match"],
            "confidence": match_result["confidence"],
            "verified": match_result["verified"]
        })

    # Safety check
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
        "risks": risks
    }


# ============================================================
# MEDICINE SEARCH
# ============================================================

@app.get("/search-medicine")
def search_medicine(q: str):

    db_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "indian_medicines.db"
    )

    conn = sqlite3.connect(db_path)
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

        results.append({
            "name": row[0],
            "composition1": row[1],
            "composition2": row[2]
        })

    return {
        "success": True,
        "query": q,
        "results": results
    }


# ============================================================
# AI ASSISTANT
# ============================================================

@app.post("/ask-ai")
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

        # ---------------------------------------------
        # SEARCH DATABASE
        # ---------------------------------------------

        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "data",
            "indian_medicines.db"
        )

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        words = question.lower().split()

        database_results = []

        for word in words:

            if len(word) < 3:
                continue

            cursor.execute(
                """
                SELECT
                    name,
                    short_composition1,
                    short_composition2
                FROM medicines
                WHERE LOWER(name) LIKE ?
                LIMIT 5
                """,
                (f"%{word}%",)
            )

            rows = cursor.fetchall()

            for row in rows:

                result = {
                    "name": row[0],
                    "composition1": row[1],
                    "composition2": row[2]
                }

                if result not in database_results:
                    database_results.append(result)

        conn.close()


        # ---------------------------------------------
        # DATABASE CONTEXT
        # ---------------------------------------------

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

            medicine_context = (
                "No matching medicine was found "
                "in the MedGuard database."
            )


        # ---------------------------------------------
        # GEMINI
        # ---------------------------------------------

        prompt = f"""
You are MedGuard AI.

User question:
{question}

Information retrieved from the MedGuard medicine database:

{medicine_context}

Answer clearly and simply.

Rules:
- Use database information when available.
- Do not invent medicine composition.
- If the medicine is not found in the database,
  clearly say so.
- Do not diagnose.
- Do not prescribe medicines.
- Do not recommend changing dosage.
- For personal medical decisions, recommend
  consulting a doctor or pharmacist.
"""

        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return {
            "success": True,
            "answer": response.text,
            "database_matches": database_results[:10]
        }


    except Exception as e:

        print("AI error:", e)

        return {
            "success": False,
            "answer": "Sorry, I couldn't process your request."
        }