#!/usr/bin/env python3
"""Site-wide WCAG 2.2 AA markup fixes for the flattened chnm.gmu.edu/declaration (chnm/sustainability#154).

Idempotent; pages are read and written as bytes so their mixed CR/LF line endings stay as they are.
Run from anywhere:  python3 scripts/declaration_a11y.py

Per page: lang="en"; viewport meta + a11y.css; the dead Piwik tracker removed; the page title graphic or
first large bold line becomes the <h1> and names the <title>; section headings become <h2>; <ul> used only
to indent (no <li>) becomes <div class="indent">; footnote links match their anchors' case; images of single
letters (Polish l/s/n, macron o) become the letters; alt on the site graphics and the scanned translations;
a skip link to the <h1>. The frameset gets frame titles and a menu frame that can scroll when zoomed.
"""
import html, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'declaration'
ENC = 'latin-1'           # the pages are ASCII; latin-1 round-trips any stray byte
SITE = 'JAH Roundtable'

# 1.1.1 / 1.4.5: 5-12px GIFs standing in for letters the 1999 fonts lacked (checked at 10x against the words they sit in).
L_STROKE, S_ACUTE, N_ACUTE, O_MACRON = '&#322;', '&#347;', '&#324;', '&#333;'
KUTNIK = {1: L_STROKE, 3: L_STROKE, 4: L_STROKE, 5: S_ACUTE, 6: L_STROKE, 7: S_ACUTE, 8: L_STROKE, 9: N_ACUTE,
          10: N_ACUTE, 11: S_ACUTE, 12: N_ACUTE, 13: S_ACUTE, 14: L_STROKE, 15: L_STROKE}
GLYPHS = [
    (re.compile(r'\s*<img src="kutnik-8\.gif"[^>]*>\s*'), L_STROKE),                 # "Wies <img> aw" -> Wiesław
    (re.compile(r'\s*<img src="eoyang/eoyang-[23]\.gif"[^>]*>\s*'), O_MACRON),       # "k <img> fuku" -> kōfuku
    (re.compile(r'\s*<img src="eoyang/eoyang-4\.gif"[^>]*>'), O_MACRON),             # "shik <img>" -> shikō
    (re.compile(r'</em>\s*<img src="aruga-107\.gif"[^>]*>'), O_MACRON + '</em>'),     # "kenp</em> <img> <em>o unda" -> kenpō o unda
    (re.compile(r'<img src="kutnik-(\d+)\.gif"[^>]*>'), lambda m: KUTNIK[int(m.group(1))]),
]

# 1.1.1: site graphics. The four clip-art pictures on the opening page are decoration.
ALTS = {
    'images/header.gif': 'Declaration',
    'images/dec.gif': 'Declaration:',
    'images/test2.gif': 'Interpreting the Declaration of Independence by Translation',
    'images/chnms.gif': 'Center for History and New Media',
    'images/scoutsel.gif': 'Scout Report Selection',
    'images/glasses2.gif': '', 'images/book.jpg': '', 'images/cup.jpg': '', 'images/mark.jpg': '',
}
# Scanned pages of printed translations: (language, year, number of pages). The page's heading names the source.
SCANS = {'russian1': ('Russian', '1901', 4), 'russian2': ('Russian', '1935', 5), 'japanese/japan1': ('Japanese', '1866', 5),
         'japanese/japan2': ('Japanese', '1952', 9), 'japanese/japan3': ('Japanese', '1998', 9)}
SCAN_FILES = {'hebrew/one.html': ('Hebrew', '1969', 1, 1), 'hebrew/two.html': ('Hebrew', '1945', 1, 2),
              'hebrew/three.html': ('Hebrew', '1945', 2, 2), 'polone.html': ('Polish', '1992', 1, 3),
              'poltwo.html': ('Polish', '1992', 2, 3), 'polthr.html': ('Polish', '1992', 3, 3)}
NUMS = 'one two three four five six seven eight nine'.split()
# Essay figures with captions beside them: left to utils/alt-text (see the PR).
FIGURES = re.compile(r'images/(resized|french)/|images/thelen\d\.jpg')

