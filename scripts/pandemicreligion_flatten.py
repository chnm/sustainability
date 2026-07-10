#!/usr/bin/env python3
"""Flatten a Pandemic Religion Omeka S wget capture into a static archive.

One capture (produced by /workspace/util/websites-mirrorer/multi-wget.py) is
turned into a committable static site under sustainability/pandemicreligion/.

Pipeline (see pandemicreligion/PLAN.md for the design):

  1. copy the capture tree, dropping .crawl/, the old .gitignore, and the whole
     files/ media dir (no media is committed -- item <img>s already point at
     absolute https://<domain>/files/... URLs on the still-live host);
  2. prune wget query-permutation junk (advanced-search / facet / sort / feed
     combinations) while keeping real content and the single-param nav browse
     pages;
  3. over every .html/.css: externalize the few *relative* files/ references to
     absolute live-domain URLs, strip the Matomo analytics block, rewire the
     header search form to the local Pagefind search.html, and neutralize dead
     same-domain submit forms (Collecting "contribute", reCAPTCHA);
  4. tag real content pages with data-pagefind-body so Pagefind only indexes
     item / item-set / page / home content;
  5. emit a root search.html (Pagefind UI, derived from the site's own chrome),
     a Caddy Dockerfile, and a minimal .gitignore.

README.md is generated separately by the mirrorer's gen-readmes.py (crawl
provenance), and the Pagefind index is built with `npx pagefind` -- both are
post-steps run by the conversion driver, not by this script.

Usage:
    pandemicreligion_flatten.py <src_capture_dir> <domain> <out_dir> [--slug SLUG]

Example:
    pandemicreligion_flatten.py \
        /workspace/wgets/pandemicreligion/hazon.collectingthesetimes.org \
        hazon.collectingthesetimes.org \
        /workspace/sustainability/pandemicreligion/hazon.collectingthesetimes.org
"""
import argparse
import html
import re
import shutil
import sys
from pathlib import Path

# Vendored assets copied into every site (footer logo; the two Leaflet marker
# images wget never fetched -- see copy_assets / the maps note below).
_ASSETS = Path(__file__).resolve().parent / "assets"

# ---------------------------------------------------------------------------
# 1. copy
# ---------------------------------------------------------------------------

# Basenames never copied into the static site.
_IGNORE = shutil.ignore_patterns(".crawl", "files", ".gitignore", ".DS_Store")


def copy_tree(src: Path, out: Path, extra_ignore=()) -> None:
    if out.exists():
        shutil.rmtree(out)
    ignore = shutil.ignore_patterns(".crawl", "files", ".gitignore", ".DS_Store",
                                    *extra_ignore)
    shutil.copytree(src, out, ignore=ignore)


# ---------------------------------------------------------------------------
# 2. prune query-permutation junk
# ---------------------------------------------------------------------------

# Junk = advanced-search / facet / sort / feed / pagination permutations that
# wget saved as `item?<querystring>.html`. Matched on the file BASENAME with
# precise substrings (NOT shell globs -- a naive `item??*` glob would eat the
# legitimate single-param `item?item_set_id=<N>.html` browse pages we keep).
_JUNK_SUBSTRINGS = (
    "fulltext_search",       # ?fulltext_search=...
    "property[",             # ?property[0][joiner]=... advanced search
    "resource_class_id",     # ?resource_class_id[]=...
    "resource_template_id",  # ?resource_template_id=...
    "resource_type",         # ?resource_type=...
    "site_id",               # ?site_id=...
    "sort_by",               # ?sort_by=...
    "sort_order",            # ?sort_order=...
    "?output=",              # feed/API exports
    "&",                     # any multi-param permutation (page=N&..., facets)
)
# Malformed URL-in-filename (wget saw an absolute URL as a query value) and the
# literal double-`?` permutation.
_JUNK_RE = re.compile(r"^item\?(https?|\?)", re.IGNORECASE)


def is_junk(name: str, keep_pagination: bool = False) -> bool:
    """True if an html basename is a prunable query-permutation file.

    With keep_pagination, the default-sorted browse pagination files
    (item?...&sort_by=created&sort_order=desc&page=N.html) are kept, so a
    multi-page site's paginated browse (and its working next/prev links) survive
    -- used for the larger sites where the browse spans >1 page.
    """
    if "?" not in name:
        return False                       # real page (item/N.html, page/x.html)
    if keep_pagination and re.search(
            r"[?&]sort_by=created&sort_order=desc&page=\d+\.html$", name):
        return False   # default-sorted pagination -- item browse (&sort_by) AND
                       # item-set browse (?sort_by, sort is the first param)
    if _JUNK_RE.match(name):
        return True
    return any(s in name for s in _JUNK_SUBSTRINGS)


