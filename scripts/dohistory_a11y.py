#!/usr/bin/env python3
"""Site-wide WCAG 2.2 AA markup fixes for the flattened dohistory.org (chnm/sustainability#147).

Idempotent. Run from the repo root:  python3 scripts/dohistory_a11y.py [--dry-run]

Per page: lang="en"; viewport meta + a11y.css; a <title> where missing; skip link and
#content target after the top nav; empty alt on spacers; alt on nav/menu images and
thumbnails; aria-labels on the diary date selects; the "Jump to" select gets a Go button
instead of navigating on change; frames get titles; empty links are removed; book footnote
lists are made valid; unlabeled inputs get aria-labels; image-map areas get alt.
"""
import collections, html, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dohistory'
ENC = 'latin-1'          # the site is ISO-8859-1; latin-1 round-trips every byte
DRY = '--dry-run' in sys.argv

# ---- alt text for sliced nav / menu images (text shown in the image) -----------------
NAV_ALT = {
    'nav_topRed2_twoStories': 'One Rape. Two Stories.', 'nav_topBlu_twoStories': 'One Rape. Two Stories.',
    'nav_topWht_twoStories': 'One Rape. Two Stories.', 'nav_topWht_manMid': 'Martha Ballard and a Man-Midwife',
    'nav_topGrn_toolkit': 'History Toolkit', 'nav_topGray_writingBook': "About Ulrich's Work",
    'nav_topWht_timeline': 'Martha Ballard Timeline', 'nav_topWht_whoWas': 'Who Was Martha Ballard?',
    'MenuControversy': 'The Controversy', 'MenuDrPage': 'Who Was Dr. Ben Page?',
    'MenuMartha': 'Martha and a Man-Midwife', 'MenuSumming': 'Summing Up',
    'SubMenuPage_diary': "Martha's Diary", 'SubMenuPage_drug': 'Drug Ads', 'SubMenuPage_drug1': 'Drugs & Medicines',
    'SubMenuPage_drug2': 'Inoculation', 'SubMenuPage_financial': 'Financial Records', 'SubMenuPage_letters': 'Letters',
    'SubMenuPage_probate': 'Probate Records', 'SubMenuPage_memorial': 'Memorial', 'SubMenuPage_letCover': 'Cover',
    'SubMenuPage_let18010220': 'Feb 20, 1801', 'SubMenuPage_let18010314': 'March 14, 1802',
    'SubMenuPage_let18010409': 'April 9, 1801', 'SubMenuPage_let18011125': 'Nov 25, 1802',
    'SubMenuMartha_entries': 'What She Wrote', 'SubMenuMartha_context': 'The Bigger Picture',
    'SubMenuMartha_sense': 'Making Sense of It', 'SubMenuMartha_happened': "Interpret What Happened from Martha's Point of View",
    'SubMenuCont_Pro': 'Pro', 'SubMenuCont_Con': 'Con', 'SubMenuCont_stone': 'Stone', 'SubMenuCont_blunt': 'Blunt',
    'SubMenuCont_channing': 'Channing', 'SubMenuCont_gregory': 'Gregory', 'SubMenuCont_maubray': 'Maubray',
    'SubMenuCont_nihell': 'Nihell', 'SubMenuCont_smellieC': 'Smellie Collection', 'SubMenuCont_smellieT': 'Smellie Treatise',
    'shockicon': 'Get Shockwave', 'getacro': 'Get Adobe Acrobat Reader', 'qtimelogo': 'Get QuickTime',
    'jumpto': 'Jump to', 'toolkit_docIcon': 'Document', 'switchto_MBstory': "Switch to Martha's story", 'switchto_Official': 'Switch to the official story',
    'img_icon': 'View Image', 'txt_icon': 'View Text', 'left_arrow': 'Map section to the left', 'right_arrow': 'Map section to the right',
    'up_arrow': 'Map section above', 'down_arrow': 'Map section below', 'bullseye': 'Interactive map', 'bullseyeBlue': 'Interactive element',
    'more': 'More', 'back': 'Back', 'blu_dot': '', '100pixels': '', 'title_drugads': 'Drug Ads', 'man-midwife_subTitle': 'Martha and a Man-Midwife', 'rape_subTitle': 'One Rape. Two Stories.',
}
DECORATIVE = re.compile(r'(spacer|shim|transparent|_line|_rule|dot_clear|blank|100pixels|blu_dot)\.gif$', re.I)
ARROW = re.compile(r'(prev|next)[^/]*\.gif$|_pg\.gif$', re.I)
FRAME_TITLES = {'left': 'Chapter text', 'right': 'Document', 'top': 'Timeline navigation', 'bottom': 'Timeline',
                'menu': 'Menu', 'main': 'Content'}
