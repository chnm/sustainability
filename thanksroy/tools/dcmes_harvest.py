#!/usr/bin/env python3
"""
Harvest the Dublin Core (dcmes-xml) sidecars the archive still links to.

Every item page offered four "Output Formats" links, and every browse listing
five, all pointing at the live Omeka backend. tools/retrofit.py drops all of
them except dcmes-xml, so the files those surviving links point at have to
exist in the archive. This fetches them while https://thanksroy.org still
answers.

    items/show/<id>.html            ->  items/show/<id>.dcmes.xml   (162, per item)
    items/browse?tags=roy.html      ->  items/browse?tags=roy.dcmes.xml
    items?page=3.html               ->  items?page=3.dcmes.xml      (190, per listing)

Item sidecars are named `<id>.dcmes.xml`, matching the 658 already committed
under mallhistory/. Listing sidecars keep the wget '?'-in-filename convention
the rest of the archive uses, and their source URL is read straight out of each
page's existing dcmes-xml link rather than reconstructed.

The listing exports are 10-record slices that duplicate the per-item sidecars;
they are harvested anyway so that no surviving link is dead.

Idempotent: files that already exist and parse as XML are skipped, so a partial
run can simply be repeated.

    python3 tools/dcmes_harvest.py [--force] [--jobs N]
"""
import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOW_DIR = os.path.join(ROOT, 'items', 'show')
ORIGIN = 'https://thanksroy.org'
UA = 'rrchnm-sustainability-archive/1.0 (dcmes sidecar harvest)'
RETRIES = 3


def item_ids():
    ids = []
    for name in os.listdir(SHOW_DIR):
        m = re.fullmatch(r'(\d+)\.html', name)
        if m:
            ids.append(int(m.group(1)))
    return sorted(ids)


DCMES_HREF = re.compile(r'href="(https?://thanksroy\.org/[^"]*output=dcmes-xml)"')


def listing_targets():
    """(source URL, destination path) for every browse/listing page.

    The URL comes from the page's own dcmes-xml link -- whatever Omeka
    generated for that exact listing slice -- so nothing has to be
    reconstructed from the filename.
    """
    targets = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ('.git', '.crawl', 'tools')]
        for name in sorted(filenames):
            if not name.endswith('.html'):
                continue
            path = os.path.join(dirpath, name)
            head = open(path, encoding='utf-8', errors='replace').read()
            m = DCMES_HREF.search(head)
            if not m:
                continue
            url = m.group(1).replace('&amp;', '&')
            targets.append((url, path[:-len('.html')] + '.dcmes.xml'))
    return targets


def is_good(path):
    """True if path already holds a well-formed, non-empty DCMES document."""
    try:
        if os.path.getsize(path) < 100:
            return False
        ET.parse(path)
        return True
    except (OSError, ET.ParseError):
        return False


def fetch(url):
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status != 200:
                    raise urllib.error.HTTPError(url, r.status, 'bad status', r.headers, None)
                return r.read()
        except Exception as e:  # noqa: BLE001 - retry anything transient
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError('%s: %s' % (url, last))


def harvest(job, force):
    url, out = job
    label = os.path.relpath(out, ROOT)
    if not force and is_good(out):
        return label, 'skip', None
    try:
        body = fetch(url)
    except RuntimeError as e:
        return label, 'fail', str(e)
    try:
        ET.fromstring(body)
    except ET.ParseError as e:
        return label, 'fail', 'not well-formed XML: %s' % e
    with open(out, 'wb') as f:
        f.write(body)
    return label, 'ok', None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true',
                    help='re-fetch even if a good sidecar already exists')
    ap.add_argument('--jobs', type=int, default=4,
                    help='parallel fetches (default 4; be polite to the origin)')
    args = ap.parse_args()

    jobs = [('%s/items/show/%d?output=dcmes-xml' % (ORIGIN, i),
             os.path.join(SHOW_DIR, '%d.dcmes.xml' % i))
            for i in item_ids()]
    n_items = len(jobs)
    jobs += listing_targets()
    print('%d item sidecars + %d listing sidecars' % (n_items, len(jobs) - n_items))

    counts = {'ok': 0, 'skip': 0, 'fail': 0}
    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for label, status, err in pool.map(lambda j: harvest(j, args.force), jobs):
            counts[status] += 1
            if status == 'fail':
                failures.append((label, err))

    print('fetched %(ok)d, skipped %(skip)d, failed %(fail)d' % counts)
    for label, err in failures:
        print('  FAIL %s: %s' % (label, err), file=sys.stderr)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
