#!/usr/bin/env python3
"""Patch document frontmatter with ground-truth image lists from the viewer harvest.

Recomputes per-doc truth from _transcription/viewer_harvest.jsonl (largest
usable on-reel viewer list, ignoring whole-reel viewers on shared reels),
then rewrites each mismatched doc's `images:` block and `num_pages:` with
minimal-diff regex surgery. Idempotent. Writes the re-transcription queue to
_transcription/harvest_retranscribe_ids.txt (only on a real run, not --dry-run).

Usage:
    python3 scripts/apply_viewer_harvest.py --dry-run [--ids 76255 ...]
    python3 scripts/apply_viewer_harvest.py
"""

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONTENT = ROOT / "content" / "document"
HARVEST = ROOT / "_transcription" / "viewer_harvest.jsonl"
IDS_OUT = ROOT / "_transcription" / "harvest_retranscribe_ids.txt"

IMAGES_BLOCK_RE = re.compile(r"^images:\n(?:- [0-9a-f]{40}\.jpg\n)+", re.M)
NUM_PAGES_RE = re.compile(r"^num_pages: '?\d+'?$", re.M)


def compute_truth():
    """Returns {omeka_id: [files]} for docs whose harvest truth differs from frontmatter."""
    mm = json.loads((ROOT / "data" / "media_map.json").read_text())
    reel_of, cur = {}, {}
    reel_docs = collections.Counter()
    for f in CONTENT.glob("*.md"):
        t = f.read_text(errors="ignore")
        m = re.search(r"^omeka_image_id: '?(\d+)'?$", t, re.M)
        if not m:
            continue
        oid = f.stem
        reel_of[oid] = m.group(1)
        reel_docs[m.group(1)] += 1
        cur[oid] = re.findall(r"^- ([0-9a-f]{40}\.jpg)", t, re.M)

    truth = {}
    for line in HARVEST.read_text().splitlines():
        r = json.loads(line)
        oid = r["omeka_id"]
        if oid not in reel_of:
            continue
        reel = mm.get(reel_of[oid], [])
        shared = reel_docs[reel_of[oid]] > 1
        usable = [
            v for v in r["viewers"].values()
            if v and set(v) <= set(reel) and not (shared and len(v) == len(reel))
        ]
        if not usable:
            continue
        best = max(usable, key=len)
        if best != cur[oid]:
            truth[oid] = best
    return truth


def patch_file(path, files):
    t = path.read_text()
    new_block = "images:\n" + "".join(f"- {f}\n" for f in files)
    t2, n_img = IMAGES_BLOCK_RE.subn(new_block, t, count=1)
    if n_img != 1:
        t2, n_img = re.subn(r"^images: \[\]\n", new_block, t, count=1, flags=re.M)
    if n_img != 1:
        return None, "no images block"
    t2, n_np = NUM_PAGES_RE.subn(f"num_pages: '{len(files)}'", t2, count=1)
    if n_np != 1:
        return None, "no num_pages line"
    return t2, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ids", nargs="*")
    args = ap.parse_args()

    truth = compute_truth()
    if args.ids:
        truth = {k: v for k, v in truth.items() if k in set(args.ids)}
    patched, failed = [], []
    for oid, files in sorted(truth.items()):
        path = CONTENT / f"{oid}.md"
        new, err = patch_file(path, files)
        if err:
            failed.append((oid, err))
            continue
        if not args.dry_run:
            path.write_text(new)
        patched.append(oid)
    print(f"{'would patch' if args.dry_run else 'patched'}: {len(patched)}, failed: {len(failed)}")
    for oid, err in failed[:20]:
        print(f"  FAIL {oid}: {err}")
    if not args.dry_run and patched:
        IDS_OUT.write_text("\n".join(patched) + "\n")
        print(f"re-transcription queue -> {IDS_OUT} ({len(patched)} ids)")


if __name__ == "__main__":
    main()
