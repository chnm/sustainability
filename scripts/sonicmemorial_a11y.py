#!/usr/bin/env python3
"""Site-wide WCAG 2.2 AA markup fixes for the flattened sonicmemorial.org (chnm/sustainability#156).

Per page: lang="en"; viewport meta + a11y.css; skip link to an h1 (#content): the page's own orange title, or a
visually hidden one on the nav pages and the home page, with later orange titles as h2; descriptive <title>s;
alt="" on spacers and rules and alt on interface images that carry text; pop-up links (Pop, Pop2, open_window,
openBrowserWindow) become plain links, and the slides' javascript:window.close() image links become a "Back to
the story" link; links to .jsp pages saved as .jsp.html are fixed; empty links go; mouse-only rollovers also run
on keyboard focus; the jump menus get a label and a Go button instead of navigating on change (3.2.2); inputs get
labels; the two forms that no longer send say so; image-map areas get alt; the Mohawk slides' picture is
a real image instead of a body background under a transparent link.

Run sonicmemorial_media.py first. Idempotent. Run from the repo root:  python3 scripts/sonicmemorial_a11y.py
"""
import html, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'sonicmemorial'
ENC = 'latin-1'
ORIGIN = 'https://sonicmemorial.org/'
SITE = 'The Sonic Memorial Project'

DECORATIVE = re.compile(r'(^|/)(spacer\w*|\w*dotline\w*|redsquare\w*|cross|arrow_(right|down)|timeline_kreuz|'
                        r'archive_header_lines\d|home_anibrowser|leer|iconsound|press_listen)\.gif$', re.I)
# interface images whose text is the content (transcribed from the images)
IMG_ALT = {
    'nav/home_about.gif': 'About', 'nav/home_addsound.gif': 'Add a Sound', 'nav/home_browser.gif': 'Sonic Browser',
    'nav/home_educators.gif': 'For Educators', 'nav/home_stories.gif': 'Stories', 'nav/home_timeline.gif': 'Timeline',
    'nav/home_archive.gif': 'Archive',
    'nav/home_about_txt.gif': 'Find out about the Sonic Memorial Project, its creators, and the national collaboration.',
    'nav/home_browser_txt.gif': 'Immerse yourself in this interactive soundscape of voices, stories, and audio traces from the World Trade Center. Requires Flash 6',
    'nav/home_educators_txt.gif': 'Introduce the Sonic Memorial Project to your students with these curriculum ideas.',
    'nav/home_stories_txt.gif': "Listen to Radio Row, Mohawk Ironworkers, and other stories produced by NPR's Lost & Found Sound and independent producers across the country.",
    'nav/home_timeline_txt.gif': 'Learn about the history of the World Trade Center and its neighborhood.',
    'nav/home_archive_txt.gif': 'Search the archive for personal or historic recordings and sonic traces of the World Trade Center.',
    'sub_logo.gif': SITE, 'sub_logo4.gif': SITE, 'stories_more.gif': 'More about this story', 'stories_mp3.gif': 'Listen to MP3',
    'stories_image3.gif': 'Stories', 'about_image3.gif': 'About the Project', 'edu_image3.gif': 'For Educators',
    'WinMedia.gif': 'Windows Media', 'quicktimelogo.gif': 'QuickTime', 'winamp.gif': 'Winamp', 'itunes.gif': 'iTunes',
    'support_cpb.gif': 'Corporation for Public Broadcasting', 'support_nea.gif': 'National Endowment for the Arts',
    'support_npr.gif': 'NPR',
}
NUMBERED = re.compile(r'(^|/)(edu|pop|add_no)_?0?(\d)\.gif$')        # orange "1", "2" ... step markers
YEAR = re.compile(r'(^|/)timeline_(\d{4})\.gif$')
# the nav pages: a hidden h1 after the header; their orange titles become h2
SUB_H1 = {'about.html': 'About the Project', 'add.html': 'Add a Sound', 'educators.html': 'For Educators',
          'press.html': 'Press', 'stations.html': 'For Radio Stations', 'stories.html': 'Stories', 'timeline.html': 'Timeline'}
