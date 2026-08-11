#!/usr/bin/env python3
"""
Static-search + WCAG 2.2 AA retrofit for the thanksroy.org archive.

Idempotent: every transformation is guarded, so running this twice is a no-op
and `git diff` after a second run must be empty. Operates on every *.html file
in the archive.

Search (Pagefind)
  - point the site-wide search form at /search.html instead of the dead
    https://thanksroy.org/search Omeka endpoint
  - mark the 169 canonical content pages with data-pagefind-body
  - add Collection / Item Type / Tag filters to the 162 item pages
  - regenerate the 171 dead items/search?*.html captures as redirect stubs

WCAG 2.2 AA
  1.3.1  <main>, named landmarks, real <label>s, heading order
  1.4.3  contrast (in themes/default/css/a11y.css)
  2.1.1  the mobile menu opener becomes a <button>
  2.4.1  skip link targets a fragment instead of reloading the page
  2.4.2  disambiguate the 8 "[Untitled]" pages
  2.4.4  name the nameless image-only links
  2.4.7  focus indicator (in a11y.css)
  2.5.8  target size (in a11y.css)

Chrome / robustness
  - RRCHNM archive notice banner (ported from the forustheliving.org archive)
  - RRCHNM logo replaces the "Proudly powered by Omeka" footer credit
  - self-hosted PT Serif instead of the blocked Google Fonts link
  - Output Formats trimmed to dcmes-xml, pointed at the harvested local sidecar
  - absolute origin URLs relativized when the target exists in-repo

Run tools/dcmes_harvest.py first; this script refuses to start if the sidecars
are missing, rather than emitting dead links.

    python3 tools/retrofit.py [--check]
"""
import argparse
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN_RE = re.compile(r'https?://thanksroy\.org')

# Hand-authored; they already carry the final chrome. Skipped wholesale.
AUTHORED = {'search.html', os.path.join('items', 'search.html')}

# Pages whose main content region gets data-pagefind-body.
SIMPLE_PAGES = {'index.html', 'about.html', 'formal-notices.html',
                'howtohelp.html', 'memorial-events.html'}

# COinS rft.type -> the Omeka item-type name the old advanced search offered.
ITEM_TYPE = {
    'Still Image': 'Still Image',
    'document': 'Document',
    'Hyperlink': 'Hyperlink',
    'audioRecording': 'Sound',
}

BANNER = '''    <aside class="notice" aria-label="Archive notice" style="font-size: 12px; \
display: flex; align-items: center; background-color: #f8f8f8; padding: 10px; \
border: 1px solid #ddd; margin-bottom: 0;">
    <a href="https://rrchnm.org" target="_blank" rel="noopener"><img \
src="/rrchnm_logo.png" alt="RRCHNM Logo" style="height: 30px; margin-right: 15px;"/></a>
    <div>
    This is a static copy of the final website maintained by the \
<a href="https://rrchnm.org" target="_blank" rel="noopener">Roy Rosenzweig \
Center for History and New Media</a>.
    </div>
</aside>
'''

FOOTER_OMEKA = '<p>Proudly powered by <a href="http://omeka.org">Omeka</a>.</p>'
# rrchnm.org's own horizontal wordmark (its /img/logo-dark.png, the dark-ink
# variant it uses on light backgrounds -- /img/logo.png is the light-ink one for
# dark backgrounds, and this footer is white). 541x100, shown at 200x37.
FOOTER_LOGO = ('<p class="rrchnm-logo"><a href="https://rrchnm.org">'
               '<img src="/themes/default/images/rrchnm-wordmark.png" width="200" '
               'height="37" alt="Roy Rosenzweig Center for History and New '
               'Media" /></a></p>')
# Previous shape, so a re-run migrates rather than leaving the old square mark.
FOOTER_LOGO_OLD = ('<p class="rrchnm-logo"><a href="https://rrchnm.org">'
                   '<img src="/themes/default/images/rrchnm_logo.png" width="62" '
                   'height="60" alt="Roy Rosenzweig Center for History and New '
                   'Media" /></a></p>')

STATS = {}


def bump(key, n=1):
    STATS[key] = STATS.get(key, 0) + n


def html_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in ('.git', '.crawl', 'pagefind', 'tools')]
        for name in filenames:
            if name.endswith('.html'):
                out.append(os.path.relpath(os.path.join(dirpath, name), ROOT))
    return sorted(out)


