"""
Validate FRQ JSON files for structure, required fields, and consistency.

Usage:
    python scripts/validate_frq_json.py scripts/output/frq_extracts/2024_ab_frqs.json
"""

import json
import sys

REQUIRED_FIELDS = [
    "question_html", "problem_type", "difficulty", "points",
    "access_tier", "correct_answer", "frq_metadata", "hints",
    "solution_steps", "rubric"
]

REQUIRED_METADATA = ["exam_year", "question_number", "source"]


def validate_frq(frq, idx):
    errors = []
    q_label = f"FRQ #{idx + 1}"

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in frq:
            errors.append(f"{q_label}: Missing required field '{field}'")

    # Check types
    if frq.get("problem_type") != "frq":
        errors.append(f"{q_label}: problem_type must be 'frq', got '{frq.get('problem_type')}'")

    if frq.get("access_tier") != "premium":
        errors.append(f"{q_label}: access_tier must be 'premium', got '{frq.get('access_tier')}'")

    if not isinstance(frq.get("points"), int) or frq["points"] < 1:
        errors.append(f"{q_label}: points must be a positive integer")

    # Check frq_metadata
    meta = frq.get("frq_metadata", {})
    for field in REQUIRED_METADATA:
        if field not in meta:
            errors.append(f"{q_label}: Missing metadata field '{field}'")

    # Check question_html has attribution
    qhtml = frq.get("question_html", "")
    if "<strong>" not in qhtml or "FRQ #" not in qhtml:
        errors.append(f"{q_label}: question_html should contain attribution like '<strong>YEAR AP Calculus AB FRQ #N</strong>'")

    # Check hints
    hints = frq.get("hints", [])
    if len(hints) < 2:
        errors.append(f"{q_label}: Should have at least 2 hints (1 free, 1 premium)")
    if hints and hints[0].get("cost_points") != 0:
        errors.append(f"{q_label}: First hint should be free (cost_points: 0)")
    if len(hints) > 1 and hints[1].get("cost_points") != 1:
        errors.append(f"{q_label}: Second hint should be premium (cost_points: 1)")

    # Check solution_steps
    steps = frq.get("solution_steps", [])
    if len(steps) < 3:
        errors.append(f"{q_label}: Should have at least 3 solution steps")
    for i, step in enumerate(steps):
        if not step.get("text"):
            errors.append(f"{q_label}: solution_steps[{i}] has empty text")

    # Check rubric
    rubric = frq.get("rubric", [])
    if len(rubric) != frq.get("points", 0):
        errors.append(f"{q_label}: rubric has {len(rubric)} items but points is {frq.get('points')} (should match)")

    # Check correct_answer is non-empty
    if not frq.get("correct_answer", "").strip():
        errors.append(f"{q_label}: correct_answer is empty")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_frq_json.py <frq_json_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, encoding='utf-8') as f:
        frqs = json.load(f)

    all_errors = []
    for i, frq in enumerate(frqs):
        errors = validate_frq(frq, i)
        all_errors.extend(errors)

    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  FAIL: {err}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED — {len(frqs)} FRQs validated successfully.")
        for frq in frqs:
            meta = frq["frq_metadata"]
            print(f"  OK: Q{meta['question_number']}: {frq['points']}pts, {len(frq['solution_steps'])} steps, {len(frq['rubric'])} rubric items")


if __name__ == '__main__':
    main()
