#!/usr/bin/env python3
"""Static-search + WCAG 2.2 AA + archive-chrome retrofit for the 20.rrchnm.org mirror.

Idempotent: every transformation is guarded, so running this twice is a no-op
and `git diff` after a second run must be empty. Operates on every *.html file
in the archive except the hand-authored search pages.

The mirror carries two Omeka themes -- Berlin (726 pages) and neatscape (31,
the history-matters and the-lost-museum exhibits). They differ enough in
structure that most transforms are theme-aware; a `.theme-berlin` /
`.theme-neatscape` marker class on <body> lets one stylesheet serve both.

Search (Pagefind)
  - point the site-wide search form at /search.html instead of the dead
    https://20.rrchnm.org/search Omeka endpoint, and drop the query-type and
    record-type controls Pagefind has no equivalent for
  - mark the ~499 canonical content pages with data-pagefind-body and pin each
    result title from the page <title>
  - expose Collection and Item Type as Pagefind filters on item pages
  - repoint the dead "People" nav link at the faceted search, pre-filtered

WCAG 2.2 AA
  1.1.1  name the 81 unnamed PDF <object> embeds and give them a download
         fallback (alt text on <img> is deliberately out of scope)
  1.3.1  <main>, named landmarks, real <label>s, heading order, table headers
  1.4.3  contrast (in themes/a11y.css)
  1.4.4  drop maximum-scale/minimum-scale from the viewport meta
  1.4.10 reflow (in themes/a11y.css)
  2.1.1  the mobile menu opener becomes a <button> (in globals.js); the
         desktop submenu gains :focus-within (in themes/a11y.css)
  2.4.1  a skip link, which no page had
  2.4.2  disambiguate the 125 pages sharing a <title>
  2.4.7  focus indicator (in themes/a11y.css)
  2.5.8  target size (in themes/a11y.css)
  4.1.1  duplicate/empty ids, an unclosed <span>, a heading inside <p>

Chrome / robustness
  - RRCHNM archive notice banner (ported from the thanksroy archive)
  - GMU Department of History and Art History logo replaces the "Proudly
    powered by Omeka" footer credit
  - one modern Matomo block per page, including the 31 that had none
  - self-hosted jQuery/jQuery UI and Crimson Text/Cabin instead of CDN links
  - files/ media references relativized to /files/ for the object bucket
  - dead sort links and RSS/Atom feed links removed

Run tools/harvest.py first; this script refuses to start without the KML and
timeline JSON it depends on, rather than emitting dead links.

    python3 tools/retrofit.py [--check]
"""
import html as htmllib
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = "https://20.rrchnm.org"

# Hand-authored; they already carry the final chrome. Skipped wholesale, as are
# the redirect stubs tools/make_search_pages.py writes over the 63 dead
# items/search?... captures -- they carry no theme stylesheet, so the chrome
# this script adds (a skip link that relies on .visually-hidden, a banner)
# would render as loose visible text on a page the visitor never sees.
AUTHORED = {"search.html", os.path.join("items", "search.html")}
STUB_RE = re.compile(r"^items/search\?.*\.html$")


def is_skipped(rel):
    rel = rel.replace(os.sep, "/")
    return rel in {x.replace(os.sep, "/") for x in AUTHORED} or bool(
        STUB_RE.match(rel))

STATS = Counter()


def bump(key, n=1):
    STATS[key] += n


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def html_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", ".crawl", "pagefind", "tools",
                                    "data")]
        for name in filenames:
            if name.endswith(".html"):
                out.append(os.path.relpath(os.path.join(dirpath, name), ROOT))
    return sorted(out)


def depth_prefix(rel):
    """'' for a root page, '../' one level down, '../../' two."""
    return "../" * (len(rel.replace(os.sep, "/").split("/")) - 1)


def is_neatscape(s):
    return "themes/neatscape/css/style.css" in s


def retag_div(s, ident, new_open, close_tag="</nav>"):
    """Replace <div id="ident">...</div> with new_open...close_tag.

    Finds the CLOSING tag by counting nesting rather than with a non-greedy
    regex. #exhibit-page-navigation wraps three sibling <div>s, so `.*?</div>`
    matches the first inner close and produces unbalanced markup.
    """
    open_str = f'<div id="{ident}">'
    i = s.find(open_str)
    if i < 0:
        return s, 0
    open_re, close_re = re.compile(r"<div\b", re.I), re.compile(r"</div\s*>", re.I)
    depth, j, end = 0, i, None
    while j < len(s):
        mo, mc = open_re.search(s, j), close_re.search(s, j)
        if not mc:
            break
        if mo and mo.start() < mc.start():
            depth += 1
            j = mo.end()
        else:
            depth -= 1
            j = mc.end()
            if depth == 0:
                end = mc
                break
    if end is None:
        return s, 0
    return (s[:i] + new_open + s[i + len(open_str):end.start()]
            + close_tag + s[end.end():], 1)


# Canonical content pages -- the ones worth indexing. Everything else is either
# chrome, a wget duplicate of another route (items.html vs items/browse.html),
# a paginated listing, or an exhibit-scoped restatement of an item page.
_ITEM = re.compile(r"^items/show/\d+\.html$")
_COLLECTION = re.compile(r"^collections/show/\d+\.html$")
_EXHIBIT = re.compile(r"^exhibits/show/.+\.html$")
_EXHIBIT_ITEM = re.compile(r"^exhibits/show/.+/item/\d+\.html$")
_SIMPLE = {"index.html", "about.html", "about-this-site.html",
           "files/show/909.html", "neatline-time/timelines/show/1.html"}


