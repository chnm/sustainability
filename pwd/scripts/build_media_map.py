#!/usr/bin/env python3
"""Build a media map from the media catalog for Hugo data templates.

Reads the media catalog JSON (produced by fetch_media.py --catalog-only)
and groups media filenames by their parent item ID. The output is a JSON
file that Hugo templates use to resolve image_id → list of filenames.

Usage:
    python3 scripts/build_media_map.py
"""

import json
import os
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUGO_DIR = os.path.dirname(SCRIPT_DIR)
CATALOG_PATH = os.path.join(HUGO_DIR, "static-media", "files", "media_catalog.json")
OUTPUT_PATH = os.path.join(HUGO_DIR, "data", "media_map.json")


def main():
    if not os.path.exists(CATALOG_PATH):
        print(f"ERROR: Media catalog not found at {CATALOG_PATH}", file=sys.stderr)
        print("Run: python3 scripts/fetch_media.py --catalog-only", file=sys.stderr)
        sys.exit(1)

    with open(CATALOG_PATH, "r") as f:
        catalog = json.load(f)

    print(f"Loaded {len(catalog)} media records from catalog")

    # Group filenames by item_id
    media_map = defaultdict(list)
    skipped = 0
    for record in catalog:
        item_id = record.get("item_id")
        filename = record.get("filename")
        if not item_id or not filename:
            skipped += 1
            continue
        media_map[str(item_id)].append(filename)

    print(f"Grouped into {len(media_map)} items ({skipped} records skipped)")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(media_map, f, separators=(",", ":"))

    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"Wrote {OUTPUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