def depth_prefix(rel):
    """'' for a root page, '../' one level down, '../../' two."""
    return '../' * (len(rel.replace(os.sep, '/').split('/')) - 1)


# ---------------------------------------------------------------- head/chrome

def fix_head(s, prefix):
    # Feed discovery for feeds we are removing.
    new = re.sub(r'[ \t]*<link rel="alternate"[^>]*/>\s*', '', s)
    if new != s:
        bump('feed_links')
        s = new

    # Blocked Google Fonts -> self-hosted PT Serif.
    if 'fonts.googleapis.com' in s:
        s = re.sub(
            r'<link href="https://fonts\.googleapis\.com[^"]*"([^>]*)>',
            '<link href="%sthemes/default/css/pt-serif.css"\\1>' % prefix, s)
        bump('pt_serif')

    # a11y.css must come after the theme-config inline <style> block so it wins.
    if 'css/a11y.css' not in s:
        s = s.replace(
            '    </style>\n',
            '    </style>\n<link href="%sthemes/default/css/a11y.css" '
            'media="all" rel="stylesheet" type="text/css" >\n' % prefix, 1)
        bump('a11y_css')

    # selectivizr.js was never crawled; the conditional comment is IE6-8 only.
    new = re.sub(r'[ \t]*<!--\[if \(gte IE 6\)&\(lte IE 8\)\].*?<!\[endif\]-->\s*',
                 '', s, flags=re.S)
    if new != s:
        bump('selectivizr')
        s = new
    return s


def fix_landmarks(s, rel, pagefind_body):
    # 2.4.1 -- the skip link used a file-relative href, so on the homepage
    # (served at /) it reloaded the page instead of jumping.
    new = re.sub(r'<a href="[^"]*#content" id="skipnav">',
                 '<a href="#content" id="skipnav">', s)
    if new != s:
        bump('skipnav')
        s = new

    # Archive notice banner, straight after the skip link.
    if 'class="notice"' not in s:
        s = re.sub(r'(<a href="#content" id="skipnav">Skip to main content</a>\n)',
                   r'\1' + BANNER, s, count=1)
        bump('banner')

    if '<header role="banner">' in s:
        s = s.replace('<header role="banner">', '<header>')
        bump('header_role')

    if '<footer role="contentinfo">' in s:
        s = s.replace('<footer role="contentinfo">', '<footer>')
        bump('footer_role')

    # 2.1.1 -- an unfocusable <div> was the only way to open the nav below
    # 768px, where #primary-nav ul.navigation is display:none.
    if '<div class="menu-button button">Menu</div>' in s:
        s = s.replace(
            '<div class="menu-button button">Menu</div>',
            '<button type="button" class="menu-button button" '
            'aria-expanded="false" aria-controls="primary-nav-list">Menu</button>')
        bump('menu_button')

    if '<nav id="primary-nav" role="navigation">' in s:
        s = s.replace('<nav id="primary-nav" role="navigation">',
                      '<nav id="primary-nav" aria-label="Main">')
        # aria-controls target for the menu button.
        s = s.replace('<nav id="primary-nav" aria-label="Main">\n                '
                      '<ul class="navigation">',
                      '<nav id="primary-nav" aria-label="Main">\n                '
                      '<ul class="navigation" id="primary-nav-list">', 1)
        bump('primary_nav')

    # 1.3.1 / 2.4.1 -- a real <main>.
    if '<div id="content" role="main" tabindex="-1">' in s:
        attr = ' data-pagefind-body' if pagefind_body else ''
        s = s.replace('<div id="content" role="main" tabindex="-1">',
                      '<main id="content" tabindex="-1"%s>' % attr)
        s = s.replace('</div><!-- end content -->', '</main><!-- end content -->')
        bump('main')

    # Two unnamed <nav>s per item page, up to three per browse page.
    if '<nav>\n<ul class="item-pagination navigation">' in s:
        s = s.replace('<nav>\n<ul class="item-pagination navigation">',
                      '<nav aria-label="Item">\n<ul class="item-pagination navigation">')
        bump('item_nav')

    if '<nav class="items-nav navigation secondary-nav">' in s:
        s = s.replace('<nav class="items-nav navigation secondary-nav">',
                      '<nav class="items-nav navigation secondary-nav" aria-label="Items">')
        bump('items_nav')

    # Browse pages carry the same pagination nav above and below the results,
    # giving two landmarks with an identical accessible name. Distinguish the
    # lower one so they can be told apart in a landmarks list.
    if s.count('<nav class="pagination-nav" aria-label="Pagination">') > 1:
        head, sep, tail = s.partition('<nav class="pagination-nav" aria-label="Pagination">')
        s = head + sep + tail.replace(
            '<nav class="pagination-nav" aria-label="Pagination">',
            '<nav class="pagination-nav" aria-label="Pagination (bottom)">', 1)
        bump('pagination_nav_name')

    if FOOTER_OMEKA in s:
        s = s.replace(FOOTER_OMEKA, FOOTER_LOGO)
        bump('footer_logo')
    elif FOOTER_LOGO_OLD in s:
        s = s.replace(FOOTER_LOGO_OLD, FOOTER_LOGO)
        bump('footer_logo_migrated')
    return s


