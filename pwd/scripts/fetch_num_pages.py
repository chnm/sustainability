#!/usr/bin/env python3
"""
Fetch bibo:numPages for all Document items and patch frontmatter.

Paginates the Omeka S API to collect numPages values, then updates
each document's frontmatter with num_pages and fixes the images list
to include page_start through page_start + num_pages - 1.

Usage:
    python3 scripts/fetch_num_pages.py
    python3 scripts/fetch_num_pages.py --dry-run
"""

import json
import os
import re
import sys
import time

import requests

API_BASE = "https://www.wardepartmentpapers.org/api"
PER_PAGE = 100
DELAY = 0.1

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUGO_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(HUGO_DIR, "content", "document")
MEDIA_MAP_PATH = os.path.join(HUGO_DIR, "data", "media_map.json")


def get_resource_type(item):
    types = item.get("@type", [])
    for t in types:
        if ":" in t and not t.startswith("o:"):
            return t.split(":")[1]
    return "Unknown"


def fetch_num_pages_map():
    """Fetch numPages for all Document items from the API."""
    resp = requests.get(f"{API_BASE}/items", params={"per_page": 1})
    resp.raise_for_status()
    total = int(resp.headers.get("Omeka-S-Total-Results", 0))
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    print(f"Total items: {total} ({total_pages} pages)")

    num_pages_map = {}  # omeka_id -> num_pages (only where > 1)
    page = 1

    while True:
        try:
            resp = requests.get(
                f"{API_BASE}/items",
                params={"per_page": PER_PAGE, "page": page, "sort_by": "id", "sort_order": "asc"},
            )
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break

            for item in items:
                if get_resource_type(item) != "Document":
                    continue
                np_vals = item.get("bibo:numPages", [])
                if not np_vals:
                    continue
                np = np_vals[0].get("@value", "")
                if np and np != "1":
                    num_pages_map[item["o:id"]] = int(np)

            if page % 50 == 0:
                print(f"  Page {page}/{total_pages} ({len(num_pages_map)} multi-page docs found)")

            page += 1
            time.sleep(DELAY)

        except requests.exceptions.RequestException as e:
            print(f"  Network error on page {page}: {e}", file=sys.stderr)
            print("  Retrying in 5 seconds...")
            time.sleep(5)
            continue

    print(f"Found {len(num_pages_map)} documents with numPages > 1")
    return num_pages_map


def patch_documents(num_pages_map, media_map, dry_run=False):
    """Patch frontmatter: add num_pages and fix images list."""
    stats = {"patched_numpages": 0, "patched_images": 0, "errors": 0}

    for omeka_id, num_pages in sorted(num_pages_map.items()):
        filepath = os.path.join(CONTENT_DIR, f"{omeka_id}.md")
        if not os.path.exists(filepath):
            continue

        try:
            with open(filepath) as f:
                content = f.read()

            if not content.startswith("---"):
                continue

            second_sep = content.index("---", 3)
            frontmatter = content[3:second_sep]
            body = content[second_sep + 3:]

            changed = False

            # Add num_pages if not present
            if "\nnum_pages:" not in frontmatter:
                # Insert after page_start line
                ps_match = re.search(r'^(page_start:\s*.+)$', frontmatter, re.MULTILINE)
                if ps_match:
                    old_line = ps_match.group(0)
                    frontmatter = frontmatter.replace(
                        old_line,
                        f"{old_line}\nnum_pages: '{num_pages}'",
                        1,
                    )
                    changed = True
                    stats["patched_numpages"] += 1

            # Fix images list using page_start + num_pages
            img_match = re.search(r'^omeka_image_id:\s*(\d+)', frontmatter, re.MULTILINE)
            ps_match = re.search(r'^page_start:\s*["\x27]?(\d+)', frontmatter, re.MULTILINE)
            if img_match and ps_match:
                image_id = img_match.group(1)
                page_start = int(ps_match.group(1))
                all_files = media_map.get(image_id, [])

                end_page = page_start + num_pages - 1
                if page_start >= 1 and end_page <= len(all_files):
                    correct_images = all_files[page_start - 1:end_page]

                    # Replace images block
                    new_images = "images:\n" + "".join(f"- {fn}\n" for fn in correct_images)
                    frontmatter = re.sub(
                        r'^images:\s*\[?\]?\s*\n(?:- .+\n)*',
                        new_images,
                        frontmatter,
                        count=1,
                        flags=re.MULTILINE,
                    )
                    changed = True
                    stats["patched_images"] += 1

            if changed and not dry_run:
                new_content = "---" + frontmatter + "---" + body
                with open(filepath, "w") as f:
                    f.write(new_content)

        except Exception as e:
            print(f"  ERROR on {omeka_id}: {e}")
            stats["errors"] += 1

    return stats


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN ===\n")

    # Step 1: Fetch numPages from API
    print("Fetching numPages from API...")
    num_pages_map = fetch_num_pages_map()

    # Step 2: Load media map
    print(f"\nLoading {MEDIA_MAP_PATH}...")
    with open(MEDIA_MAP_PATH) as f:
        media_map = json.load(f)

    # Step 3: Patch documents
    print(f"\nPatching {len(num_pages_map)} documents...")
    stats = patch_documents(num_pages_map, media_map, dry_run)

    print(f"\n{'=' * 50}")
    print(f"Done{'  (DRY RUN)' if dry_run else ''}")
    print(f"  num_pages added: {stats['patched_numpages']}")
    print(f"  images fixed:    {stats['patched_images']}")
    print(f"  errors:          {stats['errors']}")


if __name__ == "__main__":
    main()
