#!/usr/bin/env python3
"""
Rebuild images: lists (and derive num_pages) for documents missing num_pages.

Groups documents by their reel (omeka_image_id), classifies each reel by size,
and resolves each document's image slice locally from data/media_map.json and
page_start. No network access.

Usage:
    uv run python3 scripts/fix_multipage_images.py --dry-run
    uv run python3 scripts/fix_multipage_images.py
"""

SMALL_REEL_THRESHOLD = 5


def classify_reel(num_docs, reel_size, threshold=SMALL_REEL_THRESHOLD):
    """Return 'single', 'small', or 'large' for a reel.

    - single: reel referenced by exactly one document -> whole reel
    - small:  multiple docs, reel_size <= threshold   -> whole reel
    - large:  multiple docs, reel_size >  threshold   -> slice by page_start
    """
    if num_docs <= 1:
        return "single"
    if reel_size <= threshold:
        return "small"
    return "large"


def resolve_images(bucket, page_start, all_page_starts, reel_files):
    """Return the list of image filenames for one document."""
    n = len(reel_files)
    if n == 0:
        return []
    if bucket in ("single", "small"):
        return list(reel_files)
    # large: slice from page_start to the next distinct page_start on the reel
    distinct = sorted(set(all_page_starts))
    if page_start in distinct:
        i = distinct.index(page_start)
        nxt = distinct[i + 1] if i + 1 < len(distinct) else n + 1
    else:
        nxt = n + 1
    start = min(max(page_start - 1, 0), n - 1)
    end = min(nxt - 1, n)
    if end <= start:
        end = start + 1
    return list(reel_files[start:end])
