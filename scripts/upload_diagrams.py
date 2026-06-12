#!/usr/bin/env python3
"""Batch upload generated diagram images to Railway storage bucket.

Usage:
    python scripts/upload_diagrams.py --manifest scripts/manifests/calculus.json --output scripts/output
"""
import argparse
import json
import sys
import os
from pathlib import Path

# Add project root to path so we can import app utilities
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env for local development (Railway sets env vars directly)
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser(description='Upload diagram images to Railway bucket')
    parser.add_argument('--manifest', required=True, help='Path to manifest JSON')
    parser.add_argument('--output', required=True, help='Directory containing generated images')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be uploaded without uploading')
    args = parser.parse_args()

    # Verify bucket env vars
    if not args.dry_run and not os.environ.get('AWS_ENDPOINT_URL'):
        print("ERROR: AWS_ENDPOINT_URL not set. Set Railway bucket env vars or use --dry-run.")
        return 1

    manifest_path = Path(args.manifest)
    output_dir = Path(args.output)

    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    images = manifest['images']
    total = len(images)
    success = 0
    errors = []
    skipped = 0

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Uploading {total} images...")
    print(f"Source: {output_dir}")
    print("-" * 60)

    for i, entry in enumerate(images, 1):
        bucket_key = entry['bucket_key']
        filename = bucket_key.split('/')[-1]
        local_path = output_dir / filename

        if not local_path.exists():
            print(f"[{i}/{total}] SKIP {entry['id']}: {filename} not found locally")
            skipped += 1
            continue

        if args.dry_run:
            size_kb = local_path.stat().st_size / 1024
            print(f"[{i}/{total}] WOULD upload {filename} -> {bucket_key} ({size_kb:.1f} KB)")
            success += 1
            continue

        try:
            from app.utils.storage import upload_file

            # Determine content type
            ext = local_path.suffix.lower()
            content_types = {
                '.svg': 'image/svg+xml',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
            }
            content_type = content_types.get(ext, 'application/octet-stream')

            with open(local_path, 'rb') as f:
                upload_file(f, bucket_key, content_type=content_type)

            size_kb = local_path.stat().st_size / 1024
            print(f"[{i}/{total}] OK   {entry['id']}: {bucket_key} ({size_kb:.1f} KB)")
            success += 1
        except Exception as e:
            print(f"[{i}/{total}] FAIL {entry['id']}: {e}")
            errors.append((entry['id'], str(e)))

    print("-" * 60)
    print(f"Results: {success} uploaded, {skipped} skipped, {len(errors)} failed")
    if errors:
        print(f"\nFailed ({len(errors)}):")
        for eid, err in errors:
            print(f"  {eid}: {err}")

    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
