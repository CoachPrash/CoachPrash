#!/usr/bin/env python3
"""Batch generate diagram images from a manifest file.

Usage:
    python scripts/generate_diagrams.py --manifest scripts/manifests/calculus.json --output scripts/output
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from diagram_renderers import (
    function_graph,
    shaded_region,
    slope_field,
    concept_diagram,
    solid_revolution,
    parametric_polar,
    series_visual,
    statistics,
    mechanics,
)

RENDERERS = {
    'function_graph': function_graph,
    'shaded_region': shaded_region,
    'slope_field': slope_field,
    'concept_diagram': concept_diagram,
    'solid_revolution': solid_revolution,
    'parametric_polar': parametric_polar,
    'series_visual': series_visual,
    'statistics': statistics,
    'mechanics': mechanics,
}


def main():
    parser = argparse.ArgumentParser(description='Generate diagram images from manifest')
    parser.add_argument('--manifest', required=True, help='Path to manifest JSON')
    parser.add_argument('--output', required=True, help='Output directory for images')
    parser.add_argument('--category', help='Only generate images of this category')
    parser.add_argument('--id', help='Only generate image with this ID')
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    images = manifest['images']

    # Filter if requested
    if args.category:
        images = [img for img in images if img['category'] == args.category]
    if args.id:
        images = [img for img in images if img['id'] == args.id]

    total = len(images)
    success = 0
    errors = []

    print(f"Generating {total} images...")
    print(f"Output directory: {output_dir}")
    print("-" * 60)

    for i, entry in enumerate(images, 1):
        category = entry['category']
        image_id = entry['id']
        filename = entry['bucket_key'].split('/')[-1]

        renderer = RENDERERS.get(category)
        if not renderer:
            print(f"[{i}/{total}] SKIP {image_id}: Unknown category '{category}'")
            errors.append((image_id, f"Unknown category: {category}"))
            continue

        try:
            path = renderer.render(entry, output_dir)
            size_kb = path.stat().st_size / 1024
            print(f"[{i}/{total}] OK   {image_id}: {filename} ({size_kb:.1f} KB)")
            success += 1
        except Exception as e:
            print(f"[{i}/{total}] FAIL {image_id}: {e}")
            errors.append((image_id, str(e)))

    print("-" * 60)
    print(f"Results: {success}/{total} generated successfully")
    if errors:
        print(f"\nFailed ({len(errors)}):")
        for eid, err in errors:
            print(f"  {eid}: {err}")

    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