INPUT_LABELS = {'fname': 'First name', 'lname': 'Last name', 'address1': 'Address', 'address': 'Address',
                'realaddress': 'Email address', 'subject': 'Subject', 'fromname': 'Your name', '_fromemail': 'Your email',
                'toname': 'Recipient name', 'mailbody': 'Message', 'number': 'Number of lines', 'refresh': 'Refresh seconds',
                'realname': 'Your name', 'username': 'Email', 'url': 'URL', 'city': 'City', 'state': 'State',
                'country': 'Country', 'comments': 'Comments', 'city1': 'City', 'state1': 'State', 'zip1': 'ZIP code',
                'email': 'Email', 'phone': 'Phone'}

SKIP_LINK = '<a class="skip-link" href="#content">Skip to content</a>\n'
CONTENT_ANCHOR = '<div id="content" tabindex="-1"></div>'
TOPNAV_END = re.compile(r'<!--`?end topnav-->', re.I)

_title_cache = {}


def page_title(path):
    """<title> of a page, cleaned (no ' (I)'/' (T)' suffix)."""
    if path not in _title_cache:
        t = ''
        try:
            m = re.search(r'<title>(.*?)</title>', path.read_text(ENC), re.S | re.I)
            if m:
                t = html.unescape(re.sub(r'\s+', ' ', m.group(1))).strip()
                t = re.sub(r'\s*\((I|T)\)$', '', t)
        except OSError:
            pass
        _title_cache[path] = t
    return _title_cache[path]


def learn_alts():
    """Most common alt text per nav/menu image basename, from pages that have one."""
    seen = collections.defaultdict(collections.Counter)
    for p in ROOT.rglob('*.html'):
        for m in re.finditer(r'<img\s[^>]*?src="([^"]*(?:/nav/|MenuImages/|/images/[^"]*_subTitle)[^"]*)"[^>]*?\balt="([^"]+)"', p.read_text(ENC), re.I):
            base = m.group(1).rsplit('/', 1)[-1]
            if not re.fullmatch(r'[<>&;lgt]+', m.group(2)):
                seen[base][m.group(2)] += 1
    return {b: c.most_common(1)[0][0] for b, c in seen.items()}


def nav_alt(src, learned):
    base = src.rsplit('/', 1)[-1]
    if DECORATIVE.search(base):
        return ''
    if ARROW.search(base):
        what = 'chapter' if '_ch.' in base else 'page'
        return ('Previous ' if 'prev' in base.lower() else 'Next ') + what
    if base in learned:
        return learned[base]
    stem = re.sub(r'\.(gif|jpg)$', '', base, flags=re.I)
    stem = re.sub(r'_(on|off|dft)$', '', stem)
    if stem.endswith('_doHist'):
        return 'DoHistory'
    return NAV_ALT.get(stem)