def is_content_page(rel):
    rel = rel.replace(os.sep, "/")
    if rel in _SIMPLE:
        return True
    if _ITEM.match(rel) or _COLLECTION.match(rel):
        return True
    if _EXHIBIT.match(rel) and not _EXHIBIT_ITEM.match(rel):
        return True
    return False


# ---------------------------------------------------------------------------
# <head>
# ---------------------------------------------------------------------------

def fix_viewport(s):
    """1.4.4 Resize Text: maximum-scale=1.0 blocks pinch-zoom.

    The trailing user-scalable=yes does not rescue it. neatscape's meta is
    already clean, so only the 726 Berlin pages match.
    """
    old = ('<meta name="viewport" content="width=device-width, '
           'initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, '
           'user-scalable=yes" />')
    new = '<meta name="viewport" content="width=device-width, initial-scale=1" />'
    if old in s:
        s = s.replace(old, new)
        bump("viewport")
    return s


def add_a11y_css(s, prefix):
    """Load themes/a11y.css last, immediately after the theme stylesheet."""
    if "themes/a11y.css" in s:
        return s
    theme = "neatscape" if is_neatscape(s) else "Berlin"
    pat = re.compile(
        r'(<link href="[^"]*themes/' + theme +
        r'/css/style\.css%3Fv=3\.0\.1\.css"[^>]*>)')
    m = pat.search(s)
    if not m:
        return s
    link = (f'\n<link href="{prefix}themes/a11y.css" media="all" '
            f'rel="stylesheet" type="text/css" >')
    bump("a11y_css")
    return s[:m.end()] + link + s[m.end():]


def selfhost_jquery(s, prefix):
    """Serve jQuery and jQuery UI from the archive instead of ajax.googleapis.com.

    The mirror's own document.write fallbacks pointed at
    /application/views/scripts/javascripts/vendor/jquery.js?v=3.0.1, which was
    never downloaded -- so with the CDN unreachable there was no jQuery at all,
    and the drop-down nav, the advanced-search disclosure and every map died.
    Those files exist now; with the primary tags served locally the fallbacks
    are redundant, so they go too.
    """
    if "ajax.googleapis.com" not in s:
        return s
    vendor = prefix + "application/views/scripts/javascripts/vendor/"
    s = s.replace(
        '<script type="text/javascript" src="https://ajax.googleapis.com/ajax/'
        'libs/jquery/3.6.0/jquery.min.js"></script>',
        f'<script type="text/javascript" src="{vendor}jquery.js"></script>')
    s = s.replace(
        '<script type="text/javascript" src="https://ajax.googleapis.com/ajax/'
        'libs/jqueryui/1.12.1/jquery-ui.min.js"></script>',
        f'<script type="text/javascript" src="{vendor}jquery-ui.js"></script>')
    # The two now-pointless document.write fallbacks.
    s = re.sub(r'<script type="text/javascript">\s*//<!--\s*'
               r'window\.jQuery(?:\.ui)? \|\| document\.write\([^\n]*\)\s*'
               r'//-->\s*</script>\s*', "", s)
    bump("jquery_selfhosted")
    return s


def selfhost_fonts(s, prefix):
    """The 31 neatscape pages linked Google Fonts over plain http://.

    An HTTPS host blocks that as mixed content, so these pages have been
    rendering in fallback faces already. Both families are OFL; they are
    committed under themes/neatscape/fonts/.
    """
    pat = re.compile(r'<link href="http://fonts\.googleapis\.com/css\?'
                     r'family=[^"]*"[^>]*>')
    if not pat.search(s):
        return s
    s = pat.sub(f'<link href="{prefix}themes/neatscape/css/fonts.css" '
                f'media="all" rel="stylesheet" type="text/css" >', s)
    bump("fonts_selfhosted")
    return s


def drop_feed_links(s):
    """The RSS/Atom <link rel="alternate"> point at the retiring origin."""
    pat = re.compile(r'<link rel="alternate" type="application/(?:rss\+xml|'
                     r'atom\+xml)" title="Omeka (?:RSS|Atom) Feed" '
                     r'href="[^"]*" />')
    s, n = pat.subn("", s)
    if n:
        bump("feed_links", n)
    return s


def drop_ie_conditionals(s):
    """Three IE6-8 conditional scripts whose assets were never mirrored."""
    pat = re.compile(r'<!--\[if [^\]]*IE [^\]]*\]>\s*<script[^>]*>\s*</script>'
                     r'\s*<!\[endif\]-->\s*')
    s, n = pat.subn("", s)
    if n:
        bump("ie_conditionals", n)
    return s


_MATOMO_RE = re.compile(r"<!-- Matomo -->.*?<!-- End Matomo Code -->\s*",
                        re.DOTALL)

_MATOMO_SNIPPET = """<!-- Matomo -->
<script>
  var _paq = window._paq = window._paq || [];
  /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="https://stats.rrchnm.org/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '80']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Matomo Code -->
"""


def normalize_matomo(s):
    """One identical modern Matomo block per page, last in <head>.

    726 pages carried the older Omeka-emitted variant (type="text/javascript",
    g.type=); the 31 neatscape pages carried no analytics at all. Strip and
    reinsert so all 757 end up the same, and so wording changes propagate.
    """
    had = bool(_MATOMO_RE.search(s))
    s = _MATOMO_RE.sub("", s)
    if "</head>" not in s:
        return s
    s = s.replace("</head>", _MATOMO_SNIPPET + "</head>", 1)
    bump("matomo_normalized" if had else "matomo_added")
    return s


