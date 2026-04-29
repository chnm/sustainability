#!/usr/bin/env python3
"""Migrate content/item/*.md files to type-specific directories.

For each .md file in content/item/:
  1. Read resource_type from YAML front matter
  2. Move to content/{type_dir}/
  3. Add /item/{id} alias for backward compatibility
  4. Remove 'type: item' (Hugo infers type from section)

Usage:
    python3 scripts/migrate_items.py              # full migration
    python3 scripts/migrate_items.py --dry-run    # preview only
"""

import os
import re
import shutil
import sys

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
ITEM_DIR = os.path.join(CONTENT_DIR, "item")

TYPE_DIRS = {
    "Document": "document",
    "Image": "image",
    "Name": "name",
    "Collection": "collection",
    "Repository": "repository",
    "Microfilm": "microfilm",
    "Publication": "publication",
}


def migrate_file(filepath, dry_run=False):
    """Migrate a single item file to its type-specific directory."""
    with open(filepath, "r") as f:
        content = f.read()

    # Extract resource_type
    m = re.search(r"^resource_type:\s*(.+)$", content, re.MULTILINE)
    if not m:
        return None, "no resource_type"

    resource_type = m.group(1).strip()
    type_dir = TYPE_DIRS.get(resource_type)
    if not type_dir:
        return None, f"unknown type: {resource_type}"

    # Extract omeka_id for the alias
    m_id = re.search(r"^omeka_id:\s*(\d+)$", content, re.MULTILINE)
    if not m_id:
        return None, "no omeka_id"
    omeka_id = m_id.group(1)

    # Add /item/{id} alias if not already present
    item_alias = f"/item/{omeka_id}"
    if item_alias not in content:
        # Find the aliases block and append
        content = re.sub(
            r"^(aliases:\n- /s/home/item/\d+)$",
            rf"\1\n- {item_alias}",
            content,
            flags=re.MULTILINE,
        )

    # Remove 'type: item' line
    content = re.sub(r"^type: item\n", "", content, flags=re.MULTILINE)

    # Destination
    dest_dir = os.path.join(CONTENT_DIR, type_dir)
    filename = os.path.basename(filepath)
    dest_path = os.path.join(dest_dir, filename)

    if dry_run:
        return type_dir, "would move"

    os.makedirs(dest_dir, exist_ok=True)
    with open(dest_path, "w") as f:
        f.write(content)
    os.remove(filepath)

    return type_dir, "moved"


def main():
    dry_run = "--dry-run" in sys.argv

    if not os.path.isdir(ITEM_DIR):
        print(f"No item directory found at {ITEM_DIR}")
        sys.exit(1)

    files = [f for f in os.listdir(ITEM_DIR) if f.endswith(".md") and f != "_index.md"]
    files.sort()

    counts = {}
    errors = []

    for i, filename in enumerate(files, 1):
        filepath = os.path.join(ITEM_DIR, filename)
        type_dir, status = migrate_file(filepath, dry_run=dry_run)

        if type_dir:
            counts[type_dir] = counts.get(type_dir, 0) + 1
        else:
            errors.append((filename, status))

        if i % 5000 == 0:
            print(f"  Processed {i}/{len(files)}...")

    action = "Would migrate" if dry_run else "Migrated"
    print(f"\n{action} {sum(counts.values())} files:")
    for type_dir, count in sorted(counts.items()):
        print(f"  {type_dir}: {count}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for filename, status in errors[:20]:
            print(f"  {filename}: {status}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more")


if __name__ == "__main__":
    main()
