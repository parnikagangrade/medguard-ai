import sys
sys.path.append('.')
from extract_medicines import match_medicine, get_database_names, check_duplicate_ingredients

# Test cases: (ocr_extracted_name, form, expected_correct_medicine_or_None)
# expected_correct_medicine = None means "should be flagged uncertain, not guessed"
test_cases = [
    ("CALPOL", "SYP", "Calpol 250mg Paediatric Oral Suspension Strawberry"),
    ("MEFTAL-P", "SYP", "Meftal-P Suspension"),
    ("CEVOLIN", "SYP", None),  # OCR too garbled — should NOT confidently guess
    ("XYZQPR123", "TAB", None),  # nonsense input — should definitely be flagged uncertain
    ("PARCETAMOL", "TAB", None),  # misspelled generic — ambiguous, worth flagging rather than guessing
]

def run_evaluation():
    all_names = get_database_names()
    correct = 0
    correctly_flagged_uncertain = 0
    wrong_confident_match = 0  # the dangerous case
    total = len(test_cases)

    print("=== EVALUATION RESULTS ===\n")

    for ocr_name, form, expected in test_cases:
        result = match_medicine(ocr_name, form, all_names)

        print(f"Input: '{ocr_name}' ({form})")
        print(f"Expected: {expected}")
        print(f"Got: {result['match']} (confidence: {result['confidence']:.1f}%, verified: {result['verified']})")

        if expected is None:
            # We WANT this to be flagged uncertain, not matched
            if not result["verified"]:
                correctly_flagged_uncertain += 1
                print("✅ Correctly flagged as uncertain\n")
            else:
                wrong_confident_match += 1
                print("🚨 DANGEROUS: Confidently matched something that should've been flagged!\n")
        else:
            if result["verified"] and result["match"] == expected:
                correct += 1
                print("✅ Correct match\n")
            elif result["verified"] and result["match"] != expected:
                wrong_confident_match += 1
                print("🚨 DANGEROUS: Confidently matched the WRONG medicine!\n")
            else:
                print("⚠️ Missed — flagged uncertain when it shouldn't have been\n")

    print("=== SUMMARY ===")
    print(f"Total test cases: {total}")
    print(f"Correct matches: {correct}")
    print(f"Correctly flagged uncertain: {correctly_flagged_uncertain}")
    print(f"🚨 Dangerous wrong confident matches: {wrong_confident_match}")

if __name__ == "__main__":
    run_evaluation()
