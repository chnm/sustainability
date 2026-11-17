#!/usr/bin/env python3
"""Add the RRCHNM static-copy banner to every page of the flattened locallinkages.org (chnm/sustainability#152, #62).

Same banner as the other flattened sites here (utils/snippets/chnm_sustainability_banner.html), with the dark logo
the other sites use (locallinkages/rrchnm_logo.png, copied from cyh/; the theme's own logo is white, for the purple
footer) at a relative path. Goes right after the skip link. Idempotent. Run from the repo root:
python3 scripts/locallinkages_banner.py
"""
import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'locallinkages'
LOGO = 'rrchnm_logo.png'
BANNER = ('<div class="notice" style="font-size: 12px; display: flex; align-items: center; background-color: #f8f8f8; color: #0a0a0a; padding: 10px; border: 1px solid #ddd; margin-bottom: 0;">\n'
          '    <a href="https://rrchnm.org" target="_blank" rel="noopener"><img src="%s' + LOGO + '" alt="RRCHNM Logo" style="height: 30px; margin-right: 15px;"/></a>\n'
          '    <div>This is a static copy of the final website maintained by the <a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig Center for History and New Media</a>.</div>\n'
          '</div>\n')


def main():
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        doc = p.read_bytes().decode('utf-8')
        if 'class="notice"' in doc:
            continue
        body = re.search(r'<body(\s[^>]*)?>\s*(<a class="skip-link"[^>]*>[^<]*</a>\s*)?', doc, re.I)
        if not body:
            continue
        rel = os.path.relpath(ROOT, p.parent).replace(os.sep, '/')
        rel = '' if rel == '.' else rel + '/'
        doc = doc[:body.end()] + BANNER % rel + doc[body.end():]
        p.write_bytes(doc.encode('utf-8'))
        n += 1
    print('banner added to %d pages' % n)


if __name__ == '__main__':
    main()