def prune_junk(out: Path, keep_pagination: bool = False) -> list[str]:
    pruned = []
    for p in sorted(out.rglob("*.html")):
        if is_junk(p.name, keep_pagination):
            pruned.append(str(p.relative_to(out)))
            p.unlink()
    return pruned


# ---------------------------------------------------------------------------
# 3. per-file html/css transforms
# ---------------------------------------------------------------------------

_MATOMO_RE = re.compile(r"<!-- Matomo -->.*?<!-- End Matomo Code -->\s*",
                        re.DOTALL)
# Fallback: an inline <script> that references the _paq tracker, comments absent.
_MATOMO_SCRIPT_RE = re.compile(
    r"<script[^>]*>(?:(?!</script>).)*?_paq(?:(?!</script>).)*?</script>\s*",
    re.DOTALL)


def strip_matomo(text: str) -> str:
    text, n = _MATOMO_RE.subn("", text)
    if n == 0:
        text = _MATOMO_SCRIPT_RE.sub("", text)
    return text


def externalize_media(text: str, domain: str) -> str:
    """Rewrite the *relative* files/ references to absolute live-domain URLs.

    Item media is already absolute (https://<domain>/files/{square,large,...});
    only theme/site assets under files/asset are captured as relative paths
    (e.g. ../../../files/asset/<hash>.png). Absolute refs are left untouched
    because these patterns only fire right after a quote.
    """
    base = f"https://{domain}/files/"
    # "../"*n + files/   ->   absolute
    text = re.sub(r'(?<=["\'])(?:\.\./)+files/', base, text)
    # "/files/  and  "files/  (root-absolute or bare relative) -> absolute
    text = re.sub(r'(?<=["\'])/?files/', base, text)
    return text


def _depth_prefix(rel: Path) -> str:
    """`../` * (number of path segments above the site root)."""
    return "../" * (len(rel.parts) - 1)


def rewire_search(text: str, domain: str, slug: str, prefix: str) -> str:
    """Point the header search form at the local Pagefind search.html."""
    action = f'https://{domain}/s/{slug}/index/search'
    text = text.replace(
        f'action="{action}"',
        f'action="{prefix}search.html" method="get"')
    # Omeka's fulltext field -> the name Pagefind's search.html reads (?query=).
    text = text.replace('name="fulltext_search"', 'name="query"')
    return text


def neutralize_forms(text: str, domain: str) -> str:
    """Disable remaining same-domain POST forms (contribute / reCAPTCHA).

    After rewire_search, the only absolute same-domain form actions left are the
    Collecting "contribute/share" submits, which cannot work statically.
    """
    return re.sub(
        rf'(<form\b[^>]*?)\s+action="https://{re.escape(domain)}/[^"]*"',
        r'\1 action="#" onsubmit="return false;" data-static-disabled',
        text)


_DEAD_FORM_NOTE = (
    '<div class="archived-form-note" role="note"><p>'
    '<strong>This site is an archive and is no longer accepting contributions.</strong> '
    'The original contribution form was part of the live site and is not included in '
    'this archived copy. Materials contributed while the project was active remain '
    'available to browse and search. For questions about this archive, contact '
    '<a href="mailto:chnm@gmu.edu">chnm@gmu.edu</a>.</p></div>')


def replace_dead_forms(text: str) -> str:
    """Replace neutralized submit forms (the Collecting contribute form) with a
    note. The dead form's ~30 unlabeled fields, selects, and reCAPTCHA otherwise
    fail WCAG 2.2 AA (label / select-name / aria-valid-attr); it can never submit
    from a static mirror, so a plain explanatory note is both accessible and
    clearer than a form that silently does nothing."""
    return re.sub(r"<form\b[^>]*data-static-disabled[^>]*>.*?</form>",
                  _DEAD_FORM_NOTE, text, flags=re.DOTALL)


# --- archive pass: contact email + contribute calls-to-action -----------------

_SITE_CONTACT = "pandemicreligion@gmail.com"     # the project's own "Contact us"
_ARCHIVE_CONTACT = "chnm@gmu.edu"                 # address; archived items' own


def archive_contact_email(text: str) -> str:
    """Redirect the project's own contact address to the archive maintainer.

    Only the site-chrome "Contact us" address (pandemicreligion@gmail.com) is
    rewritten. The thousands of submitter / newsletter / item-metadata addresses
    inside archived items are historic primary-source content and are left
    exactly as captured.
    """
    return (text.replace(f"mailto:{_SITE_CONTACT}", f"mailto:{_ARCHIVE_CONTACT}")
                .replace(_SITE_CONTACT, _ARCHIVE_CONTACT))