def set_attr(tag, name, value):
    """Add or replace attribute `name` on a single tag string."""
    pat = re.compile(r'\s' + name + r'\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
    attr = ' %s="%s"' % (name, html.escape(value, quote=True))
    if pat.search(tag):
        return pat.sub(attr, tag, count=1)
    end = -2 if tag.endswith('/>') else -1
    return tag[:end].rstrip() + attr + tag[end:]


def has_attr(tag, name):
    return re.search(r'\s' + name + r'\s*=', tag, re.I) is not None


_map_names = {}


def map_image_alt(path, base):
    """Map section images: names come from the index page's image map (detail1 -> "Fort Western")."""
    d = path.parent
    if d not in _map_names:
        names = {}
        idx = d / 'index.html'
        if idx.exists():
            for m in re.finditer(r'<area\s[^>]*href="([^"]+)\.html"[^>]*\salt="([^"]*)"', idx.read_text(ENC), re.I):
                names[m.group(1)] = html.unescape(m.group(2)).strip()
        _map_names[d] = names
    names = _map_names[d]
    stem, ext = re.match(r'(.*)\.(gif|jpg)$', base, re.I).groups()
    title = page_title(path)
    if re.fullmatch(r'title(_small)?', stem):
        return title
    if stem in ('grid', 'nogrid'):
        return title + (' with grid' if stem == 'grid' else '')
    name = names.get(stem)
    if name is None and re.fullmatch(r'[a-d][1-4]', stem):
        name = 'section ' + stem.upper()
    if name is None:
        return None
    return ('%s, enlarged' % name) if ext.lower() == 'jpg' else ('Locator grid: %s' % name)


def fix_images(doc, path, learned):
    def repl(m):
        tag = m.group(0)
        src = re.search(r'\ssrc\s*=\s*"?([^"\s>]+)', tag, re.I)
        if not src:
            return tag
        s = src.group(1)
        base = s.rsplit('/', 1)[-1]
        if ARROW.search(base) and not DECORATIVE.search(base):
            # '<' / '>' alt on arrows says nothing
            cur = re.search(r'\salt\s*=\s*"([^"]*)"', tag, re.I)
            if not cur or re.fullmatch(r'[\s<>&;lgt]*', cur.group(1)) or (cur.group(1) in ('Previous page', 'Next page') and '_ch.' in base):
                return set_attr(tag, 'alt', nav_alt(s, learned))
        if has_attr(tag, 'alt'):
            return tag
        if DECORATIVE.search(base):
            return set_attr(tag, 'alt', '')
        stem = re.sub(r'\.(gif|jpg)$', '', base, flags=re.I)
        alt = nav_alt(s, learned) if ('/nav/' in s or s.startswith('nav/') or re.match(r'(Sub)?Menu', base) or stem in NAV_ALT or '_subTitle' in base) else None
        if alt is None and '/maps/' in str(path):
            alt = map_image_alt(path, base)
        if alt is None and re.search(r'_thumb\.jpg$', base, re.I):
            # thumbnail: name the page it opens, else this page
            pre = doc[max(0, m.start() - 400):m.start()]
            a = list(re.finditer(r'<a\s[^>]*href="([^"#]+)"[^>]*>\s*$', pre, re.I))
            target = (path.parent / html.unescape(a[-1].group(1))).resolve() if a else path
            t = page_title(target) if target.suffix.lower() == '.html' else ''
            alt = ('Thumbnail: ' + t) if t else 'Page thumbnail'
        if alt is None:
            return tag
        return set_attr(tag, 'alt', alt)
    return re.sub(r'<img\b(?:[^>"]|"[^"]*")*>', repl, doc, flags=re.I)


def fix_head(doc, path):
    rel = os.path.relpath(ROOT, path.parent).replace(os.sep, '/')
    rel = '' if rel == '.' else rel + '/'
    extra = '\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<link rel="stylesheet" href="%sa11y.css">\n' % rel
    if 'a11y.css' in doc:
        return doc
    if not re.search(r'<head[\s>]', doc, re.I):
        if re.search(r'<title>', doc, re.I):
            doc = re.sub(r'(<title>.*?</title>)', r'<head>\1</head>', doc, count=1, flags=re.S | re.I)
        else:
            m = re.search(r'<html[^>]*>', doc, re.I)
            at = m.end() if m else 0
            doc = doc[:at] + '<head></head>' + doc[at:]
    if not re.search(r'<title>', doc, re.I):
        h = re.search(r'<h[1-6][^>]*>(.*?)</h[1-6]>', doc, re.S | re.I) or re.search(r'<b>(.*?)</b>', doc, re.S | re.I)
        title = re.sub(r'<[^>]+>', '', h.group(1)).strip() if h else path.stem.replace('_', ' ').replace('-', ' ')
        title = re.sub(r'\s+', ' ', title)[:120] or 'DoHistory'
        doc = re.sub(r'(<head[^>]*>)', r'\1<title>%s</title>' % title.replace('\\', '\\\\'), doc, count=1, flags=re.I)
    return re.sub(r'(<head[^>]*>)', lambda m: m.group(1) + extra, doc, count=1, flags=re.I)


def fix_lang(doc):
    m = re.search(r'<html(\s[^>]*)?>', doc, re.I)
    if not m:
        return '<html lang="en">\n' + doc + ('\n</html>\n' if not re.search(r'</html>', doc, re.I) else '')
    if re.search(r'\slang\s*=', m.group(0), re.I):
        return doc
    return doc[:m.start()] + set_attr(m.group(0), 'lang', 'en') + doc[m.end():]


def fix_skip(doc):
    if 'skip-link' in doc or re.search(r'<frameset', doc, re.I):
        return doc
    body = re.search(r'<body(\s[^>]*)?>', doc, re.I)
    nav = re.search(r'nav/nav_', doc)
    if not body or not nav:
        return doc
    end = TOPNAV_END.search(doc, nav.end())
    if end:
        at = end.end()
    else:
        t = re.search(r'</table>', doc[nav.end():], re.I)
        if not t:
            return doc
        at = nav.end() + t.end()
    doc = doc[:at] + '\n' + CONTENT_ANCHOR + doc[at:]
    return doc[:body.end()] + '\n' + SKIP_LINK + doc[body.end():]


def fix_selects(doc):
    for name in ('Month', 'Day', 'Year'):
        doc = re.sub(r'<select\s+name="%s"(?![^>]*aria-label)' % name, '<select name="%s" aria-label="%s"' % (name, name), doc)
    # 3.2.2: the jump menu navigated on change; a Go button makes it explicit
    doc = re.sub(r'<select\s+name="SelectMenu"\s+onChange="changeIt\(\)">(.*?)</select>',
                 r'<select name="SelectMenu" aria-label="Jump to">\1</select> <input type="button" value="Go" onclick="changeIt()">',
                 doc, flags=re.S | re.I)
    return doc


def fix_frames(doc):
    def repl(m):
        tag = m.group(0)
        if has_attr(tag, 'title'):
            return tag
        name = re.search(r'\sname="([^"]*)"', tag, re.I)
        src = re.search(r'\ssrc="([^"]*)"', tag, re.I)
        t = FRAME_TITLES.get(name.group(1).lower()) if name else None
        if not t and src:
            s = re.sub(r'\.html?$', '', src.group(1).rsplit('/', 1)[-1])
            t = re.sub(r'[_\-]+', ' ', s).strip().capitalize() or 'Frame'
        return set_attr(tag, 'title', t or 'Frame')
    return re.sub(r'<frame\b(?:[^>"]|"[^"]*")*>', repl, doc, flags=re.I)


def fix_links(doc):
    # book notes: <a name="noteN" href="#jumpN"><li></a> text -> <li id="noteN"> text
    doc = re.sub(r'<a\s+name="(note\d+)"\s+href="#jump\d+">\s*<li>\s*</a>', r'<li id="\1">', doc, flags=re.I)
    # empty named anchors with an href are focusable links that say nothing: keep the anchor, drop the href
    doc = re.sub(r'<a(\s[^>]*?)\shref="[^"]*"([^>]*\sname="[^"]*"[^>]*)>\s*</a>', r'<a\1\2></a>', doc, flags=re.I)
    doc = re.sub(r'<a(\s[^>]*\sname="[^"]*"[^>]*?)\shref="[^"]*"([^>]*)>\s*</a>', r'<a\1\2></a>', doc, flags=re.I)
    # line breaks at the start or end of a link belong outside it (they stretch the link over two lines)
    doc = re.sub(r'(<a\b[^>]*>)((?:<font[^>]*>|<b>|\s)*)(<br\s*/?>\s*)', r'\3\1\2', doc, flags=re.I)
    doc = re.sub(r'(<br\s*/?>\s*)((?:</font>|</b>|\s)*)</a>', r'</a>\1\2', doc, flags=re.I)
    # empty links with nothing inside (calendar leftovers, stray anchors)
    doc = re.sub(r'<a\s[^>]*href="[^"]*"[^>]*>(?:\s|<br\s*/?>|</?b>|<font[^>]*>|</font>)*</a>', '', doc, flags=re.I)
    return doc


def fix_lists(doc):
    # stray <br> / <p> / <b> </b> between list items
    doc = re.sub(r'(</li>|<ol[^>]*>|<ul[^>]*>)\s*(?:<br\s*/?>|<p>|<b>\s*</b>)\s*(?=<li|</ol>|</ul>)', r'\1\n', doc, flags=re.I)
    # a note's "return" link that spilled into the next notes list
    doc = re.sub(r'(<ol[^>]*>)\s*(<a href="#jump\d+">return</a>)\s*(?=<li)', r'\2 \1', doc, flags=re.I)
    # <dl><i>Term</i><dd> -> a proper <dt>
    doc = re.sub(r'(<dl>)\s*(<i>[^<]*</i>)\s*(?=<dd)', r'\1<dt>\2</dt>', doc, flags=re.I)
    # lists that are only indentation: no items inside
    while True:   # nested <ul><ul> indentation: innermost first
        new = re.sub(r'<ul>((?:(?!<ul|<li)[\s\S])*?)</ul>', r'<blockquote>\1</blockquote>', doc, flags=re.I)
        if new == doc:
            break
        doc = new
    def dl_fix(m):
        inner = m.group(1)
        if re.search(r'<dt', inner, re.I) and re.search(r'<dd', inner, re.I):
            return m.group(0)
        inner = re.sub(r'<dt>', '<p>', inner, flags=re.I); inner = re.sub(r'</dt>', '</p>', inner, flags=re.I)
        inner = re.sub(r'<dd>', '<div style="margin-left:40px">', inner, flags=re.I); inner = re.sub(r'</dd>', '</div>', inner, flags=re.I)
        return '<div>' + inner + '</div>'
    doc = re.sub(r'<dl>((?:(?!<dl)[\s\S])*?)</dl>', dl_fix, doc, flags=re.I)
    doc = re.sub(r'(</dd>|</dt>|<dl[^>]*>)\s*(?:<br\s*/?>\s*)+(?=<dt|<dd|</dl>)', r'\1\n', doc, flags=re.I)
    # <dt><dl>...</dl></dt>  ->  <dd><dl>...</dl></dd>
    doc = re.sub(r'<dt>\s*(<dl>.*?</dl>)\s*</dt>', r'<dd>\1</dd>', doc, flags=re.S | re.I)
    # <ol><ol> nested list without an item around it
    doc = re.sub(r'(<ol[^>]*>)\s*(<ol[^>]*>)', r'\1<li style="list-style:none">\2', doc, flags=re.I)
    doc = re.sub(r'</ol>\s*</ol>', '</ol></li></ol>', doc, flags=re.I)
    return doc


def fix_inputs(doc):
    def repl(m):
        tag = m.group(0)
        if has_attr(tag, 'aria-label') or re.search(r'type\s*=\s*"?(hidden|submit|reset|button|image)', tag, re.I):
            return tag
        ph = re.search(r'\splaceholder="([^"]+)"', tag, re.I)
        if ph:
            return set_attr(tag, 'aria-label', ph.group(1).rstrip('.'))
        if has_attr(tag, 'id'):
            return tag
        name = re.search(r'\sname\s*=\s*"?([^"\s>]+)', tag, re.I)
        if not name:
            return tag
        label = INPUT_LABELS.get(name.group(1).lower())
        if not label:
            val = re.search(r'\svalue\s*=\s*"?([^"\s>]+)', tag, re.I)
            label = (val.group(1) if val and re.search(r'type\s*=\s*"?(radio|checkbox)', tag, re.I) else name.group(1))
            label = re.sub(r'[_\-]+', ' ', label).strip().capitalize()
        return set_attr(tag, 'aria-label', label)
    return re.sub(r'<(?:input|textarea|select)\b(?:[^>"]|"[^"]*")*>', repl, doc, flags=re.I)


def fix_areas(doc):
    def repl(m):
        tag = m.group(0)
        if has_attr(tag, 'alt'):
            return tag
        href = re.search(r'\shref="([^"]*)"', tag, re.I)
        if not href:
            return set_attr(tag, 'alt', '')
        h = href.group(1).rsplit('/', 1)[-1]
        if re.fullmatch(r'[a-d][1-4]\.html', h):
            label = 'Map section %s' % h[:2].upper()
        elif re.fullmatch(r'detail(\d+)\.html', h):
            label = 'Map detail %s' % re.sub(r'\D', '', h)
        elif re.fullmatch(r'(left|right|top|bottom)\.html', h):
            label = '%s part of the map' % h[:-5].capitalize()
        else:
            label = re.sub(r'[_\-]+', ' ', re.sub(r'\.html?$', '', h)).strip('<>& ') or 'Link'
        return set_attr(tag, 'alt', label)
    return re.sub(r'<area\b(?:[^>"]|"[^"]*")*>', repl, doc, flags=re.I)


def fix_title_heading(doc):
    """The page-title graphic (images/xxx_title.gif) becomes the h1 for assistive tech. Scanned title pages
    of documents (071_title.jpg) are content, not headings."""
    doc = re.sub(r'<span role="heading" aria-level="1">(<img\b(?:[^>"]|"[^"]*")*>)</span>', r'\1', doc)
    nav = re.search(r'nav/nav_', doc)
    start = nav.end() if nav else 0
    m = re.search(r'<img\b(?:[^>"]|"[^"]*")*?src="[^"]*/(?!\d)[^"/]*(?:[tT]itle|_subhead)\.gif"(?:[^>"]|"[^"]*")*\salt="[^"]+"(?:[^>"]|"[^"]*")*>', doc[start:])
    if not m:
        return doc
    at = start + m.start()
    before = doc[:at]
    if before.count('<a ') + before.count('<A ') > before.count('</a>') + before.count('</A>'):
        return doc     # inside a link; leave it
    return before + '<span role="heading" aria-level="1">' + m.group(0) + '</span>' + doc[start + m.end():]


def fix_charset(doc, raw):
    if re.search(rb'[\x80-\xff]', raw) and not re.search(r'charset=', doc, re.I):
        doc = re.sub(r'(<head[^>]*>)', r'\1<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">', doc, count=1, flags=re.I)
    return doc


def process(path, learned):
    raw = path.read_bytes()
    doc = raw.decode(ENC)
    out = doc
    out = fix_lang(out)
    out = fix_head(out, path)
    out = fix_charset(out, raw)
    out = fix_skip(out)
    out = fix_images(out, path, learned)
    out = fix_selects(out)
    out = fix_frames(out)
    out = fix_links(out)
    out = fix_lists(out)
    out = fix_inputs(out)
    out = fix_areas(out)
    out = fix_title_heading(out)
    if out != doc and not DRY:
        path.write_bytes(out.encode(ENC))
    return out != doc


def main():
    learned = learn_alts()
    changed = 0
    for p in sorted(ROOT.rglob('*.html')):
        changed += process(p, learned)
    print('changed %d pages%s' % (changed, ' (dry run)' if DRY else ''))


if __name__ == '__main__':
    main()
