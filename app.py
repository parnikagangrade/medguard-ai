import streamlit as st
import sys
import os

sys.path.append('notebooks')
from extract_medicines import (
    run_ocr, detect_medicine_lines, extract_medicine_info,
    match_medicine, get_database_names, check_duplicate_ingredients
)

st.set_page_config(page_title="MedGuard", page_icon="💊")

st.title("💊 MedGuard")
st.write("Upload a photo of a prescription to check medicines and get a safety summary.")

uploaded_file = st.file_uploader("Upload prescription image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Save uploaded image temporarily
    temp_path = os.path.join("data", "uploaded_temp.png")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.image(uploaded_file, caption="Uploaded Prescription", width=300)

    with st.spinner("Reading prescription..."):
        raw_text = run_ocr(temp_path)
        medicine_lines = detect_medicine_lines(raw_text)
        all_names = get_database_names()

        results = []
        for line in medicine_lines:
            info = extract_medicine_info(line)
            match_result = match_medicine(info["name"], info["form"], all_names)
            results.append({
                "ocr_name": info["name"],
                "match": match_result["match"],
                "confidence": match_result["confidence"],
                "verified": match_result["verified"]
            })

    st.subheader("Results")

    verified_medicines = []
    for r in results:
        if r["verified"]:
            st.success(f"✅ **{r['ocr_name']}** → {r['match']} (confidence: {r['confidence']:.1f}%)")
            verified_medicines.append(r["match"])
        else:
            st.warning(f"⚠️ **{r['ocr_name']}** — uncertain match (confidence: {r['confidence']:.1f}%). Manual verification required.")

    if len(verified_medicines) >= 2:
        st.subheader("Safety Check")
        risks = check_duplicate_ingredients(verified_medicines)
        if risks:
            for risk in risks:
                st.error(f"🚨 Risk: '{risk['ingredient']}' appears in both {risk['medicines'][0]} and {risk['medicines'][1]}")
        else:
            st.success("✅ No overlapping ingredient risks found.")

    if not verified_medicines:
        st.info("No medicines could be confidently identified. Please consult a pharmacist to verify this prescription manually.")