#!/usr/bin/env python3
"""Fetch all items from the Omeka S API and generate Hugo content files.

Only emits Document content files. Collection and Repository data is
denormalized into each document's front matter as taxonomy fields.

Documents use taxonomy-shaped front matter (authors, recipients, collections,
repositories, doc_types as lists) and place human transcriptions in the
markdown body. Notable persons/locations/items are stored as plain lists
(not taxonomies) for Pagefind indexing.

Two-pass approach:
  Pass 1: Fetch all items, build collection→repository lookup, write documents.
  Pass 2: Update documents with resolved repository names.
"""

import argparse
import os
import re
import sys
import time

import requests
import yaml

API_BASE = "https://www.wardepartmentpapers.org/api"
CONTENT_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
PER_PAGE = 100
DELAY = 0.1  # seconds between API calls

MAX_TAXONOMY_LEN = 150  # Prevent filesystem path-too-long errors from Hugo slugification


def truncate_taxonomy(val):
    """Truncate a taxonomy value to avoid filesystem path-too-long errors."""
    if len(val) <= MAX_TAXONOMY_LEN:
        return val
    truncated = val[:MAX_TAXONOMY_LEN].rsplit(" ", 1)[0]
    return truncated


def get_literal(item, key):
    """Get a single literal value from an item property."""
    vals = item.get(key, [])
    if not vals:
        return None
    return vals[0].get("@value")


def get_all_literals(item, key):
    """Get all literal values from a multi-valued property, stripped of whitespace."""
    vals = item.get(key, [])
    result = []
    for v in vals:
        text = v.get("@value") or v.get("display_title", "")
        text = text.strip()
        if text:
            result.append(text)
    return result


def get_resource_ref(item, key):
    """Get a resource reference (linked item) — returns (display_title, id) or (None, None)."""
    vals = item.get(key, [])
    if not vals:
        return None, None
    v = vals[0]
    if v.get("type") == "resource":
        return v.get("display_title"), v.get("value_resource_id")
    return v.get("@value"), None


def fix_thumbnail_url(url):
    """Convert absolute thumbnail URL to relative path."""
    if not url:
        return None
    url = re.sub(r"https?://(?:www\.)?wardepartmentpapers\.org", "", url)
    return url


def get_resource_type(item):
    """Extract the resource type name from an API item."""
    types = item.get("@type", [])
    for t in types:
        if ":" in t and not t.startswith("o:"):
            return t.split(":")[1]
    return "Unknown"


def extract_document(item, fm, coll_to_repo):
    """Extract Document-specific fields. Returns transcription body text."""
    fm["description"] = get_literal(item, "dcterms:description")

    # doc_types as taxonomy list
    doc_type = get_literal(item, "dcterms:type")
    if doc_type:
        fm["doc_types"] = [truncate_taxonomy(doc_type.strip())]

    fm["year"] = get_literal(item, "pwd:createdYear")
    fm["month"] = get_literal(item, "pwd:createdMonth")
    fm["day"] = get_literal(item, "pwd:createdDay")

    # Authors as taxonomy list
    author, _ = get_resource_ref(item, "dcterms:creator")
    if author:
        fm["authors"] = [truncate_taxonomy(author.strip())]

    # Recipients as taxonomy list
    recipient, _ = get_resource_ref(item, "bibo:recipient")
    if recipient:
        fm["recipients"] = [truncate_taxonomy(recipient.strip())]

    fm["sent_from"] = get_literal(item, "pwd:sentFromLocation")

    # Collections as taxonomy list
    coll_name, coll_id = get_resource_ref(item, "pwd:collection")
    if coll_name:
        fm["collections"] = [truncate_taxonomy(coll_name.strip())]
    if coll_id:
        fm["collection_id"] = coll_id
        # Resolve repository from collection
        repo_name = coll_to_repo.get(coll_id)
        if repo_name:
            fm["repositories"] = [truncate_taxonomy(repo_name.strip())]

    # Image reference (resolved at build time via data/media_map.json)
    _, img_id = get_resource_ref(item, "pwd:image")
    if img_id:
        fm["image_id"] = img_id

    fm["document_number"] = get_literal(item, "pwd:documentNumber")
    fm["page_start"] = get_literal(item, "bibo:pageStart")
    fm["num_pages"] = get_literal(item, "bibo:numPages")
    fm["note"] = get_literal(item, "pwd:note")
    fm["content_note"] = get_literal(item, "pwd:contentNote")
    fm["author_note"] = get_literal(item, "pwd:authorNote")
    fm["recipient_note"] = get_literal(item, "pwd:recipientNote")

    # Notable fields as plain lists (indexed by Pagefind, not Hugo taxonomies)
    notable_persons = [truncate_taxonomy(v) for v in get_all_literals(item, "pwd:notablePersonGroup")]
    if notable_persons:
        fm["notable_persons"] = notable_persons

    notable_locations = [truncate_taxonomy(v) for v in get_all_literals(item, "pwd:notableLocation")]
    if notable_locations:
        fm["notable_locations"] = notable_locations

    notable_items = [truncate_taxonomy(v) for v in get_all_literals(item, "pwd:notableItemThing")]
    if notable_items:
        fm["notable_items"] = notable_items

    # Transcription goes in markdown body, not front matter
    transcription = get_literal(item, "scripto:transcription")

    # Clean None values from front matter
    for key in list(fm.keys()):
        if fm[key] is None:
            del fm[key]

    return transcription or ""