NO_H2 = {'press.html', 'stations.html'}                         # orange tab rows, not headings
NOT_HEADINGS = {'(646) 926-1357', 'You can upload your digital files online.'}
INPUT_LABELS = {'realname': 'Your name', 'email': 'Email address', 'name': 'Name',
                'comments': 'How have you used the Sonic Memorial Project in the classroom?'}
DEAD_FORM = '<p class="sm-lost">This form no longer sends anything; it is kept as part of the archived page.</p>'


def read(p):
    return p.read_bytes().decode(ENC)   # bytes: keep the CRLF line endings as they are


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def esc(s):
    return html.escape(s, quote=True).encode('ascii', 'xmlcharrefreplace').decode()


def up(p):
    rel = os.path.relpath(ROOT, p.parent).replace(os.sep, '/')
    return '' if rel == '.' else rel + '/'


def resolve(p, target):
    """A pop-up/option target as a working relative link (pages under .jsp were saved as .jsp.html)."""
    path, _, frag = target.partition('#')
    if path.startswith(ORIGIN):
        path = up(p) + path[len(ORIGIN):]
    if path and not (p.parent / path).exists() and (p.parent / (path + '.html')).exists():
        path += '.html'
    return path + ('#' + frag if frag else '')


def slide_parents():
    parents = {}
    for p in ROOT.rglob('*.html'):
        for t in re.findall(r"open_window\('([^']+)'", read(p)):
            parents.setdefault((p.parent / t).resolve(), p)
    return parents


def img_alt(doc, p):
    def fix(m):
        tag = m.group(0)
        # filename alts on three Radio Row slides: drop them so utils/alt-text describes the pictures
        tag = re.sub(r'\salt="(lgradiorow1955|radiolgad1| )"', '', tag)
        if re.search(r'\salt=', tag, re.I):
            return tag
        src = re.search(r'src="([^"]+)"', tag, re.I)
        if not src:
            return tag
        s = re.sub(r'^(\.\./)+|^' + re.escape(ORIGIN), '', src.group(1)).removeprefix('images/')
        alt = None
        if DECORATIVE.search(s):
            alt = ''
        elif s in IMG_ALT:
            alt = IMG_ALT[s]
        elif NUMBERED.search(s):
            alt = NUMBERED.search(s).group(3)
        elif YEAR.search(s):
            alt = YEAR.search(s).group(2)
        if alt is None:
            return tag                          # content image: left for utils/alt-text
        return re.sub(r'^<img', '<img alt="%s"' % esc(alt), tag, flags=re.I)
    return re.sub(r'<img\b[^>]*>', fix, doc, flags=re.I)


