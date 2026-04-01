#!/usr/bin/env python3
"""Fetch media files from the Omeka S API and download missing files."""

import argparse
import json
import os
import sys
import time
import requests

API_BASE = "https://www.wardepartmentpapers.org/api"
FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static-media", "files")
PER_PAGE = 100
DELAY = 0.1  # seconds between API calls
DOWNLOAD_DELAY = 0.1  # seconds between file downloads
SIZES = ["large", "original", "square"]


def fetch_media_page(page):
    """Fetch a single page of media records from the API."""
    resp = requests.get(
        f"{API_BASE}/media",
        params={"per_page": PER_PAGE, "page": page, "sort_by": "id", "sort_order": "asc"},
    )
    resp.raise_for_status()
    return resp.json(), resp.headers


def extract_media_record(media):
    """Extract relevant fields from an API media record."""
    thumbnail_urls = media.get("o:thumbnail_urls", {})
    item = media.get("o:item", {})
    return {
        "id": media.get("o:id"),
        "filename": media.get("o:filename"),
        "source": media.get("o:source"),
        "media_type": media.get("o:media_type"),
        "size": media.get("o:size"),
        "item_id": item.get("o:id") if item else None,
        "urls": {
            "original": media.get("o:original_url"),
            "large": thumbnail_urls.get("large"),
            "square": thumbnail_urls.get("square"),
        },
    }


def scan_existing_files():
    """Scan static/files/ directories and return sets of existing filenames per size."""
    existing = {}
    for size in SIZES:
        size_dir = os.path.join(FILES_DIR, size)
        if os.path.isdir(size_dir):
            existing[size] = set(os.listdir(size_dir))
        else:
            existing[size] = set()
    return existing


def download_file(url, dest_path):
    """Download a file using streaming to handle large files."""
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def fetch_all_media(dry_run=False, catalog_only=False):
    """Fetch all media records from the API and download missing files."""
    # Ensure output directories exist
    for size in SIZES:
        os.makedirs(os.path.join(FILES_DIR, size), exist_ok=True)

    # Get total count
    resp = requests.get(f"{API_BASE}/media", params={"per_page": 1})
    resp.raise_for_status()
    total = int(resp.headers.get("Omeka-S-Total-Results", 0))
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    print(f"Total media records: {total} ({total_pages} pages of {PER_PAGE})")

    # Scan existing files on disk
    existing = scan_existing_files()
    for size in SIZES:
        print(f"  Existing {size}/: {len(existing[size])} files")

    # Catalog phase: paginate API and collect all media records
    print(f"\nFetching media catalog from API...")
    all_media = []
    page = 1

    while True:
        try:
            records, headers = fetch_media_page(page)
            if not records:
                break

            for record in records:
                all_media.append(extract_media_record(record))

            if page % 50 == 0:
                print(f"  Page {page}/{total_pages} ({len(all_media)} records)")

            page += 1
            time.sleep(DELAY)

        except requests.exceptions.RequestException as e:
            print(f"  Network error on page {page}: {e}", file=sys.stderr)
            print("  Retrying in 5 seconds...")
            time.sleep(5)
            continue

    print(f"Cataloged {len(all_media)} media records")

    # Write catalog if requested
    if catalog_only:
        catalog_path = os.path.join(FILES_DIR, "media_catalog.json")
        with open(catalog_path, "w") as f:
            json.dump(all_media, f, indent=2)
        print(f"Catalog written to {catalog_path}")
        return

    # Calculate what's missing
    missing = {size: [] for size in SIZES}
    for record in all_media:
        filename = record["filename"]
        if not filename:
            continue
        for size in SIZES:
            if filename not in existing[size] and record["urls"].get(size):
                missing[size].append(record)

    total_missing = sum(len(missing[s]) for s in SIZES)
    print(f"\nMissing files:")
    for size in SIZES:
        print(f"  {size}/: {len(missing[size])} files to download")
    print(f"  Total: {total_missing} files")

    if dry_run:
        print("\n--dry-run: no files downloaded")
        return

    # Download phase
    print(f"\nDownloading missing files...")
    downloaded = 0
    errors = 0

    for size in SIZES:
        size_dir = os.path.join(FILES_DIR, size)
        for i, record in enumerate(missing[size]):
            url = record["urls"][size]
            filename = record["filename"]
            dest = os.path.join(size_dir, filename)

            try:
                download_file(url, dest)
                downloaded += 1

                if downloaded % 100 == 0:
                    print(f"  Downloaded {downloaded}/{total_missing} "
                          f"({errors} errors)")

                time.sleep(DOWNLOAD_DELAY)

            except requests.exceptions.RequestException as e:
                errors += 1
                print(f"  ERROR downloading {size}/{filename} "
                      f"(media {record['id']}): {e}", file=sys.stderr)
                # Retry once after delay
                time.sleep(5)
                try:
                    download_file(url, dest)
                    downloaded += 1
                except Exception:
                    pass  # already counted the error

            except Exception as e:
                errors += 1
                print(f"  ERROR {size}/{filename}: {e}", file=sys.stderr)

    print(f"\nDone! Downloaded {downloaded} files ({errors} errors)")


def main():
    parser = argparse.ArgumentParser(
        description="Download media files from the Omeka S API"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Catalog media and report what's missing, but don't download",
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Write a JSON catalog of all media records and exit",
    )
    args = parser.parse_args()

    fetch_all_media(dry_run=args.dry_run, catalog_only=args.catalog_only)


if __name__ == "__main__":
    main()