def fix_search_form(s):
    """Point the header form at Pagefind and give its input a real label."""
    if 'action="https://thanksroy.org/search"' not in s:
        return s
    s = s.replace('action="https://thanksroy.org/search" method="get">',
                  'action="/search.html" method="get">')
    s = s.replace(
        '<input type="text" name="query" id="query" value="" title="Search">',
        '<label for="query" class="visually-hidden">Search this site</label>'
        '<input type="text" name="query" id="query" value="" placeholder="Search">')

    # The keyword/boolean/exact-match radios are Omeka query modes Pagefind has
    # no equivalent for. Drop the fieldset but keep #advanced-form: Omeka's
    # showAdvancedForm() keys off it to inject the toggle that reveals the link.
    s = re.sub(r'<fieldset id="query-types">.*?</fieldset>\s*', '', s, flags=re.S)

    # wget rewrote this link to whatever items/search?... capture it happened to
    # resolve against, so it has ~180 distinct forms across the archive
    # (../search.html, search%3Ftags=roy.html, items/search%3Fpage=3.html, ...).
    # Normalize them all to the one real search page.
    s = re.sub(r'<p><a href="[^"]*">Advanced Search \(Items only\)</a></p>',
               '<p><a href="/items/search.html">Advanced Search (Items only)</a></p>', s)
    bump('search_form')
    return s


def fix_listing_outputs(s, rel):
    """Browse listings offered five output formats; keep dcmes-xml only.

    Unlike item pages the surviving link is a listing slice, so it points at a
    sidecar named after this page (items/browse?tags=roy.dcmes.xml), harvested
    from the page's own former link.
    """
    if 'id="output-format-list"' not in s or 'outputs-label' not in s:
        return s
    if 'output=atom' not in s and 'output=rss2' not in s:
        return s
    # Match the archive's own convention for '?'-in-filename links, which wget
    # established and every other in-site link uses: escape only the '?', leave
    # '=' literal, and write '&' as the HTML entity.
    sidecar = (os.path.basename(rel)[:-len('.html')] + '.dcmes.xml'
               ).replace('?', '%3F').replace('&', '&amp;')
    s = re.sub(r'(<p id="output-format-list">)\s*.*?(\s*</p>)',
               lambda m: '%s\n        <a href="%s">dcmes-xml</a>%s'
                         % (m.group(1), sidecar, m.group(2)),
               s, flags=re.S)
    bump('listing_outputs')
    return s


def fix_pagination(s):
    """1.3.1/3.3.2 -- the page input was labelled by title= and had no submit."""
    old = '<input type="text" name="page" title="Current Page" value='
    if old not in s:
        return s
    # aria-label, not <label for>: these forms appear twice per page, so an id
    # would be duplicated.
    s = s.replace('<input type="text" name="page" title="Current Page" value=',
                  '<input type="text" name="page" aria-label="Page number" value=')
    s = re.sub(r'(<input type="text" name="page" aria-label="Page number" '
               r'value="\d+">)( of \d+)\s*</form>',
               r'\1\2 <button type="submit" class="button pagination-go">Go</button>'
               r'        </form>', s)
    bump('pagination')
    return s


# ------------------------------------------------------------------ item pages

def coins_item_type(s):
    m = re.search(r'rft\.type=([^&"]+)', s)
    if not m:
        return None
    raw = urllib.parse.unquote_plus(m.group(1))
    return ITEM_TYPE.get(raw, raw)


