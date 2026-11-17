#!/usr/bin/env python3
"""Import the American Women's Dime Novel Project from its MARS copy (chnm/sustainability#155).

MARS record: http://hdl.handle.net/1920/11710 (gmu.tind.io record 75574), file chnm.gmu.edu.zip, a 2020 wget mirror
of chnm.gmu.edu/dimenovels (WordPress 4.9, Elegant Themes "Flexible"). The mirror already uses relative links; this
script turns it into a tree that works served from a root:

- Drops crawler debris: RSS feeds, wp-json (oEmbed), xmlrpc.php?rsd, wlwmanifest.xml, and the ?p=N shortlink copies
  (every one duplicates a permalink page; links to them are pointed at that page).
- Replaces the cover thumbnails, which the crawl saved as 404 pages (et_temp/*.jpg.html), with the images from the
  live site.
- Renames versioned assets (jquery.js?ver=1.12.4 -> jquery.js) and points absolute chnm.gmu.edu/dimenovels links at
  the local copy.
- Removes the <head> links that pointed at the dropped WordPress endpoints, and the IE 6-8 conditional comments.

Usage: dimenovels_import.py <extracted>/chnm.gmu.edu/dimenovels <repo>/dimenovels   (DEST must not exist)
"""
import os, re, shutil, sys, urllib.request
from pathlib import Path

LIVE = 'https://chnm.gmu.edu/dimenovels/'
QP = re.compile(r'^index\.html\?p=(\d+)\.html$')
VER = re.compile(r'^(.+?\.(?:js|css))\?ver=[^/]*$')          # file names on disk
VER_REF = re.compile(r'(\.(?:js|css))%3Fver=[0-9]+(?:\.[0-9]+)*(?:\.css)?')  # the same names in links


def debris(rel):
    parts = rel.split('/')
    return (parts[0] in ('wp-json', '__MACOSX') or 'feed' in parts or rel in ('wp/xmlrpc.php?rsd', 'wp/wp-includes/wlwmanifest.xml')
            or (parts[-1].endswith('.jpg.html') and 'et_temp' in parts) or QP.match(rel))


def main(src, dest):
    src, dest = Path(src).resolve(), Path(dest).resolve()
    assert not dest.exists(), dest
    files = sorted(p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file())

    # ?p=N -> permalink page, from the permalink pages' canonical links
    perma = {}
    for rel in files:
        if rel.endswith('.html') and not debris(rel):
            m = re.search(r'<link rel="canonical" href="(?:\.\./)*index\.html%3Fp=(\d+)\.html"', (src / rel).read_text('utf-8'))
            if m and (m.group(1) not in perma or perma[m.group(1)].startswith('wp/')):
                perma[m.group(1)] = rel
    for rel in files:   # two shortlink pages are the canonical target themselves and name their permalink instead
        m = QP.match(rel)
        c = m and m.group(1) not in perma and re.search(r'<link rel="canonical" href="([^"%]+\.html)"', (src / rel).read_text('utf-8'))
        if c:
            perma[m.group(1)] = c.group(1)
    orphans = [r for r in files if QP.match(r) and QP.match(r).group(1) not in perma]
    assert not orphans, orphans

    dropped = [r for r in files if debris(r)]
    for rel in files:
        if rel in dropped:
            continue
        m = VER.match(rel)
        out = dest / (m.group(1) if m else rel)
        assert not out.exists(), out
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, out)

    covers = sorted({r[:-5] for r in dropped if r.endswith('.jpg.html')})
    for rel in covers:
        with urllib.request.urlopen(LIVE + rel) as r:
            assert r.headers['Content-Type'] == 'image/jpeg', rel
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            (dest / rel).write_bytes(r.read())

    for p in dest.rglob('*.html'):
        rel = p.relative_to(dest).as_posix()
        up = '../' * rel.count('/')
        s = p.read_bytes().decode('utf-8')
        s = re.sub(r'(?:\.\./)*index\.html%3Fp=(\d+)\.html', lambda m: os.path.relpath(perma[m.group(1)], os.path.dirname(rel) or '.'), s)
        s = re.sub(r'(et_temp/[^"\'/]+\.jpg)\.html', r'\1', s)
        s = VER_REF.sub(r'\1', s)
        s = re.sub(r'<link rel=["\'](?:alternate|https://api\.w\.org/|EditURI|wlwmanifest|pingback)["\'][^>]*>\s*', '', s)
        s = re.sub(r'\s*<!--\[if [^\]]*IE[^\]]*\]>.*?<!\[endif\]-->', '', s, flags=re.S)   # IE 6-8 stylesheets and html5.js, never crawled
        s = re.sub(r'(["\'])https?://chnm\.gmu\.edu/dimenovels/?([^"\'#]*)', lambda m: m.group(1) + local(dest, rel, up, m.group(2)), s)
        p.write_bytes(s.encode('utf-8'))

    print('copied %d files, fetched %d covers, dropped %d:' % (sum(1 for _ in dest.rglob('*') if _.is_file()), len(covers), len(dropped)))
    for k in ('wp-json/', 'feed', '?p=', 'et_temp', 'xmlrpc', 'wlwmanifest', '__MACOSX'):
        print('  %4d %s' % (sum(k in r for r in dropped), k))


def local(dest, rel, up, path):
    """Relative link for an absolute chnm.gmu.edu/dimenovels/<path>, or the live URL when the copy lacks it."""
    path = path.rstrip('/')
    for base in (path, path[3:] if path.startswith('wp/') else 'wp/' + path):   # a few content links have wp/ wrong
        for cand in (base, base + '.html', base + '/index.html', 'index.html' if not base else None):
            if cand and (dest / cand).is_file():
                return up + cand
    return LIVE + path


if __name__ == '__main__':
    main(*sys.argv[1:])
