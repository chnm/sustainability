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
import os
import json
import argparse
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_ROOT / "content" / "document"
MEDIA_MAP_PATH = PROJECT_ROOT / "data" / "media_map.json"
MANIFEST_PATH = PROJECT_ROOT / "multipage_fix_manifest.json"
GROWN_IDS_PATH = PROJECT_ROOT / "multipage_grown_ids.txt"

SMALL_REEL_THRESHOLD = 5


def classify_reel(num_docs: int, reel_size: int, threshold: int = SMALL_REEL_THRESHOLD) -> str:
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


def resolve_images(bucket: str, page_start: int, all_page_starts: list, reel_files: list) -> list:
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

    if new_images:
        new_block = "images:\n" + "".join(f"- {fn}\n" for fn in new_images)
    else:
        new_block = "images: []\n"
    new_fm, n = re.subn(
        r"^images:[^\n]*\n(?:- [^\n]*\n)*", new_block, fm, count=1, flags=re.M
    )
    if n == 0:
        new_fm = fm  # no images key; leave untouched (not expected for our docs)

    # Insert-only: we only ever add num_pages when it is absent. This tool only
    # processes documents that lack num_pages, so we never need to correct an
    # existing value here.
    if not re.search(r"^num_pages:", new_fm, re.M):
        num_pages_line = f"num_pages: '{len(new_images)}'"
        new_fm, inserted = re.subn(
            r"^(page_start:[^\n]*)$",
            lambda m: m.group(1) + f"\n{num_pages_line}",
            new_fm,
            count=1,
            flags=re.M,
        )
        if not inserted:
            # No page_start line to anchor to; insert right after the
            # rewritten images: block instead.
            new_fm, inserted = re.subn(
                re.escape(new_block),
                new_block + num_pages_line + "\n",
                new_fm,
                count=1,
            )

    new_text = "---" + new_fm + "---" + body
    return new_text, new_text != text


def plan_changes(records, media_map, threshold):
    """Compute the set of changes without touching disk.

    records: {omeka_id: {"record": <parse dict>, "text": <str>}}
    Returns (changes, grown_ids, stats).
    """
    # Group page_starts by reel across ALL documents (including already-fixed
    # ones), so slice boundaries and doc counts are correct.
    reel_starts = {}
    for info in records.values():
        rec = info["record"]
        if rec and rec["image_id"]:
            reel_starts.setdefault(rec["image_id"], []).append(rec["page_start"])

    changes = []
    grown = []
    stats = Counter()
    for omeka_id, info in records.items():
        rec = info["record"]
        if not rec or not rec["image_id"]:
            continue
        if rec["has_num_pages"]:
            stats["skip_has_num_pages"] += 1
            continue
        reel = media_map.get(rec["image_id"])
        if not reel:
            stats["skip_no_media"] += 1
            continue
        starts = reel_starts[rec["image_id"]]
        bucket = classify_reel(len(starts), len(reel), threshold)
        images = resolve_images(bucket, rec["page_start"], starts, reel)
        new_text, _ = build_patched_text(info["text"], images)
        old_count, new_count = rec["image_count"], len(images)
        stats[bucket] += 1
        changes.append({
            "omeka_id": omeka_id,
            "bucket": bucket,
            "old_count": old_count,
            "new_count": new_count,
            "new_text": new_text,
        })
        if new_count > old_count:
            grown.append(omeka_id)
    return changes, grown, stats


def collect_records(content_dir):
    """Read every document .md into {omeka_id: {'record':..., 'text':..., 'path':...}}."""
    records = {}
    for fname in os.listdir(content_dir):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        path = os.path.join(content_dir, fname)
        with open(path) as f:
            text = f.read()
        rec = parse_document(text)
        if not rec or not rec["omeka_id"]:
            continue
        records[rec["omeka_id"]] = {"record": rec, "text": text, "path": path}
    return records


def main():
    ap = argparse.ArgumentParser(description="Fix multi-page document images")
    ap.add_argument("--dry-run", action="store_true", help="Plan only; write no .md files")
    ap.add_argument("--small-reel-threshold", type=int, default=SMALL_REEL_THRESHOLD,
                    help=f"Reels with <= N images get the whole reel (default {SMALL_REEL_THRESHOLD})")
    args = ap.parse_args()

    with open(MEDIA_MAP_PATH) as f:
        media_map = json.load(f)

    print(f"Scanning {CONTENT_DIR}...")
    records = collect_records(CONTENT_DIR)
    print(f"Documents scanned: {len(records)}")

    changes, grown, stats = plan_changes(records, media_map, args.small_reel_threshold)

    would_patch = sum(
        1 for c in changes if c["new_text"] != records[c["omeka_id"]]["text"]
    )
    patched = 0
    for change in changes:
        info = records[change["omeka_id"]]
        if change["new_text"] != info["text"] and not args.dry_run:
            with open(info["path"], "w") as f:
                f.write(change["new_text"])
            patched += 1

    manifest = [{k: c[k] for k in ("omeka_id", "bucket", "old_count", "new_count")}
                for c in changes]
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(GROWN_IDS_PATH, "w") as f:
        f.write("\n".join(sorted(grown, key=int)) + ("\n" if grown else ""))

    print(f"\n{'=' * 50}")
    print(f"Done{'  (DRY RUN — no files written)' if args.dry_run else ''}")
    print(f"  single (whole reel):   {stats.get('single', 0)}")
    print(f"  small  (whole reel):   {stats.get('small', 0)}")
    print(f"  large  (sliced):       {stats.get('large', 0)}")
    print(f"  skipped (has num_pages): {stats.get('skip_has_num_pages', 0)}")
    print(f"  skipped (no media):      {stats.get('skip_no_media', 0)}")
    print(f"  documents that grew:   {len(grown)}")
    print(f"  files {'to patch (dry run)' if args.dry_run else 'patched'}: "
          f"{would_patch if args.dry_run else patched}")
    print(f"  manifest:   {MANIFEST_PATH}")
    print(f"  grown ids:  {GROWN_IDS_PATH}")


if __name__ == "__main__":
    main()