# ---------------------------------------------------------------------------
# <body>: landmarks, skip link, banner
# ---------------------------------------------------------------------------

def add_theme_class(s):
    """A marker class so one stylesheet can serve both themes.

    The natural discriminators are unusable: neatscape's html class="no-js" is
    rewritten by Modernizr at runtime, and div[role=main] is the very selector
    the neatscape rules exist to protect.
    """
    theme = "theme-neatscape" if is_neatscape(s) else "theme-berlin"
    m = re.search(r'<body([^>]*)>', s)
    if not m or theme in m.group(1):
        return s
    attrs = m.group(1)
    if 'class="' in attrs:
        new = attrs.replace('class="', f'class="{theme} ', 1)
    else:
        new = f' class="{theme}"' + attrs
    bump("theme_class")
    return s[:m.start()] + f"<body{new}>" + s[m.end():]


SKIPNAV = '<a href="#content" id="skipnav">Skip to main content</a>\n'

BANNER = '''    <aside class="notice" aria-label="Archive notice" style="font-size: 12px; \
display: flex; align-items: center; background-color: #f8f8f8; padding: 10px; \
border: 1px solid #ddd; margin-bottom: 0;">
    <a class="notice-logo" href="https://rrchnm.org" target="_blank" rel="noopener"><img \
src="/assets/rrchnm-mark.png" width="124" height="120" \
alt="RRCHNM Logo" style="height: 30px; width: auto; margin-right: 15px;"/></a>
    <div>
    This is a static copy of the final website maintained by the \
<a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig \
Center for History and New Media</a>.
    </div>
</aside>
'''
BANNER_RE = re.compile(r'    <aside class="notice".*?</aside>\n', re.S)


def add_skipnav_and_banner(s):
    """2.4.1 Bypass Blocks, plus the archive notice.

    The banner is stripped and reinserted rather than guarded, so changes to
    its markup reach pages that already carry it. The strip pattern removes
    exactly what BANNER adds.
    """
    m = re.search(r'(<body[^>]*>)\n?', s)
    if not m:
        return s
    had_banner = bool(BANNER_RE.search(s))
    s = BANNER_RE.sub("", s, count=1)
    if SKIPNAV not in s:
        m = re.search(r'(<body[^>]*>)\n?', s)
        s = s[:m.end()] + SKIPNAV + s[m.end():]
        bump("skipnav")
    # Always (re)insert the banner directly after the skip link.
    i = s.index(SKIPNAV) + len(SKIPNAV)
    s = s[:i] + BANNER + s[i:]
    bump("banner_refreshed" if had_banner else "banner")
    return s


def fix_main_landmark(s, index_page):
    """1.3.1: Berlin had no main landmark at all; neatscape's needed a name.

    Berlin's <div id="content"> becomes <main id="content">: every #content
    rule in style.css is id-based, so nothing moves.

    neatscape's <div role="main"> KEEPS its role. That theme styles the
    landmark through attribute selectors -- div[role=main] drives the clearfix
    (:462), the padding (:1015), the h1:first-child sizing (:567) and the
    wide-viewport gutters (:1358) -- so converting it to <main> would silently
    delete four rules. This is a deliberate departure from the thanksroy
    precedent, which does strip the roles.
    """
    if is_neatscape(s):
        if '<div role="main">' in s:
            s = s.replace('<div role="main">',
                          '<div role="main" id="content" tabindex="-1">', 1)
            bump("main_neatscape")
        return s
    if '<div id="content">' in s:
        s = s.replace('<div id="content">',
                      '<main id="content" tabindex="-1">', 1)
        s = s.replace("</div><!-- end content -->",
                      "</main><!-- end content -->", 1)
        bump("main_berlin")
    return s