# distinctive href fragments of the Collecting "contribute / share" pages across
# the seven sites. A dead static mirror can't collect anything, so links to them
# are removed (nav items and CTA buttons) or de-linked (inline prose keeps its
# words). The a11y skip link and page-sequence pagination are preserved.
_CONTRIBUTE_HREFS = ("share-your-experience", "contribute-your-materials",
                     "collectingform", "find-a-collecting-project",
                     "page/share.html")
_CH = "(?:" + "|".join(re.escape(h) for h in _CONTRIBUTE_HREFS) + ")"


def _keep_contribute_link(open_tag: str, inner: str) -> bool:
    """A link that points at a contribute page but must stay: the accessibility
    'Skip to main content' link and Prev/Next page-sequence pagination."""
    if 'id="skipnav"' in open_tag:
        return True
    return inner.strip().strip("»«›‹→⭢ \t") in ("Next", "Previous", "Prev")


def strip_contribute_ctas(text: str) -> str:
    """Neutralize invitations to contribute while keeping historic descriptions.

    1. nav <li> whose sole content is a contribute link  -> drop the menu item
    2. prominent CTA buttons (button/contribute class, or a → / ⭢ arrow) -> drop
    3. any remaining contribute link (inline prose)      -> unwrap, keep words
    """
    li = (r'<li\b[^>]*>\s*(?P<a><a\b[^>]*href="[^"]*' + _CH
          + r'[^"]*"[^>]*>)(?P<inner>.*?)</a>\s*</li>')
    text = re.sub(li, lambda m: m.group(0)
                  if _keep_contribute_link(m.group("a"), m.group("inner")) else "",
                  text, flags=re.DOTALL)

    button = (r'<a\b[^>]*(?:class="[^"]*(?:button|contribute)[^"]*"[^>]*'
              r'href="[^"]*' + _CH + r'[^"]*"'
              r'|href="[^"]*' + _CH + r'[^"]*"[^>]*class="[^"]*(?:button|contribute)[^"]*")'
              r'[^>]*>.*?</a>')
    text = re.sub(button, "", text, flags=re.DOTALL)
    arrow = r'<a\b[^>]*href="[^"]*' + _CH + r'[^"]*"[^>]*>[^<]*[→⭢][^<]*</a>'
    text = re.sub(arrow, "", text, flags=re.DOTALL)

    inline = r'(?P<a><a\b[^>]*href="[^"]*' + _CH + r'[^"]*"[^>]*>)(?P<inner>.*?)</a>'
    text = re.sub(inline, lambda m: m.group(0)
                  if _keep_contribute_link(m.group("a"), m.group("inner"))
                  else m.group("inner"),
                  text, flags=re.DOTALL)
    return text


def ensure_archive_statement(text: str) -> str:
    """Contribute pages that had no live <form> to replace (onetable's 'Share
    Your Experience', the 'Find a Collecting Project' directory) get the same
    archived statement, anchored just after their own page heading."""
    if "archived-form-note" in text:
        return text
    return re.sub(
        r'(<h[12][^>]*>\s*(?:Share Your Experience|Find a Collecting Project)\s*</h[12]>)',
        lambda m: m.group(1) + _DEAD_FORM_NOTE, text, count=1, flags=re.IGNORECASE)


def redirect_external_slugs(text: str, external: dict) -> str:
    """Point links into other slugs of a multi-site Omeka S install at their own
    dedicated domains, so a hub archive doesn't duplicate sites archived
    separately. external = {slug: domain}. Handles relative links at any depth
    (../../<slug>/…, s/<slug>/…) and the s/<slug>.html site-home file."""
    for slug, domain in external.items():
        s = re.escape(slug)
        pre = r'((?:href|src)=")(?:[^"]*?/)?'    # attr + optional path prefix
        # the slug's site home (.../<slug>.html or .../<slug>/index.html) -> the
        # dedicated site root (its archive home is index.html, not s/<slug>/...)
        text = re.sub(pre + rf'{s}(?:\.html|/index\.html)([^"]*)"',
                      rf'\1https://{domain}/\2"', text)
        # any other slug page -> the same path on the dedicated domain
        text = re.sub(pre + rf'{s}/([^"]*)"',
                      rf'\1https://{domain}/s/{slug}/\2"', text)
    return text


