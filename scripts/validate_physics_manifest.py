#!/usr/bin/env python3
"""Validate physics manifest entries before rendering.

Usage:
    python scripts/validate_physics_manifest.py --manifest scripts/manifests/physics.json --content content/physics_ap_physics_1_mechanics.json
"""
import argparse
import json
import sys

VALID_TYPES = {
    'free_body_diagram', 'motion_graph', 'vector_diagram', 'energy_bar_chart',
    'collision_diagram', 'circular_motion', 'shm_diagram', 'torque_diagram',
    'fluid_diagram',
}

REQUIRED_FIELDS = ['id', 'bucket_key', 'category', 'concept_slug', 'location',
                   'description', 'alt_text', 'params']

FORCE_TYPES = {'gravity', 'normal', 'friction', 'tension', 'applied', 'spring', 'net'}


def validate(manifest_path, content_path):
    with open(manifest_path) as f:
        manifest = json.load(f)
    with open(content_path, encoding='utf-8') as f:
        content = json.load(f)

    # Collect valid concept slugs
    valid_slugs = set()
    concept_problem_counts = {}
    for topic in content.get('topics', []):
        for concept in topic.get('concepts', []):
            slug = concept.get('slug', '')
            valid_slugs.add(slug)
            n_problems = sum(len(ps.get('problems', []))
                             for ps in concept.get('problem_sets', []))
            concept_problem_counts[slug] = n_problems

    images = manifest.get('images', [])
    errors = []
    warnings = []
    seen_ids = set()
    seen_keys = set()

    for i, entry in enumerate(images):
        eid = entry.get('id', f'entry-{i}')

        # Required fields
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f'{eid}: missing required field "{field}"')

        # Duplicate checks
        if eid in seen_ids:
            errors.append(f'{eid}: duplicate id')
        seen_ids.add(eid)

        bk = entry.get('bucket_key', '')
        if bk in seen_keys:
            errors.append(f'{eid}: duplicate bucket_key "{bk}"')
        seen_keys.add(bk)

        # Category
        if entry.get('category') != 'mechanics':
            errors.append(f'{eid}: category should be "mechanics", got "{entry.get("category")}"')

        # Concept slug
        slug = entry.get('concept_slug', '')
        if slug not in valid_slugs:
            errors.append(f'{eid}: concept_slug "{slug}" not found in content JSON')

        # Location / problem_index
        loc = entry.get('location', '')
        if loc not in ('content_html', 'question_html'):
            errors.append(f'{eid}: invalid location "{loc}"')
        if loc == 'question_html':
            pi = entry.get('problem_index')
            if pi is None:
                errors.append(f'{eid}: question_html location requires problem_index')
            elif not isinstance(pi, int) or pi < 0:
                errors.append(f'{eid}: problem_index must be non-negative integer')
            elif slug in concept_problem_counts and pi >= concept_problem_counts[slug]:
                errors.append(f'{eid}: problem_index {pi} out of range (concept "{slug}" has {concept_problem_counts[slug]} problems)')

        # Params validation
        params = entry.get('params', {})
        dtype = params.get('type', '')
        if dtype not in VALID_TYPES:
            errors.append(f'{eid}: unknown diagram type "{dtype}"')

        # Type-specific checks
        if dtype == 'free_body_diagram':
            forces = params.get('forces', [])
            if not forces:
                warnings.append(f'{eid}: FBD has no forces')
            for fi, force in enumerate(forces):
                if force.get('type') and force['type'] not in FORCE_TYPES:
                    errors.append(f'{eid}: force[{fi}] unknown type "{force["type"]}"')
                if 'angle_deg' not in force:
                    errors.append(f'{eid}: force[{fi}] missing angle_deg')

        elif dtype == 'motion_graph':
            if not params.get('segments'):
                errors.append(f'{eid}: motion_graph has no segments')

        elif dtype == 'energy_bar_chart':
            if not params.get('states'):
                errors.append(f'{eid}: energy_bar_chart has no states')

        elif dtype == 'collision_diagram':
            if not params.get('before'):
                errors.append(f'{eid}: collision_diagram has no "before" objects')
            if not params.get('after'):
                errors.append(f'{eid}: collision_diagram has no "after" objects')

        elif dtype == 'vector_diagram':
            if not params.get('vectors'):
                errors.append(f'{eid}: vector_diagram has no vectors')

        # Bucket key format
        if bk and not bk.startswith('images/physics/ap-physics-1-mechanics/'):
            errors.append(f'{eid}: bucket_key should start with "images/physics/ap-physics-1-mechanics/"')
        if bk and not bk.endswith('.svg'):
            errors.append(f'{eid}: bucket_key should end with .svg')

    # Summary
    print(f'Validated {len(images)} entries')
    print(f'  Concept slugs covered: {len(set(e.get("concept_slug") for e in images))} / {len(valid_slugs)}')
    print(f'  Content diagrams: {sum(1 for e in images if e.get("location") == "content_html")}')
    print(f'  Problem diagrams: {sum(1 for e in images if e.get("location") == "question_html")}')

    if warnings:
        print(f'\nWarnings ({len(warnings)}):')
        for w in warnings:
            print(f'  WARN: {w}')

    if errors:
        print(f'\nErrors ({len(errors)}):')
        for e in errors:
            print(f'  FAIL: {e}')
        return 1

    print('\nOK - All entries valid')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--content', required=True)
    args = parser.parse_args()
    sys.exit(validate(args.manifest, args.content))
