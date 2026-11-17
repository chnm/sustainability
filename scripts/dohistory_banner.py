#!/usr/bin/env python3
"""Add the RRCHNM static-copy banner to every full page of the flattened dohistory.org (chnm/sustainability#147, #62).

Same banner as the other flattened sites here (utils/snippets/chnm_sustainability_banner.html), with the logo
path made relative. Frameset documents and the pages loaded inside frames are skipped so a frame page shows
one banner, not three. Idempotent. Run from the repo root:  python3 scripts/dohistory_banner.py
"""
import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dohistory'
ENC = 'latin-1'
BANNER = ('<div class="notice" style="font-size: 12px; display: flex; align-items: center; background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd; margin-bottom: 0;">\n'
          '    <a href="https://rrchnm.org" target="_blank" rel="noopener"><img src="%srrchnm_logo.png" alt="RRCHNM Logo" style="height: 30px; margin-right: 15px;"/></a>\n'
          '    <div>This is a static copy of the final website maintained by the <a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig Center for History and New Media</a>.</div>\n'
          '</div>\n')


def frame_children():
    kids = set()
    for p in ROOT.rglob('*.html'):
        doc = p.read_bytes().decode(ENC)   # bytes: keep the old Mac CR line endings as they are
        if not re.search(r'<frameset', doc, re.I):
            continue
        for m in re.finditer(r'<frame\s[^>]*src="([^"]+)"', doc, re.I):
            kids.add((p.parent / m.group(1)).resolve())
    return kids


def main():
    skip = frame_children()
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        if p.resolve() in skip or p.parts[-3:-1] == ('dohistory', 'prototype') or 'prototype' in p.parts or 'admin' in p.parts:
            continue
        doc = p.read_bytes().decode(ENC)   # bytes: keep the old Mac CR line endings as they are
        if 'class="notice"' in doc or re.search(r'<frameset', doc, re.I):
            continue
        body = re.search(r'<body(\s[^>]*)?>\s*(<a class="skip-link"[^>]*>[^<]*</a>\s*)?', doc, re.I)
        if not body:
            continue
        rel = os.path.relpath(ROOT, p.parent).replace(os.sep, '/')
        rel = '' if rel == '.' else rel + '/'
        doc = doc[:body.end()] + BANNER % rel + doc[body.end():]
        p.write_bytes(doc.encode(ENC))
        n += 1
    print('banner added to %d pages' % n)


if __name__ == '__main__':
    main()