def name_landmarks(s):
    """1.3.1: turn the nav <div>s into landmarks and give every nav a name.

    A page carries up to six navigations. Unnamed, they are announced
    identically; two of them were not landmarks at all.
    """
    # #primary-nav / #mobile-nav are <div>s. The inner submenu </ul>s are
    # followed by </li>, so the non-greedy match ends at the right one.
    def to_nav(m):
        ident, inner, ws = m.group(1), m.group(2), m.group(3)
        label = "Main" if ident == "primary-nav" else "Main (mobile)"
        if ident == "mobile-nav":
            inner = inner.replace('<ul class="navigation">',
                                  '<ul class="navigation" id="mobile-nav-list">', 1)
        return f'<nav id="{ident}" aria-label="{label}">{inner}</ul>{ws}</nav>'

    s, n = re.subn(r'<div id="(primary-nav|mobile-nav)">(.*?)</ul>(\s*)</div>',
                   to_nav, s, flags=re.S)
    if n:
        bump("nav_landmarks", n)

    for old, new in [
        # Berlin footer
        ('<nav><ul class="navigation">',
         '<nav aria-label="Footer"><ul class="navigation">'),
        # neatscape header / footer
        ('<nav id="top-nav">', '<nav id="top-nav" aria-label="Main">'),
        ('<nav role="navigation">',
         '<nav role="navigation" aria-label="Footer">'),
        # secondary strips
        ('<nav class="items-nav navigation secondary-nav">',
         '<nav class="items-nav navigation secondary-nav" aria-label="Items">'),
        ('<nav class="navigation items-nav secondary-nav">',
         '<nav class="navigation items-nav secondary-nav" aria-label="Items">'),
        ('<nav class="navigation secondary-nav">',
         '<nav class="navigation secondary-nav" aria-label="Exhibits">'),
        ('<nav class="navigation exhibit-tags" id="secondary-nav">',
         '<nav class="navigation exhibit-tags" id="secondary-nav" aria-label="Exhibits">'),
        ('<nav id="exhibit-pages">',
         '<nav id="exhibit-pages" aria-label="Exhibit pages">'),
        ('<nav class="item-pagination">',
         '<nav class="item-pagination" aria-label="Item">'),
    ]:
        if old in s:
            s = s.replace(old, new)
            bump("nav_named")

    # Not a landmark today; all its CSS is id-based, so the swap is safe. Its
    # three sibling <div>s are why this needs the balanced matcher.
    s, n = retag_div(s, "exhibit-page-navigation",
                     '<nav id="exhibit-page-navigation" aria-label="Exhibit page">')
    if n:
        bump("nav_named", n)

    # Berlin's item prev/next list is in no <nav> at all.
    ITEM_PAG = '<ul class="item-pagination navigation">'
    if ITEM_PAG in s and f'<nav aria-label="Item">{ITEM_PAG}' not in s:
        s = re.sub(r'(<ul class="item-pagination navigation">.*?</ul>)',
                   r'<nav aria-label="Item">\1</nav>', s, count=1, flags=re.S)
        bump("item_pagination_nav")

    # Browse pages carry two <nav aria-label="Pagination">; distinguish them.
    parts = s.split('<nav class="pagination-nav" aria-label="Pagination">')
    if len(parts) == 3:
        s = (parts[0] + '<nav class="pagination-nav" aria-label="Pagination">'
             + parts[1]
             + '<nav class="pagination-nav" aria-label="Pagination (bottom)">'
             + parts[2])
        bump("pagination_nav_named")
    return s


# ---------------------------------------------------------------------------
# footer
# ---------------------------------------------------------------------------

FOOTER_OMEKA = ('<p>Proudly powered by <a href="http://omeka.org">Omeka</a>.</p>')
FOOTER_LOGO = ('<p class="histarthist-logo">'
               '<a href="https://historyarthistory.gmu.edu/">'
               '<img src="/assets/histarthist-logo.png" width="300" height="84" '
               'alt="George Mason University Department of History and Art History" />'
               '</a></p>')


def replace_footer_credit(s):
    """The visible Omeka credit only.

    The COinS citation metadata (info:sid/omeka.org:generator), the About-page
    prose and archived item content that mention Omeka are left untouched.
    """
    if FOOTER_OMEKA in s:
        s = s.replace(FOOTER_OMEKA, FOOTER_LOGO)
        bump("footer_logo")
    return s


# ---------------------------------------------------------------------------
# search form
# ---------------------------------------------------------------------------

def fix_search_form(s):
    """Point the header form at Pagefind and give its input a real label."""
    if f'action="{ORIGIN}/search"' not in s:
        return s
    s = s.replace(f'action="{ORIGIN}/search" method="get">',
                  'action="/search.html" method="get">')
    # 3.3.2: the input was named only by aria-labelledby pointing at the submit
    # BUTTON, so field and button announced identically and there was no
    # visible label.
    s = s.replace(
        '<input type="text" name="query" id="query" value="" title="Search" '
        'aria-labelledby="submit_search">',
        '<label for="query" class="visually-hidden">Search this site</label>'
        '<input type="text" name="query" id="query" value="" placeholder="Search">')
    # Berlin's form lacks the search landmark neatscape's has.
    s = s.replace('<form id="search-form" name="search-form" action="/search.html"',
                  '<form id="search-form" name="search-form" role="search" '
                  'action="/search.html"')
    # Keyword/boolean/exact-match and Item/File/Collection are Omeka query modes
    # Pagefind has no equivalent for. Drop the fieldsets but keep #advanced-form:
    # Omeka's showAdvancedForm() keys off it to inject the disclosure toggle.
    s = re.sub(r'<fieldset id="query-types">.*?</fieldset>\s*', "", s, flags=re.S)
    s = re.sub(r'<fieldset id="record-types">.*?</fieldset>\s*', "", s, flags=re.S)
    # 4.1.1: the neatscape variant emits three hidden inputs all id="record_types".
    s = re.sub(r'(<input type="hidden" name="record_types\[\]" value="[^"]*") '
               r'id="record_types"', r"\1", s)
    # wget rewrote this link against whatever items/search capture it resolved
    # to, so it has many forms across the archive. Normalize them all.
    s = re.sub(r'<p><a href="[^"]*">Advanced Search \(Items only\)</a></p>',
               '<p><a href="/items/search.html">Advanced Search (Items only)</a></p>', s)
    bump("search_form")
    return s


def fix_pagination_form(s):
    """3.3.2: the "jump to page" form had no submit button -- Enter only.

    The action also submits a query string the static server ignores, so it
    silently served page 1; themes/page-jump.js maps the number to the wget
    filename instead. The button is the no-JS floor, not the whole fix.
    """
    old = ' title="Current Page" value="'
    if old in s:
        s = s.replace(old, ' value="')
        bump("pagination_title")
    pat = re.compile(r'(<label>Page<input type="text" name="page" value="[^"]*">'
                     r'</label> of \d+)(\s*</form>)')
    if pat.search(s) and "pagination-go" not in s:
        s = pat.sub(r'\1 <button type="submit" class="button pagination-go">Go'
                    r'</button>\2', s)
        bump("pagination_go")
    return s