def fix_item_page(s, rel):
    item_id = os.path.basename(rel)[:-len('.html')]

    # 1.3.1 -- headings ran h1 -> h3 -> h3 -> h2. Promote the .element headings
    # so the page is h1 -> h2 -> h2 ... (a11y.css keeps their visual size).
    new = re.sub(r'(<div[^>]*class="element"[^>]*>\s*)<h3>(.*?)</h3>',
                 r'\1<h2>\2</h2>', s)
    if new != s:
        bump('element_h3')
        s = new

    # Output Formats: keep dcmes-xml only, pointed at the harvested sidecar.
    if 'output=atom' in s or 'output=json' in s or 'output=omeka-xml' in s:
        s = re.sub(
            r'<ul id="output-format-list">.*?</ul>',
            '<ul id="output-format-list">\n'
            '                                <li><a href="%s.dcmes.xml">'
            'dcmes-xml</a></li>\n                </ul>' % item_id,
            s, flags=re.S)
        bump('output_formats')

    # Pagefind facets. Stripped and re-injected rather than guarded, so the
    # shape can change without leaving stale markup behind on a re-run.
    s = re.sub(r'\s*<span data-pagefind-filter="Item Type\[[^\]]*\]"></span>', '', s)
    # Strip exactly what the insert below adds -- a leading single newline, not
    # \s* -- or each run eats another newline and the file never converges.
    s = re.sub(r'\n<div id="item-type" class="element">.*?</div><!-- end item-type -->',
               '', s, flags=re.S)
    s = s.replace(' data-pagefind-filter="Collection"', '')
    s = s.replace(' data-pagefind-filter="Tag"', '')
    # Earlier shape: the filter rode on <main> next to data-pagefind-body, where
    # Pagefind's body handling swallowed the value and the facet came out empty.
    s = re.sub(r'(<main id="content" tabindex="-1" data-pagefind-body)'
               r' data-pagefind-filter="Item Type\[[^\]]*\]"', r'\1', s)

    item_type = coins_item_type(s)
    if item_type:
        # Pagefind 1.5.2 only reads a filter value from an element's TEXT --
        # the documented `Name[value]` attribute form silently yields an empty
        # value (verified against span/div/meta). Rather than hide the value in
        # off-screen text, which screen readers would announce as a stray word
        # before the title, render it as a real metadata row in the theme's own
        # .element shape. The Omeka theme never displayed the item type at all,
        # so this restores information the page was missing.
        block = ('\n<div id="item-type" class="element">\n'
                 '    <h2>Item Type</h2>\n'
                 '    <div class="element-text" data-pagefind-filter="Item Type">%s</div>\n'
                 '</div><!-- end item-type -->' % item_type)
        s = re.sub(r'(<main id="content" tabindex="-1" data-pagefind-body>\s*\n<h1>.*?</h1>\n)',
                   lambda m: m.group(1) + block, s, count=1, flags=re.S)
        bump('filter_type')

    # Collection: the visible link inside #collection.
    def collection_link(m):
        bump('filter_collection')
        return m.group(1) + ' data-pagefind-filter="Collection"' + m.group(2)

    s = re.sub(r'(<div id="collection" class="element">.*?<a)'
               r'( href="[^"]*collections/show/\d+\.html">)',
               collection_link, s, flags=re.S)

    # Tag: every rel="tag" link inside #item-tags.
    n = s.count('rel="tag"')
    if n:
        s = s.replace('rel="tag"', 'rel="tag" data-pagefind-filter="Tag"')
        bump('filter_tag', n)

    # 2.4.2 -- 8 pages share the title "[Untitled]".
    if '<h1>[Untitled]</h1>' in s:
        s = s.replace('<h1>[Untitled]</h1>',
                      '<h1>[Untitled] (Item %s)</h1>' % item_id)
        s = s.replace('<title>[Untitled] &middot; Thanks, Roy</title>',
                      '<title>[Untitled] (Item %s) &middot; Thanks, Roy</title>' % item_id)
        bump('untitled')
    return s


# ------------------------------------------------------------- specific pages

