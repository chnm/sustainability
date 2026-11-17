#!/usr/bin/env python3
"""Repair the MARS copy of locallinkages.org after import (chnm/sustainability#152).

The crawler wrote links as style.css%3Fver=5.3.4.css, but the MARS zip names the files style.css_ver=5.3.4.css, so
no stylesheet, script or font loaded. Relative %3F in href/src/url() becomes _. Also strips the <head> links and
login link that point at the removed wp-json/, wp-login and wp-admin debris, and renames the League Spartan
WOFF2 font the crawler saved as .woff2.html. Idempotent. Run from the repo root:
python3 scripts/locallinkages_cleanup.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'locallinkages'

REF = re.compile(r'''((?:href|src)=['"]|url\(["']?)(?!https?:|//|data:)([^'")]*%3F[^'")]*)''')
DEBRIS = [
    re.compile(r"<link rel='https://api\.w\.org/'[^>]*>\n?"),
    re.compile(r'<link rel="alternate" type="(?:application/json|text/xml)\+oembed"[^>]*>\n?'),
    re.compile(r'\t*<script type="text/javascript">var ajaxurl = [^<]*</script>\n?'),
    re.compile(r'<a class="login-link" href="[^"]*wp-login\.php\.html">Log in</a>'),
]


FONT = ROOT / 'wp-content/themes/foundation-press/dist/assets/fonts/leaguespartan-bold.woff2'


def fix(doc):
    doc = doc.replace('leaguespartan-bold.woff2.html', 'leaguespartan-bold.woff2')
    doc = REF.sub(lambda m: m.group(1) + m.group(2).replace('%3F', '_'), doc)
    for rx in DEBRIS:
        doc = rx.sub('', doc)
    return doc


def main():
    if FONT.with_suffix('.woff2.html').exists():
        FONT.with_suffix('.woff2.html').rename(FONT)
    n = 0
    for p in sorted(ROOT.rglob('*')):
        if p.suffix not in ('.html', '.css'):
            continue
        old = p.read_bytes().decode('utf-8')
        new = fix(old)
        if new != old:
            p.write_bytes(new.encode('utf-8'))
            n += 1
    print('cleaned %d files' % n)


if __name__ == '__main__':
    assert fix("href='a.css%3Fver=1.css'") == "href='a.css_ver=1.css'"
    assert fix('url(../f.eot%3F12)') == 'url(../f.eot_12)'
    assert fix('href="https://x.org/?a%3Fb"') == 'href="https://x.org/?a%3Fb"'
    main()