def write_document(fm, body=""):
    """Write a single document as a Hugo content file."""
    item_id = fm["omeka_id"]
    output_dir = os.path.join(CONTENT_BASE, "document")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{item_id}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml.dump(fm, default_flow_style=False, allow_unicode=True, width=200))
        f.write("---\n")
        if body.strip():
            body = body.replace("\r\n", "\n").replace("\r", "\n")
            f.write("\n")
            f.write(body.strip())
            f.write("\n")


def item_is_cached(item_id):
    """Check if a document file already exists."""
    path = os.path.join(CONTENT_BASE, "document", f"{item_id}.md")
    return os.path.exists(path)


def fetch_all_items(use_cache=False):
    """Fetch all items from the API with pagination.

    Two-pass approach:
    - First pass collects collection→repository mappings and documents.
    - Documents are written with resolved repository names inline.
    """
    # Get total count first
    resp = requests.get(f"{API_BASE}/items", params={"per_page": 1})
    resp.raise_for_status()
    total = int(resp.headers.get("Omeka-S-Total-Results", 0))
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    print(f"Total items: {total} ({total_pages} pages of {PER_PAGE})")
    if use_cache:
        print("Cache mode: skipping items that already have content files")

    # Pass 1: Collect collection→repository mappings
    print("Pass 1: Building collection→repository lookup...")
    coll_to_repo = {}
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
                resource_type = get_resource_type(item)
                if resource_type == "Collection":
                    coll_id = item.get("o:id")
                    repo_name, _ = get_resource_ref(item, "pwd:repository")
                    if coll_id and repo_name:
                        coll_to_repo[coll_id] = repo_name

            if page % 50 == 0:
                print(f"  Page {page}/{total_pages} ({len(coll_to_repo)} collection→repo mappings)")

            page += 1
            time.sleep(DELAY)

        except requests.exceptions.RequestException as e:
            print(f"  Network error on page {page}: {e}", file=sys.stderr)
            print("  Retrying in 5 seconds...")
            time.sleep(5)
            continue

    print(f"  Found {len(coll_to_repo)} collection→repository mappings")

    # Pass 2: Fetch documents and write with resolved repositories
    print("Pass 2: Writing document content files...")
    counts = {"written": 0, "skipped": 0, "cached": 0}
    errors = 0
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
                try:
                    resource_type = get_resource_type(item)
                    if resource_type != "Document":
                        counts["skipped"] += 1
                        continue

                    item_id = item.get("o:id")
                    if use_cache and item_is_cached(item_id):
                        counts["cached"] += 1
                        continue

                    # Build front matter
                    fm = {}
                    title = item.get("o:title") or "[Untitled]"
                    fm["title"] = title
                    fm["omeka_id"] = item_id
                    fm["resource_type"] = "Document"

                    # Thumbnails
                    thumbs = item.get("thumbnail_display_urls", {})
                    sq = fix_thumbnail_url(thumbs.get("square"))
                    lg = fix_thumbnail_url(thumbs.get("large"))
                    if sq:
                        fm["thumbnail_square"] = sq
                    if lg:
                        fm["thumbnail_large"] = lg

                    # Created date
                    created = item.get("o:created", {})
                    if isinstance(created, dict):
                        val = created.get("@value", "")
                        if val:
                            fm["created"] = val

                    body = extract_document(item, fm, coll_to_repo)
                    write_document(fm, body)
                    counts["written"] += 1
                except Exception as e:
                    errors += 1
                    item_id = item.get("o:id", "?")
                    print(f"  ERROR on item {item_id}: {e}", file=sys.stderr)

            if page % 10 == 0:
                print(f"  Page {page}/{total_pages} ({counts['written']} written, "
                      f"{counts['cached']} cached, {counts['skipped']} skipped, {errors} errors)")

            page += 1
            time.sleep(DELAY)

        except requests.exceptions.RequestException as e:
            print(f"  Network error on page {page}: {e}", file=sys.stderr)
            print("  Retrying in 5 seconds...")
            time.sleep(5)
            continue

    print(f"\nDone!")
    print(f"  Documents written: {counts['written']}")
    if use_cache:
        print(f"  Cached (already exist): {counts['cached']}")
    print(f"  Skipped (non-Document): {counts['skipped']}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch items from Omeka S API")
    parser.add_argument("--cache", action="store_true",
                        help="Skip items that already have content files")
    args = parser.parse_args()
    fetch_all_items(use_cache=args.cache)
