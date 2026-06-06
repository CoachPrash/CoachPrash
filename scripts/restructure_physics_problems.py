#!/usr/bin/env python3
"""Restructure AP Physics 1 from 2 problem sets per concept to 1,
following the spec order: MCQ MCQ FTB FTB MCQ MCQ FTB FTB FRQ FRQ.

Keeps all existing problems, reorders them, merges into a single problem set.
Does NOT generate new problems — just reorganises what exists.

Usage:
    python scripts/restructure_physics_problems.py --content content/physics_ap_physics_1_mechanics.json [--dry-run]
"""
import argparse
import json
import re
import sys


SPEC_ORDER = ['mcq', 'mcq', 'ftb', 'ftb', 'mcq', 'mcq', 'ftb', 'ftb', 'frq', 'frq']


def strip_question_diagrams(problems):
    """Remove injected <figure class="concept-diagram">...</figure> from question_html."""
    pattern = r'<figure class="concept-diagram">.*?</figure>\s*'
    for p in problems:
        html = p.get('question_html', '')
        if '<figure' in html:
            p['question_html'] = re.sub(pattern, '', html, flags=re.DOTALL).strip()


def reorder_problems(problems):
    """Reorder problems into spec order using available problems.

    Target: MCQ MCQ FTB FTB MCQ MCQ FTB FTB FRQ FRQ
    If a type is short, leave gaps (shorter set). If excess, drop extras.
    """
    by_type = {'mcq': [], 'ftb': [], 'frq': []}
    for p in problems:
        t = p.get('problem_type', 'mcq')
        if t in by_type:
            by_type[t].append(p)

    ordered = []
    mcq_idx = ftb_idx = frq_idx = 0

    for slot_type in SPEC_ORDER:
        pool = by_type[slot_type]
        if slot_type == 'mcq':
            if mcq_idx < len(pool):
                ordered.append(pool[mcq_idx])
                mcq_idx += 1
        elif slot_type == 'ftb':
            if ftb_idx < len(pool):
                ordered.append(pool[ftb_idx])
                ftb_idx += 1
        elif slot_type == 'frq':
            if frq_idx < len(pool):
                ordered.append(pool[frq_idx])
                frq_idx += 1

    # Set display_order and difficulty tiers
    for i, p in enumerate(ordered):
        p['display_order'] = i
        # First 4 = easy/medium (free), next 4 = medium/hard, FRQs = hard
        if i < 2:
            p['difficulty'] = 'easy'
        elif i < 4:
            p['difficulty'] = 'medium'
        elif i < 8:
            p['difficulty'] = 'medium'
        else:
            p['difficulty'] = 'hard'
        # Remove access_tier from individual problems (set-level gating)
        p.pop('access_tier', None)

    return ordered


def restructure(content_path, dry_run=False):
    with open(content_path, encoding='utf-8') as f:
        data = json.load(f)

    report = []
    total_before = 0
    total_after = 0

    for topic in data.get('topics', []):
        for concept in topic.get('concepts', []):
            slug = concept.get('slug', '')

            # Flatten all problems across all problem sets
            all_problems = []
            for ps in concept.get('problem_sets', []):
                all_problems.extend(ps.get('problems', []))

            total_before += len(all_problems)

            # Strip diagram injections from question_html
            strip_question_diagrams(all_problems)

            # Reorder into spec format
            ordered = reorder_problems(all_problems)
            total_after += len(ordered)

            # Count what we have vs spec
            m = sum(1 for p in ordered if p['problem_type'] == 'mcq')
            f = sum(1 for p in ordered if p['problem_type'] == 'ftb')
            r = sum(1 for p in ordered if p['problem_type'] == 'frq')
            gaps = []
            if m < 4:
                gaps.append(f'{4-m} MCQ')
            if f < 4:
                gaps.append(f'{4-f} FTB')
            if r < 2:
                gaps.append(f'{2-r} FRQ')
            gap_str = ', '.join(gaps) if gaps else 'COMPLETE'
            report.append(f'  {slug}: {len(ordered)} problems ({m}M/{f}F/{r}R) - {gap_str}')

            # Replace with single problem set
            ps_title = concept.get('title', slug.replace('-', ' ').title())
            concept['problem_sets'] = [{
                'title': f'Practice: {ps_title}',
                'access_tier': 'free',
                'display_order': 0,
                'problems': ordered,
            }]

    # Print report
    print(f'Restructured {len(report)} concepts')
    print(f'Problems: {total_before} -> {total_after}')
    print()
    for line in report:
        print(line)

    # Count gaps
    need_mcq = sum(max(0, 4 - sum(1 for p in topic_concept_problems if p['problem_type'] == 'mcq'))
                   for topic in data['topics']
                   for c in topic['concepts']
                   for topic_concept_problems in [[p for ps in c['problem_sets'] for p in ps['problems']]])
    need_ftb = sum(max(0, 4 - sum(1 for p in [p2 for ps in c['problem_sets'] for p2 in ps['problems']] if p['problem_type'] == 'ftb'))
                   for topic in data['topics']
                   for c in topic['concepts'])
    need_frq = sum(max(0, 2 - sum(1 for p in [p2 for ps in c['problem_sets'] for p2 in ps['problems']] if p['problem_type'] == 'frq'))
                   for topic in data['topics']
                   for c in topic['concepts'])

    print(f'\nGaps remaining: {need_mcq} MCQ, {need_ftb} FTB, {need_frq} FRQ = {need_mcq+need_ftb+need_frq} total')

    if not dry_run:
        with open(content_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f'\nWrote {content_path}')
    else:
        print('\n[DRY RUN - no changes written]')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--content', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    restructure(args.content, args.dry_run)