def add_page_jump(s, prefix):
    """Load the shim that makes the page box navigate to the right file."""
    if "pagination-go" not in s or "themes/page-jump.js" in s:
        return s
    tag = f'<script src="{prefix}themes/page-jump.js"></script>\n'
    if "</body>" not in s:
        return s
    bump("page_jump")
    return s.replace("</body>", tag + "</body>", 1)


def drop_sort_links(s):
    """The three sort links per browse page are dead: the crawl excluded every
    ?sort_field= URL, and a static server cannot re-sort anyway. Removing the
    block also removes three <span aria-label> on empty generic elements, which
    axe flags as aria-prohibited-attr (4.1.2)."""
    pat = re.compile(r'\s*<div id="sort-links">.*?</div>\s*', re.S)
    s, n = pat.subn("\n\n", s)
    if n:
        bump("sort_links_removed", n)
    return s


def drop_output_formats(s):
    """Omeka's "Output Formats" row offers atom / dcmes-xml / json / omeka-xml /
    rss2 for the current listing. All five are absolute origin URLs that the
    crawl excluded by its `*output=*` reject pattern, so all 560 of them (5 on
    each of 112 pages) 404 today and will not resolve at all once the origin is
    retired. A static server cannot generate them. Same treatment as the sort
    links: remove the affordance rather than ship dead links."""
    pat = re.compile(r'\s*<div id="outputs">.*?</div>\s*', re.S)
    s, n = pat.subn("\n", s)
    # The neatscape item pages carry the same list in a different wrapper.
    pat2 = re.compile(r'\s*<div id="item-output-formats" class="element">'
                      r'.*?</ul>\s*</div>\s*</div>\s*', re.S)
    s, n2 = pat2.subn("\n", s)
    if n + n2:
        bump("output_formats_removed", n + n2)
    return s


def fix_mangled_mall_link(s):
    """The crawl's only 404, and it was mangled before the crawl ever ran.

    exhibits/show/histories-of-the-national-mall/legacy.html says the project
    "is still online today at mallhistories.org" over an href that Omeka
    resolved as a relative path, producing
    https://20.rrchnm.org/exhibits/show/histories-of-the-national-mall/mallhistories.org
    -- the single failure recorded in this archive's README. The project is
    live at mallhistory.org (mallhistories.org does not resolve), and is itself
    a sibling archive in this repository.
    """
    old = ('href="https://20.rrchnm.org/exhibits/show/'
           'histories-of-the-national-mall/mallhistories.org"')
    if old in s:
        s = s.replace(old, 'href="https://mallhistory.org/"')
        bump("mall_link_fixed")
    return s


PEOPLE_HREF = re.compile(
    r'href="' + re.escape(ORIGIN) + r'/items/browse\?search=[^"]*?type=12[^"]*"')


def fix_people_link(s):
    """The People nav entry was a raw advanced-search URL the crawl excluded --
    a 404 in the header, the mobile nav and the footer of every page. Pagefind's
    faceted page answers exactly that query."""
    s, n = PEOPLE_HREF.subn('href="/items/search.html?filter=Item+Type:Person"', s)
    if n:
        bump("people_link", n)
    return s


# ---------------------------------------------------------------------------
# headings and structure
# ---------------------------------------------------------------------------

def fix_headings(s, rel):
    """1.3.1 / 2.4.6: no page may skip a heading level or carry two h1."""
    # index.html opened with <p><h2>...</h2></p>: no h1 at all, and invalid
    # nesting. themes/a11y.css pins the size so nothing moves visually.
    if rel == "index.html":
        m = re.search(r'<p><h2>(.*?)</h2></p>', s, re.S)
        if m:
            s = s[:m.start()] + f"<h1>{m.group(1)}</h1>" + s[m.end():]
            bump("home_h1")

    # neatscape put the site title in an h1, so every one of its pages had two.
    s, n = re.subn(r'<h1 id="site-title">(.*?)</h1>',
                   r'<p id="site-title">\1</p>', s, count=1, flags=re.S)
    if n:
        bump("site_title_demoted")

    # <nav id="exhibit-pages"> led with an h4 under the page h1.
    m = re.search(r'(<nav id="exhibit-pages"[^>]*>\s*)<h4>(.*?)</h4>', s, re.S)
    if m:
        s = s[:m.start()] + m.group(1) + f"<h2>{m.group(2)}</h2>" + s[m.end():]
        bump("exhibit_pages_h2")

    # Item pages: Files / Citation / Collection were siblings of the h2
    # element-sets but a level deeper.
    for pat, repl, key in [
        (r'<h3>Files</h3>', '<h2>Files</h2>', "item_files_h2"),
        (r'(<div id="item-citation" class="element">\s*)<h3>Citation</h3>',
         r'\1<h2>Citation</h2>', "item_citation_h2"),
        (r'(<div id="collection" class="element">\s*)<h3>Collection</h3>',
         r'\1<h2>Collection</h2>', "item_collection_h2"),
    ]:
        s, n = re.subn(pat, repl, s)
        if n:
            bump(key, n)

    # Browse listings: item titles were h3 directly under the page h1. One
    # regex, open and close together, so a partial match can never leave
    # <h2>...</h3> behind. Every one of the 1,109 link texts is plain text.
    s, n = re.subn(r'<h3>(<a href="[^"]*" class="permalink">[^<]*</a>)</h3>',
                   r"<h2>\1</h2>", s)
    if n:
        bump("browse_h2", n)

    # 4.1.1: <h1><span class="exhibit-page">X</h1> -- the span is never closed.
    s, n = re.subn(r'(<h1><span class="exhibit-page">[^<]*)</h1>',
                   r"\1</span></h1>", s)
    if n:
        bump("exhibit_span_closed", n)
    return s