_FOOTER_LOGO = ('<a href="https://www.gmu.edu/" class="footer-gmu">'
                '<img src="{prefix}assets/gmu-logo.png" '
                'alt="George Mason University" style="height:2.5rem;width:auto"></a>')


def replace_footer(text: str, prefix: str) -> str:
    """Swap the shared 'Powered by Omeka S' footer line for the GMU logo."""
    return text.replace("Powered by Omeka S", _FOOTER_LOGO.format(prefix=prefix))


def _remove_div_blocks(text: str, class_token: str) -> str:
    """Remove every <div ...class="...class_token..."...>...</div>, div-balanced."""
    open_re = re.compile(r'<div\b[^>]*class="[^"]*' + re.escape(class_token)
                         + r'[^"]*"[^>]*>')
    tag_re = re.compile(r'<div\b|</div>')
    out, pos = [], 0
    while True:
        m = open_re.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        out.append(text[pos:m.start()])
        depth, end = 1, m.end()
        for t in tag_re.finditer(text, m.end()):
            depth += 1 if t.group() == "<div" else -1
            if depth == 0:
                end = t.end()
                break
        pos = end
    return "".join(out)


def remove_browse_controls(text: str) -> str:
    """Drop the .browse-controls block (pagination, sort form, advanced search).

    These collections are small enough that every item fits on one page, and the
    controls only GET/POST to the dead live Omeka server. The header Pagefind
    search stays for finding items.
    """
    return _remove_div_blocks(text, "browse-controls")


def theme_colors(text: str) -> tuple[str, str]:
    """(primary, accent) hex colors from the page's inline theme <style>.

    Each Omeka S site customizes its palette inline: `a:link {color: #rrggbb}`
    is the brand color, `a:hover {background-color: #rrggbb}` a lighter accent.
    Used to tint the archive banner per site. Falls back to a neutral pair.
    """
    blob = " ".join(re.findall(r"<style>(.*?)</style>", text, re.DOTALL))
    prim = re.search(r"a:link\s*\{[^}]*?color:\s*(#[0-9a-fA-F]{3,6})", blob, re.DOTALL)
    acc = re.search(r"a:hover[^{]*\{[^}]*?background-color:\s*(#[0-9a-fA-F]{3,6})",
                    blob, re.DOTALL)
    return (prim.group(1) if prim else "#333333",
            acc.group(1) if acc else "#cccccc")


def _title_parts(text: str) -> list:
    m = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    return [p.strip() for p in m.group(1).split("·")] if m else []


def detect_site_name(home_text: str, sample_text: str) -> str:
    """The human site name.

    Themes order <title> differently -- the spoke theme is
    "Site · Page · Pandemic Religion" (site first), the default theme is
    "Page · Site · Pandemic Religion" (site second). The site name is the one
    segment common to every page (other than the trailing "Pandemic Religion"),
    so detect it by intersecting two pages' titles.
    """
    h, s = _title_parts(home_text), _title_parts(sample_text)
    common = (set(h) & set(s)) - {"Pandemic Religion", ""}
    if len(common) == 1:
        return next(iter(common))
    if common:                       # >1 common: prefer the site-adjacent slot
        return max(common, key=len)
    return h[-2] if len(h) >= 3 else (h[0] if h else "")   # fallbacks


def page_title(text: str, site: str) -> str:
    """The page-specific part of <title>: every segment except the site name and
    the trailing "Pandemic Religion". Order-independent."""
    keep = [p for p in _title_parts(text) if p and p != site and p != "Pandemic Religion"]
    return " · ".join(keep)


def add_archive_banner(text: str, name: str, primary: str, accent: str,
                       prefix: str) -> str:
    """Inject the RRCHNM 'archived copy' banner at the top of every page.

    Modeled on the shared RRCHNM archive banner (e.g. hurricane.dev.chnm.gmu.edu)
    but tinted with the site's own brand/accent colors. Placed inside
    .off-canvas-content (Foundation) as a static top bar -- not sticky, to avoid
    fighting the theme's sticky nav.
    """
    style = (
        "<style>"
        f".pr-abanner{{background:{primary};color:#fefefe;"
        f"border-bottom:3px solid {accent};font-size:.8rem;line-height:1.4}}"
        ".pr-abanner__in{max-width:75rem;margin:0 auto;display:flex;"
        "align-items:center;gap:.6rem;padding:.4rem 1rem}"
        ".pr-abanner__logo{flex:0 0 auto;width:30px;height:29px;"
        f'background:url("{prefix}assets/rrchnm_logo.png") center/contain no-repeat}}'
        ".pr-abanner__t{margin:0;color:#fefefe}"
        ".pr-abanner .pr-abanner__t a{color:#fefefe;text-decoration:underline}"
        ".pr-abanner .pr-abanner__t a:hover{color:#fefefe;background:transparent}"
        "</style>")
    banner = (
        '<div class="pr-abanner" role="note"><div class="pr-abanner__in">'
        '<a class="pr-abanner__logo" href="https://rrchnm.org" target="_blank" '
        'rel="noopener" aria-label="Roy Rosenzweig Center for History and New Media"></a>'
        f'<p class="pr-abanner__t">This is an archived copy of <em>{html.escape(name)}</em>, '
        'provided by the <a href="https://rrchnm.org" target="_blank" rel="noopener">'
        'Roy Rosenzweig Center for History and New Media</a>.</p></div></div>')
    text = text.replace("</head>", style + "</head>", 1)
    occ = re.search(r'<div class="off-canvas-content[^"]*"[^>]*>', text)
    if occ:
        text = text[:occ.end()] + banner + text[occ.end():]
    else:
        text = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + banner, text, count=1)
    return text


