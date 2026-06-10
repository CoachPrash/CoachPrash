"""
Append released AP FRQs to content JSON files.

Reads the FRQ mapping and FRQ JSON files, then appends each FRQ
to the correct concept's problem set in the content JSON.

Usage:
    python scripts/append_frqs_to_content.py --mapping scripts/frq_mapping_calculus.json --content content/math_ap_calculus_ab_bc.json

Options:
    --dry-run    Show what would be done without modifying files
"""

import argparse
import json
import os


def find_concept(content_data, concept_slug):
    """Find a concept by slug in the content JSON. Returns (topic_idx, concept_idx, concept_data)."""
    for ti, topic in enumerate(content_data['topics']):
        for ci, concept in enumerate(topic['concepts']):
            if concept['slug'] == concept_slug:
                return ti, ci, concept
    return None, None, None


def main():
    parser = argparse.ArgumentParser(description="Append released FRQs to content JSON")
    parser.add_argument('--mapping', required=True, help='Path to FRQ mapping JSON')
    parser.add_argument('--content', required=True, help='Path to content JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Show plan without modifying files')
    args = parser.parse_args()

    # Load mapping
    with open(args.mapping, encoding='utf-8') as f:
        mapping_data = json.load(f)

    # Load content JSON
    with open(args.content, encoding='utf-8') as f:
        content_data = json.load(f)

    # Group FRQs by source file for efficient loading
    frq_cache = {}
    appended = 0
    skipped = 0

    for entry in mapping_data['mappings']:
        frq_file = entry['frq_file']
        q_num = entry['question_number']
        concept_slug = entry['concept_slug']

        # Load FRQ file if not cached
        if frq_file not in frq_cache:
            with open(frq_file, encoding='utf-8') as f:
                frq_cache[frq_file] = json.load(f)

        # Find the FRQ by question number
        frq_data = None
        for frq in frq_cache[frq_file]:
            if frq['frq_metadata']['question_number'] == q_num:
                frq_data = frq
                break

        if frq_data is None:
            print(f"  SKIP: Q{q_num} not found in {frq_file}")
            skipped += 1
            continue

        # Find the target concept
        ti, ci, concept = find_concept(content_data, concept_slug)
        if concept is None:
            print(f"  SKIP: Concept '{concept_slug}' not found in content JSON")
            skipped += 1
            continue

        # Check if this FRQ is already appended (by matching frq_metadata)
        problems = concept['problem_sets'][0]['problems']
        already_exists = any(
            p.get('frq_metadata', {}).get('exam_year') == entry['exam_year']
            and p.get('frq_metadata', {}).get('question_number') == q_num
            for p in problems
        )
        if already_exists:
            print(f"  SKIP: {entry['exam_year']} Q{q_num} already in '{concept_slug}'")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  WOULD APPEND: {entry['exam_year']} AB Q{q_num} -> '{concept_slug}' "
                  f"(currently {len(problems)} problems)")
        else:
            problems.append(frq_data)
            print(f"  APPENDED: {entry['exam_year']} AB Q{q_num} -> '{concept_slug}' "
                  f"(now {len(problems)} problems)")
        appended += 1

    # Write back if not dry-run
    if not args.dry_run and appended > 0:
        with open(args.content, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)
        print(f"\nDone: {appended} FRQs appended, {skipped} skipped. File saved.")
    elif args.dry_run:
        print(f"\nDry run: {appended} FRQs would be appended, {skipped} would be skipped.")
    else:
        print(f"\nNo changes needed. {skipped} skipped.")


if __name__ == '__main__':
    main()