def fix_about_page(s, rel):
    """4.1.1: about.html wraps block-level records in <p>."""
    if rel != "about.html":
        return s
    s, n = re.subn(r'<p>(<div class="item record">)', r"\1", s)
    if n:
        s = re.sub(r'(</div>)\s*</p>', r"\1", s)
        bump("about_p_unwrapped", n)
    s, m = re.subn(r'<h3>(<a href="[^"]*">[^<]*</a>)</h3>', r"<h2>\1</h2>", s)
    if m:
        bump("about_h2", m)
    return s


def fix_titles(s, rel):
    """2.4.2: 113 pages are titled "Browse Items", 9 "Browse Exhibits", 3
    "Browse Items on the Map". Read the page number off the page's own
    pagination form so each title says which page it is."""
    m = re.search(r'<title>(.*?)</title>', s, re.S)
    if not m or "(page " in m.group(1):
        return s
    p = re.search(r'<label>Page<input type="text" name="page" value="(\d+)">'
                  r'</label> of (\d+)', s)
    if not p or p.group(2) == "1":
        return s
    title = m.group(1)
    sep = " &middot; " if " &middot; " in title else None
    if sep:
        head, _, tail = title.partition(sep)
        new = f"{head} (page {p.group(1)} of {p.group(2)}){sep}{tail}"
    else:
        new = f"{title} (page {p.group(1)} of {p.group(2)})"
    bump("title_paginated")
    return s[:m.start(1)] + new + s[m.end(1):]


def fix_relations_table(s):
    """1.3.1: the Item Relations tables carry no <th> and no caption."""
    pat = re.compile(r'<table>(\s*<tr>\s*<td>This Item</td>)')
    if not pat.search(s):
        return s
    head = ('<table>\n<caption class="visually-hidden">Item relations</caption>\n'
            '<thead><tr><th scope="col">Subject</th>'
            '<th scope="col">Relationship</th>'
            '<th scope="col">Related item</th></tr></thead>')
    s, n = pat.subn(lambda m: head + m.group(1), s)
    bump("relations_table", n)
    return s


def fix_pdf_objects(s):
    """1.1.1 / 4.1.2: 81 pages embed <object type="application/pdf"> with no
    accessible name and no fallback content, so a screen reader meets an
    unlabelled frame and a no-plugin browser meets nothing at all."""
    m = re.search(r'<h1>(.*?)</h1>', s, re.S)
    title = htmllib.escape(htmllib.unescape(re.sub(r"<[^>]+>", "", m.group(1))
                                            .strip()), quote=True) if m else "Document"

    def one(mo):
        url = mo.group(1)
        return (f'<object data="{url}" type="application/pdf" '
                f'title="{title} (PDF)" style="width: 100%; height: 500px">'
                f'<p><a class="download-file" href="{url}">'
                f'Download &ldquo;{title}&rdquo; (PDF)</a></p></object>')

    pat = re.compile(r'<object data="([^"]*)" type="application/pdf" '
                     r'style="width: 100%; height: 500px"></object>')
    s, n = pat.subn(one, s)
    if n:
        bump("pdf_object_named", n)
    return s


def fix_map_style(s):
    """4.1.1: Omeka emits style="width: ; height: 300px" -- an empty value."""
    s, n = re.subn(r'style="width: ; height: 300px"', 'style="height: 300px"', s)
    if n:
        bump("map_style", n)
    return s


def drop_duplicate_collection_id(s):
    """4.1.1: the hidden collection input is emitted in BOTH pagination forms,
    so every collection-filtered browse page carries id="collection" twice.
    Nothing references the id."""
    pat = re.compile(r'(<input type="hidden" name="collection"[^>]*?) '
                     r'id="collection"(>)')
    if len(pat.findall(s)) > 1:
        s, n = pat.subn(r"\1\2", s)
        bump("dup_collection_id", n)
    return s


# ---------------------------------------------------------------------------
# media, maps
# ---------------------------------------------------------------------------

def relativize_media(s):
    """Rewrite every files/ reference to root-relative /files/....

    The four Omeka derivative directories were excluded at crawl time and now
    live in the object-storage bucket, which the web server serves at /files/.
    theme_uploads is committed in-repo and served from there, but the same
    root-relative form is correct for it too.
    """
    n0 = s.count(f"{ORIGIN}/files/")
    s = s.replace(f"{ORIGIN}/files/", "/files/")
    s = re.sub(r'(?<=["\'])(?:\.\./)+files/', "/files/", s)
    s = re.sub(r'(?<=["\'])files/', "/files/", s)
    if n0:
        bump("media_relativized", n0)
    return s