def links(doc, p, parents):
    doc = re.sub(r'href="javascript:openBrowserWindow\(\);?"', 'href="%ssm_detector.html"' % up(p), doc, flags=re.I)
    doc = re.sub(r'''href="javascript:(?:Pop2?|open_window)\('([^']+)'[^"]*"''',
                 lambda m: 'href="%s"' % resolve(p, m.group(1)), doc, flags=re.I)
    doc = re.sub(r'(<option\b[^>]*value=")([^"#][^"]*\.jsp)(")', lambda m: m.group(1) + resolve(p, m.group(2)) + m.group(3), doc, flags=re.I)
    doc = re.sub(r'(href=")([^"]+\.jsp)(")', lambda m: m.group(1) + resolve(p, m.group(2)) + m.group(3), doc, flags=re.I)
    doc = re.sub(r'(src=")' + re.escape(ORIGIN) + r'([^"]+)(")',
                 lambda m: m.group(1) + up(p) + m.group(2) + m.group(3) if (ROOT / m.group(2)).exists() else m.group(0), doc)

    # slides: the picture itself was a "close window" link
    parent = parents.get(p.resolve())
    back = '<p class="sm-back"><a href="%s">Back to the story</a></p>' % (
        os.path.relpath(parent, p.parent).replace(os.sep, '/') if parent else up(p) + 'stories.html')
    body_bg = re.search(r'(<body\b[^>]*?)\s+background="([^"]+)"', doc, re.I)

    def close(m):
        img = m.group(1)
        if 'leer.gif' in img and body_bg:       # transparent overlay on a body-background picture
            w = re.search(r'width="(\d+)"', img).group(1); h = re.search(r'height="(\d+)"', img).group(1)
            img = '<img src="%s" width="%s" height="%s">' % (body_bg.group(2), w, h)
        return img + back
    doc = re.sub(r'<a href="javascript:window\.close\(\)">\s*(<img\b[^>]*>)\s*</a>', close, doc, flags=re.I)
    if body_bg and 'sm-back' in doc and body_bg.group(2) in doc[body_bg.end():]:
        doc = doc[:body_bg.start()] + body_bg.group(1) + doc[body_bg.end():]

    doc = re.sub(r'<a\b[^>]*href="[^"]*"[^>]*>\s*</a>', '', doc, flags=re.I)        # empty links
    # rollovers (captions on the home page, nav image swaps) also follow keyboard focus
    def focus(m):
        tag = m.group(0)
        if re.search(r'\sonfocus=', tag, re.I):
            return tag
        over = re.search(r'\sonmouseover="([^"]*)"', tag, re.I)
        out = re.search(r'\sonmouseout="([^"]*)"', tag, re.I)
        if not over or 'status=' in over.group(1):
            return tag
        add = ' onfocus="%s"' % over.group(1) + (' onblur="%s"' % out.group(1) if out else '')
        return tag[:-1] + add + '>'
    doc = re.sub(r'<a\b[^>]*>', focus, doc, flags=re.I)
    # home page: the "+" under each nav label was a second link to the same page
    doc = re.sub(r'<a\b[^>]*>\s*(<img\b[^>]*src="images/cross\.gif"[^>]*>)(\s*</a>)?', r'\1', doc, flags=re.I)
    return doc.replace(ORIGIN + 'press/www.picture-projects.com/', 'http://www.picture-projects.com/')


def forms(doc):
    def select(m):
        tag = m.group(0)
        if 'aria-label' in tag:
            return tag
        tag = re.sub(r'\sonchange="[^"]*"', '', tag, flags=re.I)
        return tag[:-1] + ' aria-label="Go to another page">'
    doc = re.sub(r'<select\b[^>]*>', select, doc, flags=re.I)
    go = ('<button type="button" class="sm-go" onclick="var s=this.previousElementSibling, o=s.options[s.selectedIndex];'
          ' if (o.hasAttribute(\'value\') &amp;&amp; o.value != \'#\') location.href = o.value;">Go</button>')
    doc = re.sub(r'(<select\b[^>]*aria-label="Go to another page"[^>]*>.*?</select>)(?!\s*<button)', r'\1 ' + go.replace('\\', '\\\\'), doc, flags=re.I | re.S)

    def field(m):
        tag = m.group(0)
        name = re.search(r'name="([^"]+)"', tag, re.I)
        if 'aria-label' in tag or re.search(r'type="?(hidden|submit)', tag, re.I) or not name or name.group(1) not in INPUT_LABELS:
            return tag
        return tag[:-1] + ' aria-label="%s">' % INPUT_LABELS[name.group(1)]
    doc = re.sub(r'<(input|textarea)\b[^>]*>', field, doc, flags=re.I)
    if DEAD_FORM not in doc:
        doc = re.sub(r'(<form action="(?:mailto:acorn@picture-projects\.com|contact_us\.jsp\.html)")', DEAD_FORM + r'\1', doc, flags=re.I)
    return doc