# 3.1.2: pages that print a translation in full. A paragraph gets the page's language when its stopwords say so.
PAGE_LANG = {'german1.html': 'de', 'german2.html': 'de', 'italian1.html': 'it', 'italian2.html': 'it',
             'spanish2.html': 'es', 'malay2.html': 'ms'}
STOPWORDS = {
    'en': 'the and of to that in for by with their our has have is are which be them these',
    'de': 'der die das und den ein eine nicht zu von mit sich des dem ist f\u00fcr auf sie unsere',
    'it': 'il la di che per del della le non un una alla sono degli nel ha delle questi',
    'es': 'el la de que y los las del por para con una se en su ha nuestros',
    'ms': 'dan yang untuk di kepada dengan ini bagi telah beliau kita mereka dalam',
}
STOPWORDS = {k: set(v.split()) for k, v in STOPWORDS.items()}


def tag_languages(doc, lang):
    def repl(m):
        words = re.findall(r'\w+', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2))).lower())
        own = sum(w in STOPWORDS[lang] for w in words)
        en = sum(w in STOPWORDS['en'] for w in words)
        if (own >= 3 and own > 2 * en) or (own >= 2 and en == 0):
            return '<p%s lang="%s">%s' % (m.group(1), lang, m.group(2))
        return m.group(0)
    # many of these <p> are never closed: a paragraph runs to </p>, the next <p> or the end of its <div>
    return re.sub(r'<p\b((?:(?!\slang=)[^>])*)>(.*?)(?=</p>|<p\b|</div>|</td>)', repl, doc, flags=re.S | re.I)


FRAME_TITLES = {'one.html': 'Content', 'menu.html': 'Site menu'}
PIWIK = re.compile(r'<!-- Piwik -->.*?<!-- End Piwik Code -->[ \t]*\r?\n?', re.S)
SKIP_LINK = '<a class="skip-link" href="#content">Skip to content</a>'


def newline(doc):
    m = re.search(r'\r\n|\r|\n', doc)
    return m.group(0) if m else '\n'


def text_of(fragment):
    # headings were broken into lines with <br>: join the lines, with a comma before a new part
    t = re.sub(r'(:\s*)<br\s*/?>', r'\1 ', fragment, flags=re.I)
    t = re.sub(r'^(\s*<[^>]+>)*Appendix\s*<br\s*/?>', 'Appendix: ', t, flags=re.I)
    t = re.sub(r'\s*<br\s*/?>\s*(?=Page \w+ of|From )', ', ', t, flags=re.I)
    t = re.sub(r'<br\s*/?>', ' ', t, flags=re.I)
    t = html.unescape(re.sub(r'<[^>]+>', '', t))
    t = re.sub(r'\s+', ' ', t).strip()
    return re.sub(r'\s*,(\s*,)+', ',', t).strip(' ,:.')


def scan_alt(rel):
    if rel in SCAN_FILES:
        lang, year, n, total = SCAN_FILES[rel]
    else:
        d, f = rel.rsplit('/', 1)
        if d not in SCANS:
            return None
        lang, year, total = SCANS[d]
        stem = f[:-5]
        n = int(stem[-1]) if stem.startswith('japan') else NUMS.index(stem) + 1
    page = '' if total == 1 else 'page %d of %d of ' % (n, total)
    return 'Scan of %sthe %s %s translation' % (page, year, lang)


def fix_images(doc, rel):
    for pat, rep in GLYPHS:
        doc = pat.sub(rep, doc)

    def repl(m):
        tag = m.group(0)
        src = re.search(r'\ssrc="([^"]*)"', tag, re.I).group(1)
        if re.search(r'\salt=', tag, re.I) and not re.search(r'\salt="image"', tag, re.I):
            return tag
        key = os.path.normpath(os.path.join(os.path.dirname(rel), src)).replace(os.sep, '/')
        alt = ALTS.get(key)
        if alt is None and re.fullmatch(r'(one|two|three|four|five|six|seven|eight|nine|images/pol\w+)\.gif', src):
            alt = scan_alt(rel)
        if alt is None:
            return tag
        tag = re.sub(r'\salt="image"', '', tag, flags=re.I)
        return tag[:-1].rstrip() + ' alt="%s">' % html.escape(alt)
    doc = re.sub(r'<img\b[^>]*>', repl, doc, flags=re.I)
    # 2.5.8: give the remote Creative Commons badge its real size so its link box holds even if it fails to load
    return doc.replace('src="http://i.creativecommons.org/l/by-sa/3.0/88x31.png" />',
                       'src="http://i.creativecommons.org/l/by-sa/3.0/88x31.png" width="88" height="31" />')


