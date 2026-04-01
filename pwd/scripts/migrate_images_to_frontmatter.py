#!/usr/bin/env python3
"""
Migrate image references from data/media_map.json lookup to inline YAML frontmatter.

For each document in content/document/:
- Reads the image_id from frontmatter
- Looks up filenames in data/media_map.json
- Adds an `images:` list to frontmatter
- Renames `image_id` to `omeka_image_id` for reference
- Preserves the markdown body exactly

Usage:
    python3 scripts/migrate_images_to_frontmatter.py
    python3 scripts/migrate_images_to_frontmatter.py --dry-run
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
        "processed": 0,
        "migrated": 0,
        "no_image_id": 0,
        "not_in_map": 0,
        "already_migrated": 0,
        "errors": 0,
    }

    for i, filepath in enumerate(md_files):
        if (i + 1) % 5000 == 0:
            print(f"  Progress: {i + 1}/{len(md_files)}...")

        try:
            with open(filepath) as f:
                content = f.read()

            # Verify frontmatter structure
            if not content.startswith("---"):
                stats["errors"] += 1
                continue

            # Find end of frontmatter
            second_sep = content.index("---", 3)
            frontmatter = content[3:second_sep]
            body = content[second_sep + 3:]

            # Check if already migrated
            if "\nimages:" in frontmatter or frontmatter.startswith("images:"):
                stats["already_migrated"] += 1
                stats["processed"] += 1
                continue

            # Find image_id line
            image_id_match = re.search(r'^image_id:\s*(.+)$', frontmatter, re.MULTILINE)
            if not image_id_match:
                stats["no_image_id"] += 1
                stats["processed"] += 1
                continue

            image_id_str = image_id_match.group(1).strip().strip("'\"")

            # Look up in media map
            filenames = media_map.get(image_id_str, [])
            if not filenames:
                print(f"  WARNING: image_id {image_id_str} not in media_map ({filepath.name})")
                stats["not_in_map"] += 1

            # Build the images block
            if filenames:
                images_block = "images:\n" + "".join(f"- {fn}\n" for fn in filenames)
            else:
                images_block = "images: []\n"

            # Replace `image_id: XXXX` with `omeka_image_id: XXXX` and add images block
            # The images block goes right after the renamed line
            old_line = image_id_match.group(0)
            new_lines = f"omeka_image_id: {image_id_str}\n{images_block.rstrip()}"

            new_frontmatter = frontmatter.replace(old_line, new_lines, 1)

            new_content = "---" + new_frontmatter + "---" + body

            if not dry_run:
                with open(filepath, "w") as f:
                    f.write(new_content)

            stats["migrated"] += 1
            stats["processed"] += 1

        except Exception as e:
            print(f"  ERROR processing {filepath.name}: {e}")
            stats["errors"] += 1

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Migration complete{'  (DRY RUN)' if dry_run else ''}")
    print(f"{'=' * 50}")
    print(f"  Total files:       {len(md_files)}")
    print(f"  Processed:         {stats['processed']}")
    print(f"  Migrated:          {stats['migrated']}")
    print(f"  Already migrated:  {stats['already_migrated']}")
    print(f"  No image_id:       {stats['no_image_id']}")
    print(f"  Not in media_map:  {stats['not_in_map']}")
    print(f"  Errors:            {stats['errors']}")


if __name__ == "__main__":
    main()