def areas(doc, p):
    def fix(m):
        tag = m.group(0)
        if re.search(r'\salt=', tag, re.I):
            return tag
        href = re.search(r'href="([^"]+)"', tag, re.I)
        target = p.parent / href.group(1) if href else None
        cap = ''
        if target and target.exists():
            c = re.search(r'class="txt11Blue">(.*?)</td>', read(target), re.S)
            cap = text(c.group(1)) if c else ''
        return tag[:-1] + ' alt="%s">' % esc(cap or 'Photograph')
    return re.sub(r'<area\b[^>]*>', fix, doc, flags=re.I)


HEAD_RE = re.compile(r'<(span|p|td|a|div)\b([^>]*)class="txt16Orange"([^>]*)>(.*?)</\1>', re.I | re.S)


def headings(doc, p):
    name = p.relative_to(ROOT).as_posix()
    title = re.search(r'<title>(.*?)</title>', doc, re.I | re.S)
    title = text(title.group(1)) if title else SITE
    h1 = None
    if 'id="content"' not in doc:
        if name in SUB_H1 or name == 'index.html':
            h1 = SUB_H1.get(name, SITE)
            tag = '<h1 id="content" tabindex="-1" class="visually-hidden">%s</h1>\n' % esc(h1)
            nav = re.search(r'END MAIN NAV', doc)
            if nav:     # after the header table that holds the nav
                depth = len(re.findall(r'<table\b', doc[:nav.start()], re.I)) - len(re.findall(r'</table>', doc[:nav.start()], re.I))
                for t in re.finditer(r'<(/?)table\b[^>]*>', doc[nav.start():], re.I):
                    depth += -1 if t.group(1) else 1
                    if depth == 0:
                        at = nav.start() + t.end(); break
            else:
                at = doc.index('<div id="sm-banner-wrap" style="position:relative;">') + len('<div id="sm-banner-wrap" style="position:relative;">')
            doc = doc[:at] + '\n' + tag + doc[at:]
    level = [1 if 'id="content"' not in doc else 2]

    def fix(m):
        el, a1, a2, inner = m.groups()
        x = text(inner)
        if not x or x in NOT_HEADINGS or x[0] in '“"' or name in NO_H2 or re.match(r'\s*<h[12]', inner, re.I) \
                or doc[max(0, m.start() - 24):m.start()].endswith('class="sm-h">'):
            return m.group(0)
        n = level[0]; level[0] = 2
        attrs = ' id="content" tabindex="-1"' if n == 1 else ''
        nonlocal h1
        if n == 1:
            h1 = x
        if el.lower() == 'a':
            return '<h%d class="sm-h"%s>%s</h%d>' % (n, attrs, m.group(0), n)
        if el.lower() == 'td':
            return '<td%sclass="txt16Orange"%s><h%d class="txt16Orange sm-h"%s>%s</h%d></td>' % (a1, a2, n, attrs, inner, n)
        return '<h%d class="txt16Orange sm-h"%s>%s</h%d>' % (n, attrs, inner, n)
    doc = HEAD_RE.sub(fix, doc)
    if 'id="content"' not in doc:      # no visible title anywhere: hidden h1 from the <title>
        at = doc.index('<div id="sm-banner-wrap" style="position:relative;">') + len('<div id="sm-banner-wrap" style="position:relative;">')
        doc = doc[:at] + '\n<h1 id="content" tabindex="-1" class="visually-hidden">%s</h1>' % esc(title) + doc[at:]
    h1 = h1 or text(re.search(r'<h1\b[^>]*>(.*?)</h1>', doc, re.I | re.S).group(1))
    if title.lower() == SITE.lower() and name != 'index.html':
        doc = re.sub(r'<title>.*?</title>', '<title>%s | %s</title>' % (esc(h1), SITE), doc, count=1, flags=re.I | re.S)
    return doc