def fix_index(s):
    # 1.3.1 -- the only page in the archive with no <h1>; it started at h2.
    if 'id="home-title"' not in s:
        s = s.replace(
            '<main id="content" tabindex="-1" data-pagefind-body>\n                <div id="primary">',
            '<main id="content" tabindex="-1" data-pagefind-body>\n'
            '                <h1 id="home-title" class="visually-hidden">Thanks, Roy'
            ' &mdash; Remembering Roy Rosenzweig, 1950-2007</h1>\n'
            '                <div id="primary">', 1)
        bump('home_h1')

    # Invalid <p><p ...></p></p> nesting Omeka emitted around the intro text.
    if '<p><p style="text-align:left;">' in s:
        s = s.replace('<p><p style="text-align:left;">', '<p style="text-align:left;">', 1)
        s = s.replace('<a href="about.html">More....</a></p></p>',
                      '<a href="about.html">More about Roy</a></p>', 1)
        bump('index_p_nesting')

    # The featured item is randomized at runtime and both blocks merely repeat
    # text the item pages own, so keep them out of the index.
    if 'id="featured-item"' in s and 'data-pagefind-ignore' not in s:
        s = s.replace('<div id="featured-item">',
                      '<div id="featured-item" data-pagefind-ignore>')
        s = s.replace('<div id="recent-items">',
                      '<div id="recent-items" data-pagefind-ignore>')
        bump('pagefind_ignore')

    # Placed right after the block rather than on DOMContentLoaded, so the swap
    # happens as the element is parsed and there is no flash of the frozen item.
    if 'featured-item.js' not in s:
        s = s.replace(
            '    </div><!--end featured-item-->',
            '    </div><!--end featured-item-->\n'
            '    <script src="themes/default/javascripts/featured-item.js"></script>', 1)
        bump('featured_js')
    return s


def fix_memorial_events(s):
    # 1.3.1 -- id="primary" appeared twice, nested.
    if s.count('<div id="primary">') > 1:
        head, sep, tail = s.partition('<div id="primary">')
        s = head + sep + tail.replace('<div id="primary">',
                                      '<div class="primary-content">', 1)
        bump('dup_id')

    # 2.4.4/4.1.2 -- an image-only link whose <img alt=""> left it with no name.
    old = ('<a href="http://chnm.gmu.edu/celebration/">'
           '<img src="http://chnm.gmu.edu/celebration/image001-1.jpg" alt="" /></a>')
    if old in s:
        s = s.replace(old,
                      '<a href="http://chnm.gmu.edu/celebration/">'
                      '<img src="http://chnm.gmu.edu/celebration/image001-1.jpg" '
                      'alt="Roy Rosenzweig Celebration" /></a>')
        bump('nameless_link')

    # 1.1.1 -- a directions map carrying alt="" is informative, not decorative.
    old = '<img src="http://coyote.gmu.edu/map/arling.gif" alt="" />'
    if old in s:
        s = s.replace(old,
                      '<img src="http://coyote.gmu.edu/map/arling.gif" '
                      'alt="Map of the George Mason University Arlington campus at '
                      '3401 Fairfax Drive, at the intersection of Washington and '
                      'Fairfax Boulevards. Directions in text follow." />')
        bump('map_alt')
    return s


def relativize(s, rel):
    """Point absolute origin URLs at the local file when we actually have it.

    Nearly a no-op today: the crawl excluded every files/ media directory, so
    the tree holds only six media files. Written generically so it re-applies
    automatically if the media is ever mirrored.
    """
    prefix = depth_prefix(rel)

    def sub(m):
        attr, path = m.group(1), m.group(2)
        clean = urllib.parse.unquote(path.split('?')[0].split('#')[0])
        if not clean or not os.path.isfile(os.path.join(ROOT, clean)):
            return m.group(0)
        bump('relativized')
        return '%s="%s%s"' % (attr, prefix, path)

    s = re.sub(r'\b(src|href)="https?://thanksroy\.org/([^"]*)"', sub, s)

    # A Hyperlink item whose URL field is rendered as bare text, pointing at a
    # file we do have. Make it a working link.
    old = '<div class="element-text">http://thanksroy.org/roy-wp-obituary.jpg</div>'
    if old in s:
        s = s.replace(old, '<div class="element-text"><a href="%sroy-wp-obituary.jpg">'
                           'roy-wp-obituary.jpg</a></div>' % prefix)
        bump('relativized_text')
    return s


# ------------------------------------------------------------- redirect stubs

