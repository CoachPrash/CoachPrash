#!/usr/bin/env python3
"""Migrate diagram references from manifests + inline HTML into content JSON fields.

After this migration:
- Each problem with a diagram has a "diagram" object in the content JSON
- Each concept with diagrams has a "diagrams" array in the content JSON
- All inline <figure class="concept-diagram"> tags are stripped from HTML fields
- The seed process (content_loader.py) builds <figure> tags at load time

Usage:
    python scripts/migrate_diagrams_to_problems.py [--dry-run]
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Map each manifest to its content JSON file
MANIFEST_CONTENT_MAP = {
    'scripts/manifests/physics.json': 'content/physics_ap_physics_1_mechanics.json',
    'scripts/manifests/calculus.json': 'content/math_ap_calculus_ab_bc.json',
    'scripts/manifests/statistics.json': 'content/math_ap_statistics.json',
}

FIGURE_PATTERN = re.compile(
    r'<figure class="concept-diagram">.*?</figure>\s*',
    re.DOTALL,
)


def strip_figures(html):
    """Remove all <figure class="concept-diagram">...</figure> from HTML."""
    return FIGURE_PATTERN.sub('', html).strip()


def process_course(manifest_path, content_path, dry_run=False):
    """Migrate one course's diagrams from manifest+inline into content JSON fields."""
    with open(manifest_path) as f:
        manifest = json.load(f)
    with open(content_path, encoding='utf-8') as f:
        content = json.load(f)

    # Index manifest entries by concept_slug
    concept_entries = {}  # slug -> list of content_html entries
    problem_entries = {}  # slug -> list of question_html entries
    for entry in manifest['images']:
        slug = entry['concept_slug']
        if entry['location'] == 'content_html':
            concept_entries.setdefault(slug, []).append(entry)
        elif entry['location'] == 'question_html':
            problem_entries.setdefault(slug, []).append(entry)

    stats = {
        'concept_diagrams_added': 0,
        'problem_diagrams_added': 0,
        'figures_stripped_content': 0,
        'figures_stripped_questions': 0,
        'warnings': [],
    }

    for topic in content.get('topics', []):
        for concept in topic.get('concepts', []):
            slug = concept.get('slug', '')

            # --- Concept-level diagrams ---
            c_entries = concept_entries.get(slug, [])
            if c_entries:
                concept['diagrams'] = [
                    {
                        'bucket_key': e['bucket_key'],
                        'alt_text': e['alt_text'],
                        'caption': e.get('description', ''),
                    }
                    for e in c_entries
                ]
                stats['concept_diagrams_added'] += len(c_entries)

            # Strip inline figures from content_html
            html = concept.get('content_html', '')
            if '<figure' in html:
                stripped = strip_figures(html)
                count = len(FIGURE_PATTERN.findall(html))
                stats['figures_stripped_content'] += count
                concept['content_html'] = stripped

            # --- Problem-level diagrams ---
            p_entries = problem_entries.get(slug, [])
            if p_entries:
                # Flatten all problems across problem sets
                problems = []
                for ps in concept.get('problem_sets', []):
                    problems.extend(ps.get('problems', []))

                for entry in p_entries:
                    pi = entry.get('problem_index')
                    if pi is None or pi >= len(problems):
                        stats['warnings'].append(
                            f"{entry['id']}: problem_index {pi} invalid for {slug} "
                            f"(has {len(problems)} problems)"
                        )
                        continue
                    problems[pi]['diagram'] = {
                        'bucket_key': entry['bucket_key'],
                        'alt_text': entry['alt_text'],
                        'caption': entry.get('description', ''),
                    }
                    stats['problem_diagrams_added'] += 1

            # Strip inline figures from all question_html
            for ps in concept.get('problem_sets', []):
                for prob in ps.get('problems', []):
                    qhtml = prob.get('question_html', '')
                    if '<figure' in qhtml:
                        prob['question_html'] = strip_figures(qhtml)
                        stats['figures_stripped_questions'] += 1

    # Report
    course_name = Path(content_path).stem
    print(f"\n{'='*60}")
    print(f"  {course_name}")
    print(f"{'='*60}")
    print(f"  Concept diagrams added:     {stats['concept_diagrams_added']}")
    print(f"  Problem diagrams added:     {stats['problem_diagrams_added']}")
    print(f"  Figures stripped (content):  {stats['figures_stripped_content']}")
    print(f"  Figures stripped (question): {stats['figures_stripped_questions']}")
    if stats['warnings']:
        print(f"  Warnings ({len(stats['warnings'])}):")
        for w in stats['warnings']:
            print(f"    WARN: {w}")

    if not dry_run:
        with open(content_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"  Wrote {content_path}")

    return stats


def main():
    parser = argparse.ArgumentParser(description='Migrate diagrams into content JSON fields')
    parser.add_argument('--dry-run', action='store_true', help='Print changes without modifying files')
    args = parser.parse_args()

    total = {
        'concept_diagrams_added': 0,
        'problem_diagrams_added': 0,
        'figures_stripped_content': 0,
        'figures_stripped_questions': 0,
        'warnings': [],
    }

    for manifest_path, content_path in MANIFEST_CONTENT_MAP.items():
        if not Path(manifest_path).exists():
            print(f"Skipping {manifest_path} (not found)")
            continue
        if not Path(content_path).exists():
            print(f"Skipping {content_path} (not found)")
            continue

        stats = process_course(manifest_path, content_path, dry_run=args.dry_run)
        for key in ('concept_diagrams_added', 'problem_diagrams_added',
                     'figures_stripped_content', 'figures_stripped_questions'):
            total[key] += stats[key]
        total['warnings'].extend(stats['warnings'])

    print(f"\n{'='*60}")
    print(f"  TOTALS")
    print(f"{'='*60}")
    print(f"  Concept diagrams:  {total['concept_diagrams_added']}")
    print(f"  Problem diagrams:  {total['problem_diagrams_added']}")
    print(f"  Figures stripped:  {total['figures_stripped_content'] + total['figures_stripped_questions']}")
    if total['warnings']:
        print(f"  Warnings:          {len(total['warnings'])}")

    if args.dry_run:
        print("\n  [DRY RUN — no files modified]")

    return 1 if total['warnings'] else 0


if __name__ == '__main__':
    sys.exit(main())
