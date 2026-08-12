#!/usr/bin/env python3
"""Harvest from the still-live 20.rrchnm.org origin the things the crawl left out.

The wget mirror excluded the Omeka media derivatives and never followed the
AJAX/JSON endpoints, so three sets of data exist only on the origin. It is still
up; it will not be forever. This script pulls all three, and is idempotent --
anything already on disk is skipped unless --force is given.

  1. geolocation/map.kml
     The browse map fetches this over AJAX. The origin paginates it (page 1 =
     50 placemarks, page 2 = 5), so the two are merged into one file carrying
     all 55, and the URLs inside it are pointed at this archive's conventions:
     /files/... root-relative for the bucket, /items/show/<id>.html for links.
     Committed -- it is 35 KB and map.js sends its params as a query string, so
     a static file at that path serves correctly.

  2. data/neatline-timeline-1.json
     The "Projects" timeline's data (58 events). Its renderer (simile-widgets)
     is dead and http-only, so retrofit.py renders this statically instead.
     Committed -- 27 KB.

  3. The 1,406 media objects under files/{original,square_thumbnails,fullsize,
     thumbnails}/, staged OUTSIDE the repo for loading into the object bucket.
     .gitignore excludes all four directories, so they cannot be committed by
     accident. ~700 MB.

    python3 tools/harvest.py [--force] [--media-dir DIR] [--skip-media]
"""
import argparse
import hashlib
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = "https://20.rrchnm.org"
UA = "rrchnm-sustainability-harvest/1.0 (+https://rrchnm.org)"

KML_OUT = ROOT / "geolocation" / "map.kml"
TIMELINE_OUT = ROOT / "data" / "neatline-timeline-1.json"

# The four Omeka derivative dirs the crawl excluded (see .gitignore).
MEDIA_RE = re.compile(
    r"https://20\.rrchnm\.org"
    r"(/files/(?:original|square_thumbnails|fullsize|thumbnails)/[A-Za-z0-9._%-]+)")


def fetch(url, tries=3):
    """GET a URL, returning bytes. Retries on transient failures."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, OSError) as exc:  # noqa: PERF203
            last = exc
    raise RuntimeError(f"{url}: {last}")


# ---------------------------------------------------------------------------
# 1. map.kml
# ---------------------------------------------------------------------------

# The KML is merged as text, not parsed and re-serialised. map.js reads it with
# jQuery's `xml.find('Placemark')`, which is sensitive to how namespaces are
# emitted; keeping page 1 byte-for-byte and splicing page 2's placemarks in
# guarantees the shape map.js already knows how to read.
PLACEMARKS_RE = re.compile(r"<Placemark>.*</Placemark>", re.DOTALL)


def harvest_kml(force=False):
    if KML_OUT.exists() and not force:
        print(f"[kml]      {KML_OUT.relative_to(ROOT)} exists, skipping")
        return
    params = ("?controller=map&action=browse&module=geolocation"
              "&geolocation-mapped=true&page=")
    pages = [fetch(f"{ORIGIN}/geolocation/map.kml{params}{n}").decode("utf-8")
             for n in (1, 2)]

    extra = []
    for page in pages[1:]:
        m = PLACEMARKS_RE.search(page)
        if m:
            extra.append(m.group(0))

    merged = pages[0]
    if extra:
        # Splice after the last placemark of page 1, preserving its indentation.
        m = PLACEMARKS_RE.search(merged)
        if not m:
            sys.exit("error: page 1 of map.kml has no <Placemark>")
        merged = merged[:m.end()] + "\n        " + \
            "\n        ".join(extra) + merged[m.end():]

    merged = rewrite_kml_urls(merged)
    n = merged.count("<Placemark>")
    KML_OUT.parent.mkdir(parents=True, exist_ok=True)
    KML_OUT.write_text(merged, encoding="utf-8")
    print(f"[kml]      {KML_OUT.relative_to(ROOT)}: {n} placemarks, "
          f"{len(merged)} bytes")


def rewrite_kml_urls(text):
    """Point the KML's own URLs at this archive rather than the origin.

    The thumbnails and item links live inside entity-escaped HTML in
    <description>/<namewithlink>, but the URLs themselves are not escaped, so
    plain substitution reaches them.
    """
    # Media -> root-relative, so the bucket redirect serves it.
    text = text.replace("https://20.rrchnm.org/files/", "/files/")
    # Item links -> the archive's .html filenames. Guarded so a re-run is a
    # no-op and so /items/show/2.html is never turned into /items/show/2.html.html.
    text = re.sub(r'(/items/show/\d+)(?!\.html)(?=["&<\s])', r"\1.html", text)
    return text


# ---------------------------------------------------------------------------
# 2. Neatline timeline JSON
# ---------------------------------------------------------------------------

def harvest_timeline(force=False):
    if TIMELINE_OUT.exists() and not force:
        print(f"[timeline] {TIMELINE_OUT.relative_to(ROOT)} exists, skipping")
        return
    raw = fetch(f"{ORIGIN}/neatline-time/timelines/items/1"
                "?output=neatlinetime-json").decode("utf-8")
    # Same two rewrites as the KML: the events carry origin-absolute thumbnail
    # URLs and extensionless item links.
    raw = raw.replace("https:\\/\\/20.rrchnm.org\\/files\\/", "\\/files\\/")
    raw = raw.replace("https://20.rrchnm.org/files/", "/files/")
    raw = re.sub(r'(\\/items\\/show\\/\d+)(?!\.html)(?=")', r"\1.html", raw)
    raw = re.sub(r'(/items/show/\d+)(?!\.html)(?=")', r"\1.html", raw)
    TIMELINE_OUT.parent.mkdir(parents=True, exist_ok=True)
    TIMELINE_OUT.write_text(raw, encoding="utf-8")
    print(f"[timeline] {TIMELINE_OUT.relative_to(ROOT)}: "
          f"{raw.count('\"start\"')} events, {len(raw)} bytes")


# ---------------------------------------------------------------------------
# 3. Media objects -> staging tree outside the repo
# ---------------------------------------------------------------------------

def media_urls():
    """Every distinct origin media URL referenced by the archive's HTML."""
    found = set()
    for p in sorted(ROOT.rglob("*.html")):
        if "pagefind" in p.parts or "tools" in p.parts:
            continue
        for m in MEDIA_RE.finditer(p.read_text(encoding="utf-8",
                                               errors="replace")):
            found.add(m.group(1))
    return sorted(found)