STUB = '''<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Redirecting to Search Items &middot; Thanks, Roy</title>
<link rel="canonical" href="/items/search.html">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0;url={target}">
<link href="/themes/default/css/style.css%3Fv=2.8.css" media="all" rel="stylesheet" type="text/css">
<link href="/themes/default/css/pt-serif.css" media="all" rel="stylesheet" type="text/css">
<link href="/themes/default/css/a11y.css" media="all" rel="stylesheet" type="text/css">
</head>
<body>
<main id="content" tabindex="-1" style="padding: 2em 5.26316%;">
<h1>Search Items</h1>
<p>Omeka's advanced item search has been replaced by a client-side search.
Redirecting to <a href="{target}">Search Items</a>&hellip;</p>
</main>
</body>
</html>
'''


def stub_target(name):
    """items/search?tags=X.html -> a prefilled query; other facets go bare."""
    q = name[len('search?'):-len('.html')]
    params = urllib.parse.parse_qs(q, keep_blank_values=True)
    tags = params.get('tags', [])
    if tags and tags[0].strip():
        return '/items/search.html?query=%s' % urllib.parse.quote_plus(tags[0])
    return '/items/search.html'


def write_stubs(check):
    items = os.path.join(ROOT, 'items')
    changed = 0
    for name in sorted(os.listdir(items)):
        if not (name.startswith('search?') and name.endswith('.html')):
            continue
        path = os.path.join(items, name)
        body = STUB.format(target=stub_target(name))
        if open(path, encoding='utf-8').read() == body:
            continue
        changed += 1
        if not check:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(body)
    if changed:
        bump('stubs', changed)
    return changed


# ------------------------------------------------------------------------ main

def process(rel, check):
    path = os.path.join(ROOT, rel)
    original = open(path, encoding='utf-8').read()
    s = original
    prefix = depth_prefix(rel)

    norm = rel.replace(os.sep, '/')
    is_item = norm.startswith('items/show/')
    pagefind_body = (is_item
                     or norm in SIMPLE_PAGES
                     or norm.startswith('collections/show/'))

    s = fix_head(s, prefix)
    s = fix_landmarks(s, rel, pagefind_body)
    s = fix_search_form(s)
    s = fix_listing_outputs(s, rel)
    s = fix_pagination(s)
    if is_item:
        s = fix_item_page(s, rel)
    if norm == 'index.html':
        s = fix_index(s)
    if norm == 'memorial-events.html':
        s = fix_memorial_events(s)
    s = relativize(s, rel)

    if s != original:
        if not check:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(s)
        return True
    return False


def preflight():
    """Every page that keeps an Output Formats link needs its sidecar on disk."""
    missing = []
    for rel in html_files():
        norm = rel.replace(os.sep, '/')
        if norm in AUTHORED or norm.startswith('items/search?'):
            continue
        body = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        needs = (re.fullmatch(r'items/show/\d+\.html', norm)
                 or ('id="output-format-list"' in body and 'outputs-label' in body))
        if needs and not os.path.isfile(
                os.path.join(ROOT, rel[:-len('.html')] + '.dcmes.xml')):
            missing.append(rel)
    if missing:
        print('ERROR: %d pages keep an Output Formats link but have no .dcmes.xml\n'
              '       sidecar (e.g. %s).\n'
              '       Run tools/dcmes_harvest.py first -- otherwise that link would\n'
              '       point at a file that does not exist.'
              % (len(missing), ', '.join(sorted(missing)[:3])), file=sys.stderr)
        return False
    for asset in ('rrchnm_logo.png',                              # archive banner
                  'themes/default/images/rrchnm-wordmark.png',   # footer credit
                  'themes/default/css/a11y.css', 'themes/default/css/pt-serif.css',
                  'themes/default/javascripts/featured-item.js'):
        if not os.path.isfile(os.path.join(ROOT, asset)):
            print('ERROR: missing asset %s' % asset, file=sys.stderr)
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='report what would change without writing')
    args = ap.parse_args()

    if not preflight():
        return 2

    changed = 0
    for rel in html_files():
        norm = rel.replace(os.sep, '/')
        if norm in AUTHORED:
            continue
        if norm.startswith('items/search?'):
            continue          # regenerated wholesale below
        if process(rel, args.check):
            changed += 1
    changed += write_stubs(args.check)

    verb = 'would change' if args.check else 'changed'
    print('%s %d files' % (verb, changed))
    for key in sorted(STATS):
        print('  %-20s %d' % (key, STATS[key]))
    if args.check and changed:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