# ---------------------------------------------------------------------------
# 3b. WCAG 2.2 AA remediation
# ---------------------------------------------------------------------------

def _rename_div_block(text: str, class_token: str, new_tag: str) -> str:
    """Rename <div ...class="...class_token...">...</div> to <new_tag>, div-balanced."""
    open_re = re.compile(r'<div\b([^>]*class="[^"]*' + re.escape(class_token)
                         + r'[^"]*"[^>]*)>')
    tag_re = re.compile(r'<div\b|</div>')
    out, pos = [], 0
    while True:
        m = open_re.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        out.append(text[pos:m.start()])
        depth, end = 1, m.end()
        for t in tag_re.finditer(text, m.end()):
            depth += 1 if t.group() == "<div" else -1
            if depth == 0:
                end = t.end()
                break
        inner = text[m.end():end - len("</div>")]
        out.append(f"<{new_tag}{m.group(1)}>{inner}</{new_tag}>")
        pos = end
    return "".join(out)


def fix_definition_lists(text: str) -> str:
    """Fix Omeka S's invalid item-metadata <dl> (WCAG 1.3.1 / axe definition-list).

    Omeka emits `<dl><div class="property"><dt>..</dt><div class="values">
    <dl class="value">text</dl></div></div></dl>` -- the value wrapper is a div
    (not <dd>) and each value is a nested <dl> with no dt/dd. Rewrite the leaf
    value <dl>s to <div>s and the .values wrapper to <dd>, giving valid
    dl > div(dt, dd) structure.
    """
    # leaf value <dl>s are invalid (no dt/dd) -> plain <div> (safe anywhere).
    # Match any trailing classes too (e.g. class="value uri"); leaving those as
    # <dl> would also break the region scoping below.
    text = re.sub(r'<dl class="value([^"]*)"([^>]*)>(.*?)</dl>',
                  r'<div class="value\1"\2>\3</div>', text, flags=re.DOTALL)
    # the .values wrapper must be a <dd> -- but ONLY inside the metadata <dl>.
    # Scope the rename to each <dl>...</dl> region so unrelated .values blocks
    # (e.g. the "Item Sets" list, which uses <h4> and sits outside the dl) stay
    # <div> rather than becoming orphan <dd>s (axe dlitem).
    def _fix_region(m: "re.Match") -> str:
        return m.group(1) + _rename_div_block(m.group(2), "values", "dd") + m.group(3)
    return re.sub(r"(<dl\b[^>]*>)(.*?)(</dl>)", _fix_region, text, flags=re.DOTALL)


def build_item_titles(out: Path, slug: str, site: str) -> dict:
    """{item_id: title} from each item page's <title> (page-specific segment)."""
    titles = {}
    itemdir = out / "s" / slug / "item"
    if itemdir.is_dir():
        for f in itemdir.glob("*.html"):
            m = re.match(r"(\d+)\.html$", f.name)
            if not m:
                continue
            t = page_title(f.read_text(encoding="utf-8", errors="replace"), site)
            if t:
                titles[m.group(1)] = t
    return titles


