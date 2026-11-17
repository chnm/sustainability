#!/usr/bin/env python3
"""RRCHNM static-copy banner on every page of the flattened sonicmemorial.org (chnm/sustainability#156, #62).

The live site already carries the banner from utils/snippets/chnm_sustainability_banner.html, but its logo is
/images/nav/rrchnm_logo.png, which 404s there and which wget rewrote to an absolute sonicmemorial.org URL. The logo
now ships at images/nav/rrchnm_logo.png (the RRCHNM logo used by the other flattened sites) and every banner
points at it relatively; its links open with rel="noopener". Pages written by sonicmemorial_media.py, which have
no banner, get one after the skip link. There is no GMU or RRCHNM logo in the original site.

Idempotent. Run from the repo root after sonicmemorial_a11y.py:  python3 scripts/sonicmemorial_banner.py
"""
import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'sonicmemorial'
ENC = 'latin-1'
LOGO = 'images/nav/rrchnm_logo.png'
BANNER = ('<div class="notice" style="font-size: 12px; display: flex; align-items: center; background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd; margin-bottom: 0;">\n'
          '    <a href="https://rrchnm.org" target="_blank" rel="noopener"><img src="%s" alt="RRCHNM Logo" style="height: 30px; margin-right: 15px;"/></a>\n'
          '    <div>This is a static copy of the final website maintained by the <a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig Center for History and New Media</a>.</div>\n'
          '</div>\n')


def main():
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        doc = p.read_bytes().decode(ENC)   # bytes: keep the CRLF line endings as they are
        rel = os.path.relpath(ROOT / LOGO, p.parent).replace(os.sep, '/')
        new = re.sub(r'src="(?:https://sonicmemorial\.org)?/images/nav/rrchnm_logo\.png"', 'src="%s"' % rel, doc)
        new = new.replace('<a href="https://rrchnm.org" target="_blank">', '<a href="https://rrchnm.org" target="_blank" rel="noopener">')
        if 'class="notice"' not in new:
            skip = re.search(r'<a class="skip-link"[^>]*>[^<]*</a>\r?\n', new)
            new = new[:skip.end()] + BANNER % rel + new[skip.end():]
        if new != doc:
            p.write_bytes(new.encode(ENC)); n += 1
    print('banner fixed or added on %d pages' % n)

    # self-check
    for p in ROOT.rglob('*.html'):
        doc = p.read_bytes().decode(ENC)
        assert doc.count('class="notice"') == 1, p
        logo = re.search(r'class="notice".*?<img src="([^"]+)"', doc, re.S).group(1)
        assert (p.parent / logo).resolve() == (ROOT / LOGO).resolve(), (p, logo)
    print('self-check ok')


if __name__ == '__main__':
    main()
