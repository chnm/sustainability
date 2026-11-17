#!/usr/bin/env python3
"""Add the RRCHNM static-copy banner to every page of the American Women's Dime Novel Project (chnm/sustainability#155, #62).

Same banner as the other flattened sites (utils/snippets/chnm_sustainability_banner.html, as in
scripts/dohistory_banner.py), with the logo path made relative so it resolves wherever the copy is served
(the site lived under chnm.gmu.edu/dimenovels/, where /rrchnm_logo.png is someone else's file). Goes right after
the skip link from dimenovels_a11y.py. Idempotent. Run from the repo root:  python3 scripts/dimenovels_banner.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dimenovels'
BANNER = ('<div class="notice" style="font-size: 12px; display: flex; align-items: center; background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd; margin-bottom: 0;">\n'
          '    <a href="https://rrchnm.org" target="_blank" rel="noopener"><img src="%srrchnm_logo.png" alt="RRCHNM Logo" style="height: 30px; margin-right: 15px;"/></a>\n'
          '    <div>This is a static copy of the final website maintained by the <a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig Center for History and New Media</a>.</div>\n'
          '</div>\n')


def main():
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        doc = p.read_bytes().decode('utf-8')
        if 'class="notice"' in doc:
            continue
        body = re.search(r'<body(\s[^>]*)?>\s*(<a class="skip-link"[^>]*>[^<]*</a>\s*)?', doc)
        up = '../' * p.relative_to(ROOT).as_posix().count('/')
        doc = doc[:body.end()] + BANNER % up + doc[body.end():]
        p.write_bytes(doc.encode('utf-8'))
        n += 1
    print('banner added to %d pages' % n)


if __name__ == '__main__':
    main()