def fix_link_names(text: str, titles: dict) -> str:
    """Give image-only item links an accessible name (WCAG 2.4.4/4.1.2 link-name).

    - Grid `.thumbnail` links duplicate the adjacent title link -> hide them from
      AT and the tab order (aria-hidden + tabindex=-1).
    - Standalone image links (e.g. the home showcase) are the only link to their
      item -> set the <img> alt to the item's title.
    """
    text = text.replace('<a class="thumbnail"',
                        '<a class="thumbnail" tabindex="-1" aria-hidden="true"')

    def repl(m: "re.Match") -> str:
        href, pre, post = m.group(1), m.group(2), m.group(3)
        idm = re.search(r"item/(\d+)\.html", href)
        title = titles.get(idm.group(1)) if idm else None
        alt = html.escape(title, quote=True) if title else "Featured item"
        return f'<a href="{href}"><img{pre} alt="{alt}"{post}></a>'

    return re.sub(r'<a href="([^"]*item/\d+\.html)"><img([^>]*?)\s+alt=""([^>]*?)></a>',
                  repl, text)


def fix_images(text: str) -> str:
    """Give alt-less images an alt (WCAG 1.1.1 image-alt / 4.1.2 link-name).

    Some themes put an alt-less logo <img> inside a link (e.g. the RRCHNM
    footer logo `<a class="logo" href="rrchnm.org"><img></a>`), which fails both
    image-alt and the link's link-name. Name that logo; give every other
    alt-less image a decorative empty alt.
    """
    text = re.sub(
        r'(<a [^>]*href="[^"]*rrchnm[^"]*"[^>]*><img)((?:(?!alt=)[^>])*)>',
        r'\1\2 alt="Roy Rosenzweig Center for History and New Media">', text)
    return re.sub(r'(<img)((?:(?!alt=)[^>])*)>', r'\1\2 alt="">', text)


def fix_selects(text: str) -> str:
    """Give any <select> lacking an accessible name an aria-label (WCAG 4.1.2
    select-name). Omeka S item pages carry a linked-resources property filter
    (id=filter-property) with no <label>; the browse sort selects already have
    aria-label."""
    def repl(m: "re.Match") -> str:
        tag = m.group(0)
        if "aria-label" in tag:
            return tag
        sid = re.search(r'\bid="([^"]*)"', tag)
        sid = sid.group(1) if sid else ""
        if sid and f'for="{sid}"' in text:            # already has a <label for>
            return tag
        label = ("Filter linked resources by property"
                 if sid == "filter-property" else "Filter")
        return tag[:-1] + f' aria-label="{label}">'
    return re.sub(r"<select\b[^>]*>", repl, text)


# ---------------------------------------------------------------------------
# 4. Pagefind body tagging
# ---------------------------------------------------------------------------

_CONTENT_OPEN = '<div id="content" role="main">'
_CONTENT_OPEN_TAGGED = '<div id="content" role="main" data-pagefind-body>'

# Real content pages worth indexing (relative posix path).
_CONTENT_PAGE_RE = re.compile(
    r"^(index\.html"
    r"|s/[^/]+/item/\d+\.html"
    r"|s/[^/]+/item-set/\d+\.html"
    r"|s/[^/]+/page/[^/]+\.html)$")


def is_content_page(rel_posix: str) -> bool:
    return bool(_CONTENT_PAGE_RE.match(rel_posix))


def pagefind_title(text: str, site: str, is_home: bool) -> str:
    """Per-page result title for Pagefind.

    Every page's chrome has an <h1> that Pagefind would otherwise use as the
    title of *every* result. Use the page-specific <title> segment instead (the
    site name for the home page).
    """
    if is_home:
        return site
    return page_title(text, site) or site


def tag_pagefind_body(text: str, title: str) -> str:
    """Tag #content for indexing and pin the result title.

    The empty span carries the title in a data-attribute (read via Pagefind's
    `title[attr]` syntax), so nothing extra is rendered or added to the body
    content -- it just overrides the automatic (wrong) h1-based title.
    """
    meta = (f'<span data-pagefind-meta="title[data-pf-title]" '
            f'data-pf-title="{html.escape(title, quote=True)}"></span>')
    return text.replace(_CONTENT_OPEN, _CONTENT_OPEN_TAGGED + meta, 1)


# ---------------------------------------------------------------------------
# 5. search.html, Dockerfile, .gitignore
# ---------------------------------------------------------------------------

_PAGEFIND_HEAD = (
    '<link href="pagefind/pagefind-ui.css" rel="stylesheet">\n'
    '<script src="pagefind/pagefind-ui.js"></script>\n'
    '<style>#pf-search{max-width:48rem;margin:1rem auto}'
    '#pf-search{--pagefind-ui-primary:#1c6896;--pagefind-ui-scale:.9}</style>\n')

_PAGEFIND_INIT = """
<script>
window.addEventListener('DOMContentLoaded', function () {
    var ui = new PagefindUI({ element: '#pf-search', showSubResults: true, showImages: false, pageSize: 10 });
    var q = new URLSearchParams(window.location.search).get('query');
    if (q) { ui.triggerSearch(q); }
});
</script>
"""

