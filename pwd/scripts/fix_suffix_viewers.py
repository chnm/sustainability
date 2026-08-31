#!/usr/bin/env python3
"""Corpus-wide repair of image lists inflated by unbounded legacy viewers.

The old site's letterbook viewers run from a document's start page to the END
of the microfilm volume (Omeka never stored end boundaries), and
apply_viewer_harvest preferred the longest usable viewer — so those unbounded
suffix lists overwrote good neighbor-sliced lists on shared reels.

Corrected truth per document:
  - usable viewers exclude, on shared reels, any viewer that (a) is a
    contiguous slice of the reel running to the reel's END (a whole-reel
    list is the suffix starting at page 1) AND (b) swallows other
    documents' page_starts at letterbook scale: >= 3 swallowed starts, or
    swallowed >= half the viewer's length. A per-doc viewer that merely
    sits at the end of its reel (78978) or overlaps a couple of separately
    catalogued sub-records at low density (composite 76255) is kept;
  - if a bounded usable viewer remains, take the longest (preserves the
    PR #85 composite-doc corrections);
  - otherwise fall back to the neighbor slice from fix_multipage_images.

Patches only docs whose current images: block differs from that truth, via
minimal-diff regex surgery. Writes the re-transcription inventory (changed
docs that already have an AI transcription) to
_transcription/suffix_fix_retranscribe_ids.txt on a real run.

Usage:
    python3 scripts/fix_suffix_viewers.py --dry-run
    python3 scripts/fix_suffix_viewers.py
"""

import argparse
import collections
import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from apply_viewer_harvest import patch_file
from fix_multipage_images import classify_reel, resolve_images

ROOT = Path(__file__).parent.parent
CONTENT = ROOT / "content" / "document"
HARVEST = ROOT / "_transcription" / "viewer_harvest.jsonl"
IDS_OUT = ROOT / "_transcription" / "suffix_fix_retranscribe_ids.txt"


def scan_corpus():
    """Per-doc reel/page_start/current images; per-reel doc counts and starts."""
    reel_of, start_of, cur = {}, {}, {}
    reel_docs = collections.Counter()
    reel_starts = collections.defaultdict(list)
    for f in CONTENT.glob("*.md"):
        t = f.read_text(errors="ignore")
        m = re.search(r"^omeka_image_id: '?(\d+)'?$", t, re.M)
        if not m:
            continue
        oid = f.stem
        reel_of[oid] = m.group(1)
        reel_docs[m.group(1)] += 1
        ps = re.search(r"^page_start: '?(\d+)'?$", t, re.M)
        start_of[oid] = int(ps.group(1)) if ps else 1
        reel_starts[m.group(1)].append(start_of[oid])
        cur[oid] = re.findall(r"^- ([0-9a-f]{40}\.jpg)", t, re.M)
    return reel_of, start_of, cur, reel_docs, reel_starts


def compute_truth():
    """Returns {omeka_id: [files]} for docs whose corrected truth differs."""
    mm = json.loads((ROOT / "data" / "media_map.json").read_text())
    reel_of, start_of, cur, reel_docs, reel_starts = scan_corpus()

    # page_starts of OTHER docs per reel, for the swallow test
    starts_on_reel = {rid: sorted(s) for rid, s in reel_starts.items()}

    def is_unbounded(oid, v, reel_id, reel):
        """Suffix-of-reel viewer that swallows another doc's page_start."""
        if reel_docs[reel_id] <= 1 or len(v) > len(reel):
            return False
        if v != reel[len(reel) - len(v):]:
            return False  # not a contiguous run-to-reel-end slice
        s = len(reel) - len(v) + 1  # 1-based start position of the viewer
        own = start_of[oid]
        swallowed = sum(1 for p in starts_on_reel[reel_id]
                        if s < p <= len(reel) and p != own)
        # A composite doc legitimately overlaps 1-2 sub-records at low density
        # (e.g. 76255: 5 pages, 1 swallowed start). Letterbook tails swallow
        # many starts, or a large share of their length.
        return swallowed >= 3 or swallowed * 2 >= len(v)

    bounded_viewer = {}
    for line in HARVEST.read_text().splitlines():
        r = json.loads(line)
        oid = r["omeka_id"]
        if oid not in reel_of:
            continue
        reel = mm.get(reel_of[oid], [])
        usable = [
            v for v in r["viewers"].values()
            if v and set(v) <= set(reel)
            and not is_unbounded(oid, v, reel_of[oid], reel)
        ]
        if usable:
            bounded_viewer[oid] = max(usable, key=len)

    truth = {}
    for oid, reel_id in reel_of.items():
        reel = mm.get(reel_id, [])
        if not reel:
            continue
        best = bounded_viewer.get(oid)
        if best is None:
            bucket = classify_reel(reel_docs[reel_id], len(reel))
            best = resolve_images(bucket, start_of[oid], reel_starts[reel_id], reel)
        if best and best != cur[oid]:
            truth[oid] = best
    return truth, cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    truth, cur = compute_truth()
    shrunk = sum(1 for o, v in truth.items() if len(v) < len(cur[o]))
    grown = sum(1 for o, v in truth.items() if len(v) > len(cur[o]))
    print(f"{len(truth)} docs differ from corrected truth "
          f"({shrunk} shrink, {grown} grow, {len(truth) - shrunk - grown} same length)")

    patched, failed = [], []
    for oid, files in sorted(truth.items()):
        new, err = patch_file(CONTENT / f"{oid}.md", files)
        if err:
            failed.append((oid, err))
            continue
        if not args.dry_run:
            (CONTENT / f"{oid}.md").write_text(new)
        patched.append(oid)
    print(f"{'would patch' if args.dry_run else 'patched'}: {len(patched)}, failed: {len(failed)}")
    for oid, err in failed[:20]:
        print(f"  FAIL {oid}: {err}")

    if not args.dry_run and patched:
        transcribed = set(json.loads(
            (ROOT / "_transcription" / "transcriptions.json").read_text()))
        redo = [o for o in patched if o in transcribed]
        IDS_OUT.write_text("\n".join(redo) + "\n")
        print(f"re-transcription inventory -> {IDS_OUT} ({len(redo)} ids)")


if __name__ == "__main__":
    main()
