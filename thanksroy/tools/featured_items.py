#!/usr/bin/env python3
"""
Regenerate the FEATURED array in themes/default/javascripts/featured-item.js.

Omeka's homepage picked a random featured item per request; the static archive
reproduces that client-side. The authoritative list of featured items comes from
the live origin:

    https://thanksroy.org/items/browse?featured=1

Prints a ready-to-paste JS array. Only useful while the origin still answers --
once it is gone, the committed array is the record.

    python3 tools/featured_items.py
"""
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://thanksroy.org/items/browse?featured=1'
UA = 'rrchnm-sustainability-archive/1.0 (featured item list)'


def unescape(s):
    for a, b in (('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                 ('&quot;', '"'), ('&#039;', "'"), ('&#8211;', '–'),
                 ('&#8212;', '—'), ('&nbsp;', ' ')):
        s = s.replace(a, b)
    return s.strip()


def main():
    req = urllib.request.Request(URL, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode('utf-8', 'replace')

    if 'page=2' in html or 'next' in html.lower() and 'featured=1&amp;page' in html:
        print('WARNING: the featured browse looks paginated; check by hand.',
              file=sys.stderr)

    ids = []
    for m in re.finditer(r'items/show/(\d+)', html):
        i = int(m.group(1))
        if i not in ids:
            ids.append(i)
    ids.sort()
    if not ids:
        print('no featured items found', file=sys.stderr)
        return 1

    rows = []
    for item_id in ids:
        path = os.path.join(ROOT, 'items', 'show', '%d.html' % item_id)
        if not os.path.exists(path):
            print('WARNING: %d is featured but has no local page' % item_id,
                  file=sys.stderr)
            continue
        page = open(path, encoding='utf-8').read()
        t = re.search(r'<h1>(.*?)</h1>', page, re.S)
        thumb = re.search(r'square_thumbnails/([A-Za-z0-9._-]+)', page)
        rows.append((item_id,
                     unescape(re.sub(r'<[^>]+>', '', t.group(1))) if t else '',
                     thumb.group(1) if thumb else ''))

    width = max(len(r[1]) for r in rows) + 3
    print('    var FEATURED = [')
    for n, (item_id, title, thumb) in enumerate(rows):
        js_title = title.replace('\\', '\\\\').replace("'", "\\'")
        comma = '' if n == len(rows) - 1 else ','
        print("        { id: %d, title: %-*s thumb: '%s' }%s"
              % (item_id, width, "'%s'," % js_title, thumb, comma))
    print('    ];')
    return 0


if __name__ == '__main__':
    sys.exit(main())
