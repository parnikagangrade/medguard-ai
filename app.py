import streamlit as st
import sys
import os

sys.path.append("notebooks")

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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MedGuard",
    page_icon="💊",
    layout="centered"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background-color: #0b0f17;
}

.block-container {
    max-width: 900px;
    padding-top: 3rem;
    padding-bottom: 3rem;
}

/* ================= HEADER ================= */

.medguard-header {
    text-align: center;
    padding: 1rem 0 2.5rem 0;
}

.medguard-logo {
    font-size: 4rem;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.medguard-title {
    font-size: 4rem;
    font-weight: 800;
    letter-spacing: -2px;
    color: #f8fafc;
    line-height: 1.1;
}

.medguard-subtitle {
    color: #a8b3c5;
    font-size: 1.25rem;
    font-weight: 500;
    margin-top: 0.8rem;
}

/* ================= UPLOAD ================= */

.upload-title {
    color: #f8fafc;
    font-size: 1.45rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.upload-help {
    color: #9aa7b8;
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 1rem;
}

/* Streamlit uploader */

[data-testid="stFileUploader"] {
    background-color: #111827;
    border: 2px dashed #3b82f6;
    border-radius: 18px;
    padding: 0.8rem;
}

[data-testid="stFileUploaderDropzone"] {
    background-color: #111827;
}

/* ================= BUTTON ================= */

.stButton > button {
    width: 100%;
    border-radius: 13px;
    font-size: 1.05rem;
    font-weight: 700;
    padding: 0.8rem;
    margin-top: 1rem;
}

/* ================= RESULTS ================= */

h2 {
    color: #f8fafc !important;
    font-size: 1.8rem !important;
    margin-top: 2rem !important;
}

.result-card {
    background-color: #111827;
    border: 1px solid #263244;
    border-radius: 17px;
    padding: 1.35rem;
    margin: 1rem 0;
}

.medicine-name {
    color: #f8fafc;
    font-size: 1.2rem;
    font-weight: 700;
    line-height: 1.5;
}

.confidence {
    color: #a8b3c5;
    font-size: 0.98rem;
    margin-top: 0.5rem;
    line-height: 1.5;
}

.success-text {
    color: #34d399;
    font-weight: 700;
}

.warning-text {
    color: #fbbf24;
    font-weight: 700;
}

/* ================= SAFETY ================= */

.safety-card {
    background-color: #111827;
    border: 1px solid #263244;
    border-radius: 17px;
    padding: 1.3rem;
    margin-top: 1.8rem;
}

.safety-card h3 {
    color: #f8fafc;
    font-size: 1.3rem;
}

/* ================= IMAGE ================= */

[data-testid="stImage"] {
    border-radius: 15px;
    overflow: hidden;
}

/* ================= FOOTER ================= */

.footer {
    text-align: center;
    color: #64748b;
    font-size: 0.85rem;
    line-height: 1.7;
    margin-top: 3.5rem;
}

/* Hide Streamlit default elements */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="medguard-header">
        <div class="medguard-logo">💊</div>
        <div class="medguard-title">MedGuard</div>
        <div class="medguard-subtitle">
            Understand your prescription. Check medicines with confidence.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# UPLOAD SECTION
# ============================================================

st.markdown(
    """
    <div class="upload-title">
        Upload your prescription
    </div>

    <div class="upload-help">
        For best results, use a clear and well-lit photo.
        Keep the prescription straight and avoid unnecessary background.
    </div>
    """,
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload prescription image",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed"
)


# ============================================================
# PROCESS IMAGE
# ============================================================

if uploaded_file is not None:

    temp_path = os.path.join(
        "data",
        "uploaded_temp.png"
    )

    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.image(
        uploaded_file,
        caption="Prescription preview",
        use_container_width=True
    )

    analyze = st.button(
        "🔍 Analyze Prescription",
        type="primary"
    )

    if analyze:

        # ====================================================
        # OCR
        # ====================================================

        with st.spinner("Reading prescription..."):

            raw_text = run_ocr(temp_path)

            medicine_lines = detect_medicine_lines(raw_text)

            # Existing Gemini fallback
            if len(medicine_lines) < 2:

                st.info(
                    "Standard OCR had trouble reading this image — "
                    "trying an AI-powered reading instead..."
                )

                raw_text = run_ocr_with_gemini(temp_path)

                medicine_lines = detect_medicine_lines(raw_text)

            # =================================================
            # DATABASE MATCHING
            # =================================================

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
                    "match": match_result["match"],
                    "confidence": match_result["confidence"],
                    "verified": match_result["verified"]
                })


        # ====================================================
        # RESULTS
        # ====================================================

        st.markdown("## Prescription Results")

        verified_medicines = []

        if not results:

            st.warning(
                "⚠️ No medicine lines could be detected. "
                "Please upload a clearer prescription image."
            )

        for r in results:

            if r["verified"]:

                st.markdown(
                    f"""
                    <div class="result-card">

                        <div class="medicine-name">
                            💊 {r["match"]}
                        </div>

                        <div class="confidence">

                            <span class="success-text">
                                ✓ Confidently identified
                            </span>

                            &nbsp; • &nbsp;

                            Confidence:
                            {r["confidence"]:.1f}%

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                verified_medicines.append(
                    r["match"]
                )

            else:

                st.markdown(
                    f"""
                    <div class="result-card">

                        <div class="medicine-name">
                            ⚠️ {r["ocr_name"]}
                        </div>

                        <div class="confidence">

                            <span class="warning-text">
                                Unable to confidently identify
                            </span>

                            &nbsp; • &nbsp;

                            Confidence:
                            {r["confidence"]:.1f}%

                            <br><br>

                            Manual verification is recommended.

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


        # ====================================================
        # SAFETY CHECK
        # ====================================================

        if len(verified_medicines) >= 2:

            st.markdown(
                """
                <div class="safety-card">
                    <h3>🛡️ Safety Check</h3>
                """,
                unsafe_allow_html=True
            )

            risks = check_duplicate_ingredients(
                verified_medicines
            )

            if risks:

                for risk in risks:

                    st.error(
                        f"🚨 '{risk['ingredient']}' appears in both "
                        f"{risk['medicines'][0]} and "
                        f"{risk['medicines'][1]}"
                    )

            else:

                st.success(
                    "✓ No overlapping ingredient risks found."
                )

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )


        # ====================================================
        # NO VERIFIED MEDICINES
        # ====================================================

        if not verified_medicines:

            st.info(
                "No medicines could be confidently identified. "
                "Please verify the prescription manually with a pharmacist."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        MedGuard is an AI-assisted prescription reading tool.<br>
        It does not replace professional medical advice or pharmacist verification.
    </div>
    """,
    unsafe_allow_html=True
)