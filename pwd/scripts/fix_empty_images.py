#!/usr/bin/env python3
"""
Fix documents that have omeka_image_id but empty images lists.

Resolves image filenames from data/media_map.json using page_start and
num_pages. For documents missing page_start, fetches it from the Omeka
S API (only for the specific items that need it).

Usage:
    python3 scripts/fix_empty_images.py --dry-run
    python3 scripts/fix_empty_images.py
"""

import json
import os
import re
import sys
import time
import urllib.request

API_BASE = "https://www.wardepartmentpapers.org/api"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HUGO_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(HUGO_DIR, "content", "document")
MEDIA_MAP_PATH = os.path.join(HUGO_DIR, "data", "media_map.json")

DELAY = 0.15  # seconds between API calls


def find_empty_image_docs():
    """Find all documents with images: [] and an omeka_image_id."""
    docs = []
    for fname in os.listdir(CONTENT_DIR):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        filepath = os.path.join(CONTENT_DIR, fname)
        with open(filepath) as f:
            content = f.read(3000)

        if not re.search(r"^images: \[\]", content, re.MULTILINE):
            continue

        m = re.search(r"^omeka_image_id:\s*(\d+)", content, re.MULTILINE)
        if not m:
            continue

        image_id = m.group(1)
        omeka_id = fname.replace(".md", "")

        ps_match = re.search(r"^page_start:\s*[\"']?(\d+)", content, re.MULTILINE)
        page_start = int(ps_match.group(1)) if ps_match else None

        np_match = re.search(r"^num_pages:\s*[\"']?(\d+)", content, re.MULTILINE)
        num_pages = int(np_match.group(1)) if np_match else None

        docs.append({
            "omeka_id": omeka_id,
            "image_id": image_id,
            "page_start": page_start,
            "num_pages": num_pages,
            "filepath": filepath,
        })

    return docs


def fetch_page_start(omeka_id):
    """Fetch bibo:pageStart for a single item from the API."""
    url = f"{API_BASE}/items/{omeka_id}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            item = json.loads(resp.read())
        vals = item.get("bibo:pageStart", [])
        if vals:
            val = vals[0].get("@value", "")
            if val and val.strip().isdigit():
                return int(val.strip())
    except Exception as e:
        print(f"  WARNING: API error for item {omeka_id}: {e}", file=sys.stderr)
    return None


def resolve_images(doc, media_map):
    """Resolve image filenames for a document. Returns list of filenames or None."""
    image_id = doc["image_id"]
    all_files = media_map.get(image_id)
    if not all_files:
        return None

    page_start = doc["page_start"] or 1
    num_pages = doc["num_pages"] or 1

    start_idx = page_start - 1
    end_idx = start_idx + num_pages

    if start_idx < 0 or start_idx >= len(all_files):
        return None

    # Clamp end to available files
    end_idx = min(end_idx, len(all_files))
    return all_files[start_idx:end_idx]


def patch_frontmatter(filepath, images):
    """Replace images: [] with the resolved image list in frontmatter."""
    with open(filepath) as f:
        content = f.read()

    new_images_block = "images:\n" + "".join(f"- {fn}\n" for fn in images)
    patched = re.sub(
        r"^images: \[\]\n",
        new_images_block,
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if patched == content:
        return False

    with open(filepath, "w") as f:
        f.write(patched)
    return True


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN ===\n")

    # Load media map
    print(f"Loading {MEDIA_MAP_PATH}...")
    with open(MEDIA_MAP_PATH) as f:
        media_map = json.load(f)

    # Find documents needing fixes
    print(f"Scanning {CONTENT_DIR}...")
    docs = find_empty_image_docs()
    print(f"Found {len(docs)} documents with images: [] and omeka_image_id")

    in_map = [d for d in docs if d["image_id"] in media_map]
    not_in_map = [d for d in docs if d["image_id"] not in media_map]
    print(f"  In media_map: {len(in_map)}")
    print(f"  Not in media_map (no images on Omeka): {len(not_in_map)}")

    # Split fixable docs by whether they need API fetching
    need_api = [d for d in in_map if d["page_start"] is None]
    local_fix = [d for d in in_map if d["page_start"] is not None]

    # For single-image entries without page_start, no API needed
    single_image = [d for d in need_api if len(media_map[d["image_id"]]) == 1]
    multi_image_need_api = [d for d in need_api if len(media_map[d["image_id"]]) > 1]

    print(f"\n  Local fix (have page_start): {len(local_fix)}")
    print(f"  Single-image (no page_start needed): {len(single_image)}")
    print(f"  Need API fetch for page_start: {len(multi_image_need_api)}")

    stats = {"patched": 0, "api_fetched": 0, "api_missing": 0, "skipped": 0, "errors": 0}

    # Fix docs that have page_start locally
    print(f"\nPatching {len(local_fix)} docs with local data...")
    for doc in local_fix:
        images = resolve_images(doc, media_map)
        if images and not dry_run:
            if patch_frontmatter(doc["filepath"], images):
                stats["patched"] += 1
            else:
                stats["errors"] += 1
        elif images:
            stats["patched"] += 1

    # Fix single-image docs (page_start doesn't matter)
    print(f"Patching {len(single_image)} single-image docs...")
    for doc in single_image:
        images = media_map[doc["image_id"]]
        if not dry_run:
            if patch_frontmatter(doc["filepath"], images):
                stats["patched"] += 1
            else:
                stats["errors"] += 1
        else:
            stats["patched"] += 1

    # Fetch page_start from API for multi-image docs
    if multi_image_need_api:
        print(f"\nFetching page_start from API for {len(multi_image_need_api)} docs...")
        for i, doc in enumerate(multi_image_need_api):
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(multi_image_need_api)}")

            page_start = fetch_page_start(doc["omeka_id"])
            if page_start is not None:
                doc["page_start"] = page_start
                stats["api_fetched"] += 1
            else:
                # Default to page 1
                doc["page_start"] = 1
                stats["api_missing"] += 1

            images = resolve_images(doc, media_map)
            if images and not dry_run:
                if patch_frontmatter(doc["filepath"], images):
                    stats["patched"] += 1
                else:
                    stats["errors"] += 1
            elif images:
                stats["patched"] += 1

            time.sleep(DELAY)

    print(f"\n{'=' * 50}")
    print(f"Done{'  (DRY RUN)' if dry_run else ''}")
    print(f"  Documents patched:        {stats['patched']}")
    print(f"  API page_start found:     {stats['api_fetched']}")
    print(f"  API page_start missing:   {stats['api_missing']} (defaulted to 1)")
    print(f"  Skipped (not in map):     {len(not_in_map)}")
    print(f"  Errors:                   {stats['errors']}")


if __name__ == "__main__":
    main()