def head(doc, p):
    if not re.search(r'<html\b[^>]*\slang=', doc, re.I):
        doc = re.sub(r'<html\b', '<html lang="en"', doc, count=1, flags=re.I)
    if 'a11y.css' not in doc:
        doc = re.sub(r'</head>', '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                     '<link rel="stylesheet" href="%sa11y.css" type="text/css">\n</head>' % up(p), doc, count=1, flags=re.I)
    if 'class="skip-link"' not in doc:
        doc = re.sub(r'(<body\b[^>]*>)', r'\1\n<a class="skip-link" href="#content">Skip to content</a>', doc, count=1, flags=re.I)
    return doc


# 1.4.13: the home page captions (shown on hover and focus) vanished as soon as the pointer left the link, so the
# pointer could not reach them, and nothing dismissed them. Hiding now waits a moment and is cancelled while the
# pointer is on the caption; Escape hides them all.
CAPTIONS_JS = '''<script>
(function () {
  var pending = null, timer = null;
  function showHide(a) {    /* MM_showHideLayers reads MM_showHideLayers.arguments, so it cannot be called from here */
    for (var i = 0; i + 2 < a.length; i += 3) { var el = document.getElementById(a[i]); if (el) el.style.visibility = a[i + 2] == 'show' ? 'visible' : 'hidden'; }
  }
  function flush() { clearTimeout(timer); if (pending) { var a = pending; pending = null; showHide(a); } }
  MM_showHideLayers = function () {
    var a = arguments, hides = false;
    for (var i = 2; i < a.length; i += 3) if (a[i] == 'hide') hides = true;
    if (pending && !hides && pending[0] == a[0]) { clearTimeout(timer); pending = null; }   /* back on the same caption */
    flush();
    if (hides) { pending = a; timer = setTimeout(flush, 600); } else showHide(a);
  };
  document.addEventListener('keydown', function (e) {
    if (e.key != 'Escape') return;
    flush();
    var d = document.querySelectorAll('[id$="_txt"], #browser_ani');
    for (var i = 0; i < d.length; i++) d[i].style.visibility = 'hidden';
    var t = document.getElementById('today'); if (t) t.style.visibility = 'visible';
  });
})();
</script>
'''


def captions(doc, p):
    if p.name != 'index.html' or p.parent != ROOT:
        return doc
    doc = re.sub(r'<script>\n\(function \(\) \{\n  var (showHide = MM_showHideLayers, )?pending.*?</script>\n', '', doc, flags=re.S)   # replace an older copy
    doc = re.sub(r'(<div id="(\w+_txt)" style="[^"]*")>',
                 lambda m: '%s onmouseover="MM_showHideLayers(\'%s\',\'\',\'show\')" onmouseout="MM_showHideLayers(\'%s\',\'\',\'hide\')">' % (m.group(1), m.group(2), m.group(2)), doc)
    return re.sub(r'</body>', CAPTIONS_JS + '</body>', doc, count=1, flags=re.I)


def main():
    parents = slide_parents()
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        if p.name == '_sheet.html':
            continue
        doc = read(p)
        new = captions(head(doc, p), p)
        new = links(new, p, parents)
        new = img_alt(new, p)
        new = forms(new)
        new = areas(new, p)
        new = headings(new, p)
        if new != doc:
            p.write_bytes(new.encode(ENC)); n += 1
    print('updated %d pages' % n)

    # self-check
    for p in ROOT.rglob('*.html'):
        if p.name == '_sheet.html':
            continue
        doc = read(p)
        assert re.search(r'<html[^>]*lang="en"', doc, re.I), p
        assert doc.count('id="content"') == 1 and 'class="skip-link"' in doc, p
        assert not re.search(r'href="javascript:(Pop|open_window|openBrowserWindow|window\.close)', doc, re.I), p
        assert not re.search(r'<select\b[^>]*onchange', doc, re.I), p
        for s in re.findall(r'href="([^"#:]+)"', re.sub(r'<!--.*?-->', '', doc, flags=re.S)):
            assert (p.parent / s).exists(), (p, s)
    print('self-check ok')


if __name__ == '__main__':
    main()
