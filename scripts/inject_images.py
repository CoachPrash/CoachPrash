#!/usr/bin/env python3
"""Inject <img> tags into content JSON based on the diagram manifest.

Usage:
    python scripts/inject_images.py --manifest scripts/manifests/calculus.json --content content/math_ap_calculus_ab_bc.json
"""
import argparse
import json
import sys
from pathlib import Path


def build_img_tag(entry):
    """Build an HTML figure+img tag from a manifest entry."""
    bucket_key = entry['bucket_key']
    alt_text = entry.get('alt_text', entry.get('description', ''))
    caption = entry.get('description', '')

    return (
        f'<figure class="concept-diagram">'
        f'<img data-bucket-key=\'{bucket_key}\' alt=\'{alt_text}\' '
        f'loading=\'lazy\' />'
        f'<figcaption>{caption}</figcaption>'
        f'</figure>'
    )


def inject_into_content_html(concept, entries):
    """Insert diagram tags into a concept's content_html."""
    html = concept.get('content_html', '')
    # Append content_html diagrams at the end of content
    for entry in entries:
        html += '\n' + build_img_tag(entry)
    concept['content_html'] = html


def inject_into_question_html(problem, entry):
    """Prepend a diagram to a problem's question_html."""
    html = problem.get('question_html', '')
    # Insert diagram before the question text
    problem['question_html'] = build_img_tag(entry) + '\n' + html


def main():
    parser = argparse.ArgumentParser(description='Inject image tags into content JSON')
    parser.add_argument('--manifest', required=True, help='Path to manifest JSON')
    parser.add_argument('--content', required=True, help='Path to content JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Print changes without modifying')
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)

    with open(args.content, encoding='utf-8') as f:
        content = json.load(f)

    # Index manifest entries by concept_slug
    by_concept = {}
    for entry in manifest['images']:
        slug = entry['concept_slug']
        by_concept.setdefault(slug, []).append(entry)

    injected = 0
    skipped = 0

    # Walk through all concepts in all topics
    for topic in content.get('topics', []):
        for concept in topic.get('concepts', []):
            slug = concept.get('slug', '')
            entries = by_concept.get(slug, [])
            if not entries:
                continue

            content_entries = [e for e in entries if e['location'] == 'content_html']
            question_entries = [e for e in entries if e['location'] == 'question_html']

            # Inject content_html diagrams
            if content_entries:
                if args.dry_run:
                    for e in content_entries:
                        print(f"WOULD inject {e['id']} into {slug} content_html")
                else:
                    inject_into_content_html(concept, content_entries)
                injected += len(content_entries)

            # Inject question_html diagrams
            for entry in question_entries:
                problem_index = entry.get('problem_index')
                if problem_index is None:
                    skipped += 1
                    continue

                # Find the problem at the specified index
                problem_sets = concept.get('problem_sets', [])
                if not problem_sets:
                    skipped += 1
                    continue

                # Flatten problems across all problem sets
                problems = []
                for ps in problem_sets:
                    problems.extend(ps.get('problems', []))
                if problem_index >= len(problems):
                    print(f"WARNING: {entry['id']} problem_index {problem_index} "
                          f"out of range for {slug} (has {len(problems)} problems)")
                    skipped += 1
                    continue

                if args.dry_run:
                    print(f"WOULD inject {entry['id']} into {slug} problem[{problem_index}]")
                else:
                    inject_into_question_html(problems[problem_index], entry)
                injected += 1

    if not args.dry_run:
        with open(args.content, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"Updated {args.content}")

    print(f"Results: {injected} images injected, {skipped} skipped")
    return 0


if __name__ == '__main__':
    sys.exit(main())