_SEARCH_UI = '\n<h1>Search</h1>\n<div id="pf-search"></div>\n'

_DOCKERFILE = """\
# syntax=docker/dockerfile:1
# Preview this flattened Pandemic Religion archive as a static site.
#   docker build -t pandemicreligion-preview .
#   docker run -d -p 8100:80 pandemicreligion-preview
# Files with a literal '?' in their names (Omeka S browse permutations, ?v=
# assets) serve fine: %3F in the request URL decodes to the on-disk '?'.
FROM caddy:alpine
COPY <<'EOF' /etc/caddy/Caddyfile
:80 {
\troot * /usr/share/caddy
\tfile_server
}
EOF
COPY . /usr/share/caddy
"""

_GITIGNORE = """\
# Minimal: media lives on the live host (never committed); .crawl/ is dropped
# during flattening. Nothing under files/ is referenced locally.
.DS_Store
errors.log
"""


def make_search_html(index_text: str, domain: str, slug: str, site: str) -> str:
    """Build root search.html from the (already-transformed) home page."""
    text = index_text
    m = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    if m:
        text = text[:m.start()] + f"<title>{site or slug} · Search · Pandemic Religion</title>" + text[m.end():]
    # head assets
    text = text.replace("</head>", _PAGEFIND_HEAD + "</head>", 1)
    # swap the #content region for the Pagefind UI. Emits the *untagged*
    # #content open, so search.html itself is never indexed by Pagefind.
    before, sep, after = text.partition(_CONTENT_OPEN)
    if not sep:
        sys.exit("error: could not locate #content region while building "
                 "search.html (is the home page already tagged?)")
    _content, fsep, rest = after.partition("<footer")
    if not fsep:
        sys.exit("error: no <footer> after #content while building search.html")
    text = before + _CONTENT_OPEN + _SEARCH_UI + "</div>\n            " + fsep + rest
    # init script
    text = text.replace("</body>", _PAGEFIND_INIT + "</body>", 1)
    return text


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def detect_slug(out: Path) -> str:
    s = out / "s"
    if not s.is_dir():
        sys.exit(f"error: no s/ dir in {out} -- not an Omeka S capture?")
    dirs = [d.name for d in s.iterdir() if d.is_dir()]
    if len(dirs) != 1:
        sys.exit(f"error: expected exactly one slug dir under s/, found {dirs}")
    return dirs[0]


def copy_assets(out: Path, domain: str) -> None:
    """Land vendored assets: the footer logo, and the two Leaflet marker images
    wget missed (marker-icon-2x.png / marker-shadow.png are referenced only by
    the Mapping module's JS, never by CSS, so the crawler never fetched them --
    which left map markers invisible on retina displays)."""
    (out / "assets").mkdir(exist_ok=True)
    shutil.copy2(_ASSETS / "gmu-logo.png", out / "assets" / "gmu-logo.png")
    shutil.copy2(_ASSETS / "rrchnm_logo.png", out / "assets" / "rrchnm_logo.png")

    leaflet_imgs = out / "modules/Mapping/asset/vendor/leaflet/images"
    if leaflet_imgs.is_dir():
        for img in ("marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"):
            shutil.copy2(_ASSETS / "leaflet" / img, leaflet_imgs / img)
        print(f"[{domain}] added Leaflet marker images (maps)")


