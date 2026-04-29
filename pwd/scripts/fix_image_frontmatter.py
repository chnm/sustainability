#!/usr/bin/env python3
"""
Fix document image frontmatter to use page_start for correct image selection.

The original migration dumped ALL media files for an Image item (microfilm reel)
into each document's `images:` list. In reality, each document references a
single page within the reel via `page_start` (1-indexed).

This script:
- Reads each document's `omeka_image_id` and `page_start`
- Looks up the ordered media list in data/media_map.json
- Replaces the `images:` list with the single correct file
- Documents without `page_start` get `images: []`

Usage:
    python3 scripts/fix_image_frontmatter.py
    python3 scripts/fix_image_frontmatter.py --dry-run
"""

import json
import os
import re
import sys
from pathlib import Path

HUGO_DIR = Path(__file__).parent.parent
CONTENT_DIR = HUGO_DIR / "content" / "document"
MEDIA_MAP_PATH = HUGO_DIR / "data" / "media_map.json"


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN (no files will be modified) ===\n")

    # Load media map
    print(f"Loading {MEDIA_MAP_PATH}...")
    with open(MEDIA_MAP_PATH) as f:
        media_map = json.load(f)
    print(f"  {len(media_map)} entries in media_map\n")

    # Collect all .md files (skip _index.md)
    md_files = sorted(
        p for p in CONTENT_DIR.glob("*.md")
        if p.name != "_index.md"
    )
    print(f"Found {len(md_files)} document files\n")

    stats = {
        "fixed": 0,
        "already_correct": 0,
        "no_image_id": 0,
        "no_page_start": 0,
        "page_start_out_of_range": 0,
        "not_in_map": 0,
        "errors": 0,
    }

    for i, filepath in enumerate(md_files):
        if (i + 1) % 5000 == 0:
            print(f"  Progress: {i + 1}/{len(md_files)}...")

        try:
            with open(filepath) as f:
                content = f.read()

            if not content.startswith("---"):
                stats["errors"] += 1
                continue

            # Split frontmatter and body
            second_sep = content.index("---", 3)
            frontmatter = content[3:second_sep]
            body = content[second_sep + 3:]

            # Find omeka_image_id
            img_match = re.search(r'^omeka_image_id:\s*(\d+)', frontmatter, re.MULTILINE)
            if not img_match:
                stats["no_image_id"] += 1
                continue

            image_id_str = img_match.group(1)

            # Look up media files
            all_files = media_map.get(image_id_str, [])
            if not all_files:
                stats["not_in_map"] += 1
                continue

            # Find page_start
            ps_match = re.search(r'^page_start:\s*["\x27]?(\d+)', frontmatter, re.MULTILINE)
            if not ps_match:
                # No page_start — set images to empty
                correct_images = []
                stats["no_page_start"] += 1
            else:
                page_start = int(ps_match.group(1))
                if page_start < 1 or page_start > len(all_files):
                    # page_start likely refers to a different pwd:image reel
                    # that we didn't capture (fetch_items only takes the first).
                    # Clear for now; these need a multi-image-ref fix later.
                    correct_images = []
                    stats["page_start_out_of_range"] += 1
                else:
                    correct_images = [all_files[page_start - 1]]

            # Check if already correct
            existing_match = re.search(
                r'^images:\s*\n((?:- .+\n)*)',
                frontmatter, re.MULTILINE
            )
            if existing_match:
                existing_images = [
                    line.lstrip("- ").strip()
                    for line in existing_match.group(1).strip().splitlines()
                    if line.strip()
                ]
            else:
                # Could be images: [] or no images at all
                existing_images = []

            if existing_images == correct_images:
                stats["already_correct"] += 1
                continue

            # Replace the images block in frontmatter
            if correct_images:
                new_images_block = "images:\n" + "".join(f"- {fn}\n" for fn in correct_images)
            else:
                new_images_block = "images: []\n"

            # Remove existing images block (multi-line list or empty list)
            # Match "images:\n- file1\n- file2\n..." or "images: []\n"
            new_frontmatter = re.sub(
                r'^images:\s*\[?\]?\s*\n(?:- .+\n)*',
                new_images_block,
                frontmatter,
                count=1,
                flags=re.MULTILINE,
            )

            new_content = "---" + new_frontmatter + "---" + body

            if not dry_run:
                with open(filepath, "w") as f:
                    f.write(new_content)

            stats["fixed"] += 1

        except Exception as e:
            print(f"  ERROR processing {filepath.name}: {e}")
            stats["errors"] += 1

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Fix complete{'  (DRY RUN)' if dry_run else ''}")
    print(f"{'=' * 50}")
    print(f"  Total files:            {len(md_files)}")
    print(f"  Fixed:                  {stats['fixed']}")
    print(f"  Already correct:        {stats['already_correct']}")
    print(f"  No omeka_image_id:      {stats['no_image_id']}")
    print(f"  No page_start (cleared):{stats['no_page_start']}")
    print(f"  page_start out of range:{stats['page_start_out_of_range']}")
    print(f"  Not in media_map:       {stats['not_in_map']}")
    print(f"  Errors:                 {stats['errors']}")


if __name__ == "__main__":
    main()