def fix_timeline_page(s, rel):
    """Render the "Projects" timeline statically.

    The page shipped an empty <div> filled at runtime by SIMILE Timeline, from
    an endpoint the crawl never followed. Both are gone: the renderer is
    http://api.simile-widgets.org (dead, and blocked as mixed content from an
    HTTPS host), and the data lived only on the origin. tools/harvest.py pulls
    the data while the origin is still up; this renders it as an ordered list,
    which needs no JavaScript and is indexable.
    """
    if rel.replace(os.sep, "/") != "neatline-time/timelines/show/1.html":
        return s
    if 'id="static-timeline"' in s:
        return s
    with open(os.path.join(ROOT, "data/neatline-timeline-1.json"),
              encoding="utf-8") as fh:
        events = json.load(fh).get("events", [])
    events.sort(key=lambda e: e.get("start") or "")

    rows = []
    for e in events:
        start = (e.get("start") or "")[:10]
        title = htmllib.escape(htmllib.unescape(e.get("title") or "Untitled"))
        link = e.get("link") or ""
        img = e.get("image") or ""
        desc = (e.get("description") or "").strip()
        thumb = (f'<span class="timeline-thumb"><img src="{img}" alt="" '
                 f'width="96" /></span>') if img else ""
        head = (f'<a href="{link}">{title}</a>') if link else title
        rows.append(
            f'  <li>{thumb}<h2>{head}</h2>'
            f'<span class="timeline-date">{start}</span>'
            + (f"<p>{desc}</p>" if desc else "")
            + "</li>")

    block = ('<ol id="static-timeline">\n' + "\n".join(rows) + "\n</ol>\n")
    # Drop the container and its loader, and the dead SIMILE script tags.
    s = re.sub(r'<!-- Construct the timeline\. -->.*?</script>\s*',
               block, s, count=1, flags=re.S)
    s = re.sub(r'<script[^>]*src="[^"]*simile-widgets[^"]*"[^>]*></script>\s*',
               "", s)
    s = re.sub(r'<script[^>]*src="[^"]*neatline-time-scripts\.js"[^>]*></script>\s*',
               "", s)
    s = re.sub(r'<script type="text/javascript">\s*//<!--\s*SimileAjax.*?</script>\s*',
               "", s, flags=re.S)
    bump("timeline_static", len(events))
    return s


KNIGHTLAB_NOTE = (
    '<div class="missing-embed">\n'
    '<p>This exhibit was built around an interactive timeline hosted by '
    'KnightLab, drawing on a Google spreadsheet. Neither survives: the '
    'spreadsheet has been deleted, and no copy was captured by the Internet '
    'Archive. The material it presented is preserved in the sections listed '
    'below.</p>\n'
    '</div>')


def fix_knightlab(s):
    """The TimelineJS embed cannot be revived.

    Its source spreadsheet returns 410 Gone and the Internet Archive holds no
    capture of the sheet, its feed, or the rendered embed. The iframe was also
    plain http:// inside an https:// page, so browsers were already blocking
    it -- what a visitor saw was a 650px empty box under a heading.
    """
    pat = re.compile(r'<p><iframe src="https?://cdn\.knightlab\.com[^"]*"[^>]*>'
                     r'</iframe></p>')
    s, n = pat.subn(KNIGHTLAB_NOTE, s)
    if n:
        bump("knightlab_note", n)
    return s


DRIVE_NOTE = ('<p class="missing-image">Image no longer available.</p>')


def fix_drive_image(s):
    """One hot-linked Google Drive thumbnail, repeated across 9 exhibit pages.

    Drive now answers the URL with a sign-in page rather than the image, the
    uc?export=view form 404s, and the Internet Archive has no snapshot. It
    carried alt="", so nothing is lost semantically; the note marks the gap
    rather than leaving a broken-image icon.
    """
    pat = re.compile(r'<img[^>]*src="https://drive\.google\.com/thumbnail\?'
                     r'[^"]*"[^>]*>')
    s, n = pat.subn(DRIVE_NOTE, s)
    if n:
        bump("drive_image_note", n)
    return s


def fix_map_pages(s, rel):
    """The browse map now has one KML with all 55 markers, so its 2-page
    pagination is meaningless -- and page 2 would have shown 5."""
    if not re.match(r"^items/map", rel.replace(os.sep, "/")):
        return s
    s, n = re.subn(r'\s*<nav class="pagination-nav" aria-label="Pagination'
                   r'(?: \(bottom\))?">.*?</nav>\s*', "\n", s, flags=re.S)
    if n:
        bump("map_pagination_removed", n)
    # page=1 / page=2 in the params would be sent to a static file that ignores
    # them; drop them so the request is honest about what it fetches.
    s, m = re.subn(r'"module":"geolocation","page":"\d+"',
                   '"module":"geolocation"', s)
    if m:
        bump("map_page_param", m)
    return s


# ---------------------------------------------------------------------------
# Pagefind
# ---------------------------------------------------------------------------

def page_title(s):
    m = re.search(r'<title>(.*?)</title>', s, re.S)
    if not m:
        return ""
    t = m.group(1).strip()
    # Berlin: "Item &middot; RRCHNM20"; neatscape: "RRCHNM20 | Exhibit"
    if " &middot; " in t:
        t = t.split(" &middot; ")[0]
    elif t.startswith("RRCHNM20 | "):
        t = t[len("RRCHNM20 | "):]
    return t.strip()


def record_type(rel):
    """Which kind of record a page is, for the Record facet."""
    rel = rel.replace(os.sep, "/")
    if _ITEM.match(rel):
        return "Item"
    if _COLLECTION.match(rel):
        return "Collection"
    if _EXHIBIT.match(rel):
        return "Exhibit"
    return "Page"