def flatten(src: Path, domain: str, out: Path, slug: str | None,
            keep_browse_controls: bool = False,
            banner_color: str | None = None, banner_accent: str | None = None,
            external: dict | None = None) -> None:
    external = external or {}
    print(f"[{domain}] copy {src} -> {out}")
    copy_tree(src, out, extra_ignore=list(external))   # drop external-slug dirs
    for sl in external:                                # + their site-home files
        (out / "s" / f"{sl}.html").unlink(missing_ok=True)
    if external:
        print(f"[{domain}] external slugs -> dedicated domains: "
              + ", ".join(f"{k}={v}" for k, v in external.items()))
    copy_assets(out, domain)

    slug = slug or detect_slug(out)
    print(f"[{domain}] slug = {slug}")

    # site name + palette for the archive banner (constant across the site).
    # Detect the name by comparing the home with a sample item (themes order the
    # <title> segments differently).
    home_raw = (out / "index.html").read_text(encoding="utf-8", errors="replace")
    itemdir = out / "s" / slug / "item"
    sample = next((f.read_text(encoding="utf-8", errors="replace")
                   for f in sorted(itemdir.glob("[0-9]*.html"))[:1]), "") if itemdir.is_dir() else ""
    name = detect_site_name(home_raw, sample)
    auto_primary, auto_accent = theme_colors(home_raw)
    primary = banner_color or auto_primary      # CLI override for themes whose
    accent = banner_accent or auto_accent       # palette isn't in the inline <style>
    print(f"[{domain}] banner: '{name}' primary={primary} accent={accent}")
    titles = build_item_titles(out, slug, name)   # for accessible image-link names

    pruned = prune_junk(out, keep_pagination=keep_browse_controls)
    print(f"[{domain}] pruned {len(pruned)} junk permutation file(s)"
          + (":" if pruned else ""))
    for p in pruned:
        print(f"           - {p}")

    index_text = None
    n_html = n_css = n_tagged = 0
    for p in sorted(out.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(out)
        rel_posix = rel.as_posix()
        if p.suffix == ".css":
            p.write_text(externalize_media(p.read_text(encoding="utf-8", errors="replace"),
                                           domain), encoding="utf-8")
            n_css += 1
            continue
        if p.suffix != ".html":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        text = strip_matomo(text)
        text = externalize_media(text, domain)
        text = rewire_search(text, domain, slug, _depth_prefix(rel))
        text = neutralize_forms(text, domain)
        text = replace_dead_forms(text)
        text = ensure_archive_statement(text)
        text = archive_contact_email(text)
        text = strip_contribute_ctas(text)
        if external:
            text = redirect_external_slugs(text, external)
        text = replace_footer(text, _depth_prefix(rel))
        if not keep_browse_controls:
            text = remove_browse_controls(text)
        text = fix_definition_lists(text)
        text = fix_link_names(text, titles)
        text = fix_images(text)
        text = fix_selects(text)
        text = add_archive_banner(text, name, primary, accent, _depth_prefix(rel))
        # Capture the home BEFORE tagging -- search.html is derived from it and
        # must stay untagged (never self-index).
        if rel_posix == "index.html":
            index_text = text
        if is_content_page(rel_posix):
            title = pagefind_title(text, name, is_home=(rel_posix == "index.html"))
            tagged = tag_pagefind_body(text, title)
            if tagged != text:
                n_tagged += 1
            text = tagged
        p.write_text(text, encoding="utf-8")
        n_html += 1

    print(f"[{domain}] transformed {n_html} html + {n_css} css; "
          f"tagged {n_tagged} content page(s) for Pagefind")

    if index_text is None:
        sys.exit(f"error: no index.html in {out}; cannot build search.html")
    (out / "search.html").write_text(make_search_html(index_text, domain, slug, name),
                                     encoding="utf-8")
    (out / "Dockerfile").write_text(_DOCKERFILE, encoding="utf-8")
    (out / ".gitignore").write_text(_GITIGNORE, encoding="utf-8")
    print(f"[{domain}] wrote search.html, Dockerfile, .gitignore")
    print(f"[{domain}] done. Next: gen-readmes.py README + `npx pagefind --site .`")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, help="wget capture dir")
    ap.add_argument("domain", help="live domain (== capture dir name)")
    ap.add_argument("out", type=Path, help="output static-site dir")
    ap.add_argument("--slug", help="Omeka S site slug (auto-detected from s/ if omitted)")
    ap.add_argument("--keep-browse-controls", action="store_true",
                    help="Keep the browse pagination/sort controls and the "
                         "default-sorted paginated browse pages (for sites whose "
                         "browse spans more than one page, e.g. collectingthesetimes).")
    ap.add_argument("--banner-color",
                    help="Archive-banner background (e.g. '#2436a1'); overrides "
                         "auto-detection for themes whose palette isn't inline.")
    ap.add_argument("--banner-accent", help="Archive-banner bottom-border color.")
    ap.add_argument("--external-slug", action="append", default=[], metavar="SLUG=DOMAIN",
                    help="On a multi-site install, drop this slug's pages and "
                         "point its links at DOMAIN (repeatable). E.g. "
                         "--external-slug preaching-goes-viral=preachinggoesviral.org")
    args = ap.parse_args()
    if not args.src.is_dir():
        sys.exit(f"error: src {args.src} is not a directory")
    external = {}
    for spec in args.external_slug:
        if "=" not in spec:
            sys.exit(f"error: --external-slug expects SLUG=DOMAIN, got {spec!r}")
        k, v = spec.split("=", 1)
        external[k] = v
    flatten(args.src, args.domain, args.out, args.slug,
            keep_browse_controls=args.keep_browse_controls,
            banner_color=args.banner_color, banner_accent=args.banner_accent,
            external=external)


if __name__ == "__main__":
    main()
