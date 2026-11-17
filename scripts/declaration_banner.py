#!/usr/bin/env python3
"""Keep the RRCHNM static-copy banner on every page of the flattened chnm.gmu.edu/declaration (chnm/sustainability#154, #62).

The live server already showed the banner (utils/snippets/chnm_sustainability_banner.html) on every page but the
menu frame. This rewrites each copy to the same markup as the other flattened sites, with the logo path relative
(the site is a sub-path of chnm.gmu.edu), and adds it where it is missing. menu.html, the 10%-high bottom frame,
is skipped so the frameset shows one banner. Idempotent. Run from anywhere:  python3 scripts/declaration_banner.py
"""
import os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'declaration'
ENC = 'latin-1'
SKIP = {'menu.html'}
BANNER = ('<div class="notice" style="font-size: 12px; display: flex; align-items: center; background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd; margin-bottom: 0;">{nl}'
          '    <a href="https://rrchnm.org" target="_blank" rel="noopener"><img src="{rel}images/rrchnm_logo.png" alt="RRCHNM Logo" style="height: 30px; margin-right: 15px;"/></a>{nl}'
          '    <div>This is a static copy of the final website maintained by the <a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig Center for History and New Media</a>.</div>{nl}'
          '</div>')
OLD = re.compile(r'<div class="notice".*?</div>\s*</div>', re.S)


def main():
    n = 0
    pages = sorted(ROOT.rglob('*.htm*'))
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        if rel in SKIP:
            continue
        doc = p.read_bytes().decode(ENC)   # bytes: keep the mixed CR/LF line endings as they are
        old = OLD.search(doc)
        nl = re.search(r'\r\n|\r|\n', old.group(0) if old else doc).group(0)   # the live banner was pasted in with LF
        up = os.path.relpath(ROOT, p.parent).replace(os.sep, '/')
        banner = BANNER.format(nl=nl, rel='' if up == '.' else up + '/')
        if old:
            new = OLD.sub(lambda m: banner, doc, count=1)
        else:
            body = re.search(r'<body\b[^>]*>\s*(<a class="skip-link"[^>]*>[^<]*</a>\s*)?', doc, re.I)
            new = doc[:body.end()] + banner + nl + doc[body.end():]
        if new != doc:
            p.write_bytes(new.encode(ENC))
            n += 1
    print('banner updated on %d pages' % n)
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        doc = p.read_bytes().decode(ENC)
        logo = re.search(r'<img src="([^"]*rrchnm_logo\.png)"', doc)
        if rel not in SKIP and (doc.count('class="notice"') != 1 or not (p.parent / logo.group(1)).exists()):
            sys.exit('self-check failed: ' + rel)
    print('self-check ok')


if __name__ == '__main__':
    main()
