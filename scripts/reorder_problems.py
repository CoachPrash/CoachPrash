"""Reorder problems in all qhsJSON content files.

Standard order per concept (10 problems):
  MCQ free, MCQ free, MCQ premium, MCQ premium,
  FTB free, FTB free, FTB premium, FTB premium,
  FRQ premium, FRQ premium

Rules:
- Group by type: MCQ first, then FTB, then FRQ
- Within each type group: free problems first, then premium
- Within each sub-group: preserve original relative order
- Fix tier mismatches: exactly 2 free MCQ, 2 free FTB, all FRQ premium
- Set display_order sequentially 0-9
"""
import json
import glob
import os
import sys


def reorder_problems(problems):
    """Reorder and fix tiers for a list of problems. Returns (new_list, changes)."""
    changes = []

    # Separate by type
    mcqs = [p for p in problems if p.get('problem_type') == 'mcq']
    ftbs = [p for p in problems if p.get('problem_type') == 'ftb']
    frqs = [p for p in problems if p.get('problem_type') == 'frq']
    others = [p for p in problems if p.get('problem_type') not in ('mcq', 'ftb', 'frq')]

    # Fix tiers within each type group
    # MCQ: first 2 free, rest premium
    for i, p in enumerate(mcqs):
        expected = 'free' if i < 2 else 'premium'
        if p.get('access_tier') != expected:
            changes.append(f"MCQ[{i}]: {p.get('access_tier')} -> {expected}")
            p['access_tier'] = expected

    # FTB: first 2 free, rest premium
    for i, p in enumerate(ftbs):
        expected = 'free' if i < 2 else 'premium'
        if p.get('access_tier') != expected:
            changes.append(f"FTB[{i}]: {p.get('access_tier')} -> {expected}")
            p['access_tier'] = expected

    # FRQ: all premium
    for i, p in enumerate(frqs):
        if p.get('access_tier') != 'premium':
            changes.append(f"FRQ[{i}]: {p.get('access_tier')} -> premium")
            p['access_tier'] = 'premium'

    # Assemble in order: MCQ, FTB, FRQ, others
    ordered = mcqs + ftbs + frqs + others

    # Set display_order
    for i, p in enumerate(ordered):
        p['display_order'] = i

    return ordered, changes


def process_file(filepath, dry_run=False):
    """Process a single qhsJSON file. Returns (concepts_changed, total_changes)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    filename = os.path.basename(filepath)
    concepts_changed = 0
    total_changes = []

    for topic in data.get('topics', []):
        for concept in topic.get('concepts', []):
            slug = concept.get('slug', '?')
            for ps in concept.get('problem_sets', []):
                problems = ps.get('problems', [])
                if not problems:
                    continue

                # Check current order
                types_before = [p.get('problem_type') for p in problems]
                tiers_before = [p.get('access_tier') for p in problems]

                new_problems, changes = reorder_problems(problems)

                types_after = [p.get('problem_type') for p in new_problems]
                tiers_after = [p.get('access_tier') for p in new_problems]

                # Check if anything actually changed
                if types_before != types_after or tiers_before != tiers_after:
                    concepts_changed += 1
                    if changes:
                        for c in changes:
                            total_changes.append(f"  {slug}: {c}")

                    if types_before != types_after:
                        total_changes.append(f"  {slug}: reordered {types_before} -> {types_after}")

                    ps['problems'] = new_problems

    if concepts_changed > 0 and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')

    return concepts_changed, total_changes


def main():
    dry_run = '--dry-run' in sys.argv
    content_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content')
    files = sorted(glob.glob(os.path.join(content_dir, '*.json')))

    total_files_changed = 0
    total_concepts_changed = 0

    for fp in files:
        fn = os.path.basename(fp)
        if fn == 'qhsjson_schema.json':
            continue

        concepts_changed, changes = process_file(fp, dry_run)

        if concepts_changed > 0:
            total_files_changed += 1
            total_concepts_changed += concepts_changed
            status = "[DRY RUN]" if dry_run else "[UPDATED]"
            print(f"{status} {fn}: {concepts_changed} concepts fixed")
            for c in changes:
                print(c)
        else:
            print(f"[OK] {fn}: no changes needed")

    print(f"\nSummary: {total_files_changed} files, {total_concepts_changed} concepts {'would be ' if dry_run else ''}updated")


if __name__ == '__main__':
    main()