H1_FONT = re.compile(r'(<p>\s*)?((?:<font\b[^>]*\bsize="?(?:5|6|\+2)"?[^>]*>.*?</font>\s*)+)(</p>)?', re.S | re.I)
H1_SCAN = re.compile(r'<div align="left">\s*<ul>\s*<p>(Declaration of Independence in .*?)</p>\s*</ul>\s*</div>', re.S)
H1_HOME = re.compile(r'<img src="images/dec\.gif"[^>]*><img src="images/test2\.gif"[^>]*>')


def add_h1(doc):
    if 'id="content"' in doc:
        return doc
    m = H1_HOME.search(doc)
    if m:
        return doc[:m.start()] + '<h1 class="pg" id="content" tabindex="-1">' + m.group(0) + '</h1>' + doc[m.end():]
    m = H1_SCAN.search(doc)
    if m:
        return doc[:m.start()] + '<h1 class="pg scan" id="content" tabindex="-1">' + m.group(1) + '</h1>' + doc[m.end():]
    m = H1_FONT.search(doc)
    if m:   # take a wrapping <p> with it only when both its tags are there
        start, end = (m.start(), m.end()) if m.group(1) and m.group(3) else (m.start(2), m.end(2))
        return doc[:start] + '<h1 class="pg" id="content" tabindex="-1">' + m.group(2).rstrip() + '</h1>' + doc[end:]
    return doc


def h1_text(doc):
    m = re.search(r'<h1 class="pg[^"]*"[^>]*>(.*?)</h1>', doc, re.S)
    if not m:
        return None
    imgs = ' '.join(re.findall(r'alt="([^"]*)"', m.group(1)))
    return text_of(m.group(1)) or text_of(imgs)


def fix_headings(doc):
    # 1.3.1: run-in section headings in the essays and the appendix
    doc = re.sub(r'<p class="(S1|APS1)">(.*?)</p>', r'<h2 class="\1">\2</h2>', doc, flags=re.S)
    # oltra.html wraps its rule in an empty <h1 class="AU">
    doc = re.sub(r'<h1 class="AU">(\s*<hr>\s*)</h1>', r'<div class="AU">\1</div>', doc)
    # "Translations:" / "Related JAH Articles:" on the language pages
    return re.sub(r'<p>(<font size="\+1" face="Comic Sans MS"><b>[^<]*:</b></font>)</p>', r'<h2 class="sub">\1</h2>', doc)


def fix_fragments(doc, name):
    names = {n.lower(): n for n in re.findall(r'\bname="([^"]+)"', doc)}

    def repl(m):
        frag = m.group(2)
        if m.group(1) in ('', name) and frag.lower() in names:
            return 'href="%s#%s"' % (m.group(1), names[frag.lower()])
        return m.group(0)
    return re.sub(r'href="([^"#]*)#([^"]+)"', repl, doc)