def harvest_media(media_dir, force=False):
    urls = media_urls()
    print(f"[media]    {len(urls)} distinct objects -> {media_dir}")
    media_dir.mkdir(parents=True, exist_ok=True)
    manifest = media_dir / "manifest.tsv"
    rows, failures = [], []

    def one(path):
        dest = media_dir / path.lstrip("/")
        if dest.exists() and not force:
            body = dest.read_bytes()
        else:
            try:
                body = fetch(ORIGIN + path)
            except RuntimeError as exc:
                failures.append((path, str(exc)))
                return None
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
        return (path, str(dest.relative_to(media_dir)), len(body),
                hashlib.sha256(body).hexdigest())

    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, row in enumerate(pool.map(one, urls), 1):
            if row:
                rows.append(row)
            if i % 100 == 0:
                print(f"[media]    {i}/{len(urls)}")

    with manifest.open("w", encoding="utf-8") as fh:
        fh.write("url\tpath\tbytes\tsha256\n")
        for url, path, size, digest in rows:
            fh.write(f"{ORIGIN}{url}\t{path}\t{size}\t{digest}\n")

    total = sum(r[2] for r in rows)
    print(f"[media]    {len(rows)}/{len(urls)} objects, "
          f"{total / 1048576:.1f} MB, manifest at {manifest}")
    if failures:
        print(f"[media]    {len(failures)} FAILED:")
        for path, err in failures[:20]:
            print(f"             {path}  {err}")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="re-fetch even if the file already exists")
    ap.add_argument("--skip-media", action="store_true",
                    help="only harvest the two small committed files")
    ap.add_argument("--media-dir", default=os.environ.get(
        "HARVEST_MEDIA_DIR", "/tmp/20.rrchnm.org-media"),
        help="staging directory for the media objects (outside the repo)")
    args = ap.parse_args()

    harvest_kml(args.force)
    harvest_timeline(args.force)
    if not args.skip_media:
        media_dir = Path(args.media_dir).resolve()
        if ROOT in media_dir.parents or media_dir == ROOT:
            sys.exit(f"error: --media-dir {media_dir} is inside the repo; "
                     "the media must be staged outside it")
        harvest_media(media_dir, args.force)


if __name__ == "__main__":
    main()