def tag_pagefind(s, rel):
    """Mark the canonical content pages for indexing and pin their titles.

    Every page's chrome carries an <h1>, which Pagefind would otherwise use as
    the title of every result. The empty spans hold their values in data
    attributes, read via Pagefind's `name[attr]` syntax, so nothing extra is
    rendered AND nothing extra is indexed as body text -- a filter element's
    text content would otherwise make every item page match a search for
    "item".
    """
    if not is_content_page(rel):
        return s
    # Strip any spans a previous run left, so changes to what we record reach
    # pages that are already tagged. The pattern removes exactly what is added
    # below, and nothing else on the page looks like it.
    s = re.sub(r'<span data-pagefind-(?:meta="title\[data-pf-title\]" '
               r'data-pf-title="[^"]*"|filter="Record\[data-rt\]" '
               r'data-rt="[^"]*")></span>', "", s)
    title = page_title(s) or "RRCHNM20"
    meta = ('<span data-pagefind-meta="title[data-pf-title]" '
            f'data-pf-title="{htmllib.escape(htmllib.unescape(title), quote=True)}">'
            '</span>'
            # Lets items/search.html restrict itself to the 422 item pages
            # while the site-wide search.html stays unrestricted.
            f'<span data-pagefind-filter="Record[data-rt]" '
            f'data-rt="{record_type(rel)}"></span>')
    for open_tag in ('<main id="content" tabindex="-1">',
                     '<div role="main" id="content" tabindex="-1">'):
        tagged = open_tag[:-1] + " data-pagefind-body>"
        if tagged in s:                       # already tagged on an earlier run
            s = s.replace(tagged, tagged + meta, 1)
            bump("pagefind_retagged")
            break
        if open_tag in s:
            s = s.replace(open_tag, tagged + meta, 1)
            bump("pagefind_body")
            break
    return s


def add_pagefind_filters(s, rel):
    """Expose Collection and Item Type as Pagefind facets on item pages.

    Pagefind 1.5.2 reads a filter value from an element's TEXT, not from an
    attribute -- the Name[value] form silently yields an empty value. So the
    Collection filter goes on the element that already holds the name, and the
    Item Type filter wraps just the type word inside its heading, leaving the
    rendered text byte-identical.
    """
    if not _ITEM.match(rel.replace(os.sep, "/")):
        return s
    if 'data-pagefind-filter="Collection"' not in s:
        s, n = re.subn(
            r'(<div id="collection" class="element">\s*<h2>Collection</h2>\s*)'
            r'<div class="element-text">',
            r'\1<div class="element-text" data-pagefind-filter="Collection">', s)
        if n:
            bump("filter_collection", n)
    if 'data-pagefind-filter="Item Type"' not in s:
        s, n = re.subn(
            r'<h2>([A-Za-z][A-Za-z ]*?) Item Type Metadata</h2>',
            r'<h2><span data-pagefind-filter="Item Type">\1</span>'
            r' Item Type Metadata</h2>', s)
        if n:
            bump("filter_item_type", n)
    return s


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def process(s, rel):
    prefix = depth_prefix(rel)

    # head
    s = fix_viewport(s)
    s = drop_feed_links(s)
    s = drop_ie_conditionals(s)
    s = selfhost_jquery(s, prefix)
    s = selfhost_fonts(s, prefix)
    s = add_a11y_css(s, prefix)

    # body chrome
    s = add_theme_class(s)
    s = fix_main_landmark(s, rel == "index.html")
    s = name_landmarks(s)
    s = add_skipnav_and_banner(s)
    s = replace_footer_credit(s)

    # forms and links
    s = fix_search_form(s)
    s = fix_pagination_form(s)
    s = add_page_jump(s, prefix)
    s = drop_sort_links(s)
    s = drop_output_formats(s)
    s = fix_mangled_mall_link(s)
    s = drop_duplicate_collection_id(s)
    s = fix_people_link(s)

    # structure
    s = fix_headings(s, rel)
    s = fix_about_page(s, rel)
    s = fix_relations_table(s)
    s = fix_pdf_objects(s)
    s = fix_map_style(s)
    s = fix_titles(s, rel)

    # dead interactive content -> static replacements
    s = fix_timeline_page(s, rel)
    s = fix_knightlab(s)
    s = fix_drive_image(s)

    # media and maps
    s = relativize_media(s)
    s = fix_map_pages(s, rel)

    # analytics last in <head>, so it survives the head edits above
    s = normalize_matomo(s)

    # Pagefind last: it reads the finished DOM
    s = tag_pagefind(s, rel)
    s = add_pagefind_filters(s, rel)
    return s


def preflight():
    missing = [p for p in (
        "geolocation/map.kml",
        "data/neatline-timeline-1.json",
        "themes/a11y.css",
        "assets/rrchnm-mark.png",
        "assets/histarthist-logo.png",
        "themes/neatscape/css/fonts.css",
        "application/views/scripts/javascripts/vendor/jquery.js",
        "application/views/scripts/javascripts/vendor/jquery-ui.js",
    ) if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        sys.exit("error: missing prerequisites, run tools/harvest.py first:\n  "
                 + "\n  ".join(missing))


def main():
    check = "--check" in sys.argv[1:]
    preflight()
    changed = total = 0
    for rel in html_files():
        if is_skipped(rel):
            continue
        total += 1
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8", errors="replace") as fh:
            before = fh.read()
        after = process(before, rel)
        if after != before:
            changed += 1
            if not check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(after)
    verb = "would change" if check else "changed"
    print(f"{verb} {changed}/{total} html file(s)")
    for key, n in sorted(STATS.items()):
        print(f"  {n:6}  {key}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