def fix_page(p):
    rel = p.relative_to(ROOT).as_posix()
    doc = p.read_bytes().decode(ENC)
    nl = newline(doc)
    doc = PIWIK.sub('', doc)
    doc = re.sub(r'<html(?![^>]*\blang=)', '<html lang="en"', doc, count=1, flags=re.I)
    if 'name="viewport"' not in doc:
        css = os.path.relpath(ROOT / 'a11y.css', p.parent).replace(os.sep, '/')
        head = re.search(r'</head>', doc, re.I)
        doc = (doc[:head.start()] + '<meta name="viewport" content="width=device-width, initial-scale=1">' + nl
               + '<link rel="stylesheet" href="%s">' % css + nl + doc[head.start():])

    if rel == 'index.html':                 # the frameset
        for src, title in FRAME_TITLES.items():
            doc = re.sub(r'<frame src="%s"(?![^>]*title=)' % re.escape(src), '<frame src="%s" title="%s"' % (src, title), doc)
        doc = doc.replace(' scrolling="no"', '')   # 1.4.4/1.4.10: the 10%-high menu frame must scroll when zoomed
    elif rel == 'menu.html':
        doc = re.sub(r'<TITLE>menu</TITLE>', '<TITLE>Site menu | %s</TITLE>' % SITE, doc)
    else:
        doc = add_h1(doc)
        doc = re.sub(r'<(/?)ul\b[^>]*>', lambda m: '</div>' if m.group(1) else '<div class="indent">', doc, flags=re.I)
        doc = fix_headings(doc)
        h1 = h1_text(doc)
        if h1 and rel != 'one.html':
            if h1 == SITE:   # roundtable.html, the table of contents
                h1 = 'Contents'
            title = html.escape('%s | %s' % (h1, SITE), quote=False).encode('ascii', 'xmlcharrefreplace').decode()
            doc = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, doc, count=1, flags=re.S | re.I)
        if SKIP_LINK not in doc:
            doc = re.sub(r'(<body\b[^>]*>)', r'\1' + nl + SKIP_LINK, doc, count=1, flags=re.I)

    doc = fix_images(doc, rel)
    doc = fix_fragments(doc, p.name)
    if rel in PAGE_LANG:
        doc = tag_languages(doc, PAGE_LANG[rel])
    return doc


def check(pages):
    bad = []
    for p in pages:
        rel = p.relative_to(ROOT).as_posix()
        doc = p.read_bytes().decode(ENC)
        if not re.search(r'<html lang="en"', doc, re.I): bad.append((rel, 'lang'))
        if 'piwik' in doc.lower(): bad.append((rel, 'piwik'))
        if re.search(r'kutnik-|eoyang-|aruga-107', doc): bad.append((rel, 'glyph image'))
        for tag in re.findall(r'<img\b[^>]*>', doc, re.I):
            if not re.search(r'\salt=', tag, re.I) and not FIGURES.search(tag): bad.append((rel, 'no alt: ' + tag[:60]))
        names = set(re.findall(r'\b(?:name|id)="([^"]+)"', doc))
        for f, frag in re.findall(r'href="([^"#]*)#([^"]+)"', doc):
            if f in ('', p.name) and frag not in names: bad.append((rel, 'fragment #' + frag))
        if rel in ('index.html', 'menu.html'):
            continue
        if re.search(r'<ul\b', doc, re.I): bad.append((rel, 'ul'))
        if doc.count('<h1 ') != 1 or 'id="content"' not in doc: bad.append((rel, 'h1'))
        if re.search(r'<title>\s*JAH Roundtable\s*</title>', doc, re.I): bad.append((rel, 'title'))
        if doc.count(SKIP_LINK) != 1: bad.append((rel, 'skip link'))
        if rel in PAGE_LANG and ' lang="%s"' % PAGE_LANG[rel] not in doc: bad.append((rel, 'lang of parts'))
    idx = (ROOT / 'index.html').read_bytes().decode(ENC)
    if idx.count(' title="') < 2 or 'scrolling="no"' in idx: bad.append(('index.html', 'frames'))
    return bad


def main():
    pages = sorted(p for p in ROOT.rglob('*.htm*'))
    changed = 0
    for p in pages:
        old = p.read_bytes().decode(ENC)
        new = fix_page(p)
        if new != old:
            p.write_bytes(new.encode(ENC))
            changed += 1
    print('%d of %d pages changed' % (changed, len(pages)))
    again = [p for p in pages if fix_page(p) != p.read_bytes().decode(ENC)]
    bad = check(pages)
    for b in bad:
        print('CHECK', *b)
    if again or bad:
        sys.exit('not idempotent: %s' % [str(p) for p in again] if again else 'self-check failed')
    print('self-check ok')


if __name__ == '__main__':
    main()
