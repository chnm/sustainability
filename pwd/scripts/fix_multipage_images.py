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

import re

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


def _images_block(frontmatter):
    """Return the raw 'images:' block text (the images: line plus any - items)."""
    m = re.search(r"^images:[^\n]*\n(?:- [^\n]*\n)*", frontmatter, re.M)
    return m.group(0) if m else ""


def parse_document(text):
    """Parse a document file's text into a record dict, or None if no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.index("---", 3)
    fm = text[3:end]

    def field(name):
        m = re.search(rf"^{name}:\s*[\"']?([^\"'\n]+)", fm, re.M)
        return m.group(1).strip() if m else None

    page_start_raw = field("page_start")
    block = _images_block(fm)
    return {
        "omeka_id": field("omeka_id"),
        "image_id": field("omeka_image_id"),
        "page_start": int(page_start_raw) if page_start_raw and page_start_raw.isdigit() else 1,
        "has_num_pages": re.search(r"^num_pages:", fm, re.M) is not None,
        "image_count": len(re.findall(r"^- \S+", block, re.M)),
    }


def build_patched_text(text, new_images):
    """Rewrite the images: block and insert num_pages if absent.

    Returns (new_text, changed).
    """
    if not text.startswith("---"):
        return text, False
    end = text.index("---", 3)
    fm = text[3:end]
    body = text[end + 3:]

    new_block = "images:\n" + "".join(f"- {fn}\n" for fn in new_images)
    new_fm, n = re.subn(
        r"^images:[^\n]*\n(?:- [^\n]*\n)*", new_block, fm, count=1, flags=re.M
    )
    if n == 0:
        new_fm = fm  # no images key; leave untouched (not expected for our docs)

    if not re.search(r"^num_pages:", new_fm, re.M):
        new_fm = re.sub(
            r"^(page_start:[^\n]*)$",
            lambda m: m.group(1) + f"\nnum_pages: '{len(new_images)}'",
            new_fm,
            count=1,
            flags=re.M,
        )

    new_text = "---" + new_fm + "---" + body
    return new_text, new_text != text
