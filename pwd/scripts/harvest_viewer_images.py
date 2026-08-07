#!/usr/bin/env python3
"""Harvest ground-truth document image lists from the legacy PWD viewers.

For every document with an omeka_image_id, fetch its old-site item page,
follow the pwd/viewer/<legacy_id> link(s), and record each viewer's exact
image file list. Output is JSONL (one doc per line), resumable: already-
harvested omeka_ids are skipped on restart.

Usage:
    python3 scripts/harvest_viewer_images.py            # full harvest
    python3 scripts/harvest_viewer_images.py --ids 76255 78978   # smoke test
"""

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

import requests

BASE = "https://omeka.wardepartmentpapers.org"
CONTENT_DIR = Path(__file__).parent.parent / "content" / "document"
OUT_FILE = Path(__file__).parent.parent / "_transcription" / "viewer_harvest.jsonl"
DELAY = 0.1
RETRY_WAIT = 5

VIEWER_RE = re.compile(r"pwd/viewer/(\d+)")
IMAGE_RE = re.compile(r"files/large/([0-9a-f]{40}\.jpg)")


def fetch(session, url):
    while True:
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            return html.unescape(r.text)
        except requests.RequestException as e:
            print(f"    retry ({e})", flush=True)
            time.sleep(RETRY_WAIT)


def harvest_doc(session, omeka_id):
    item_html = fetch(session, f"{BASE}/s/home/item/{omeka_id}")
    viewer_ids = sorted(set(VIEWER_RE.findall(item_html)))
    viewers = {}
    for vid in viewer_ids:
        time.sleep(DELAY)
        vhtml = fetch(session, f"{BASE}/s/home/pwd/viewer/{vid}")
        # dict.fromkeys: dedupe (thumbnail + main img) but keep page order
        viewers[vid] = list(dict.fromkeys(IMAGE_RE.findall(vhtml)))
    return {"omeka_id": omeka_id, "viewers": viewers}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*", help="only harvest these omeka_ids")
    args = ap.parse_args()

    if args.ids:
        ids = args.ids
    else:
        ids = []
        for f in sorted(CONTENT_DIR.glob("*.md")):
            if re.search(r"^omeka_image_id:", f.read_text(errors="ignore"), re.M):
                ids.append(f.stem)

    done = set()
    if OUT_FILE.exists():
        for line in OUT_FILE.read_text().splitlines():
            try:
                done.add(json.loads(line)["omeka_id"])
            except (json.JSONDecodeError, KeyError):
                pass
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} docs, {len(done)} already harvested, {len(todo)} to go", flush=True)

    session = requests.Session()
    with open(OUT_FILE, "a") as out:
        for n, oid in enumerate(todo, 1):
            rec = harvest_doc(session, oid)
            out.write(json.dumps(rec) + "\n")
            out.flush()
            nimg = {v: len(fs) for v, fs in rec["viewers"].items()}
            print(f"[{n}/{len(todo)}] doc {oid}: viewers {nimg}", flush=True)
            time.sleep(DELAY)


if __name__ == "__main__":
    main()
