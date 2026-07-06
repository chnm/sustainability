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
