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


def copy_tree(src: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=_IGNORE)


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


def is_junk(name: str) -> bool:
    """True if an html basename is a prunable query-permutation file."""
    if "?" not in name:
        return False                       # real page (item/N.html, page/x.html)
    if _JUNK_RE.match(name):
        return True
    return any(s in name for s in _JUNK_SUBSTRINGS)


def prune_junk(out: Path) -> list[str]:
    pruned = []
    for p in sorted(out.rglob("*.html")):
        if is_junk(p.name):
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


def pagefind_title(text: str, is_home: bool) -> str:
    """Per-page result title for Pagefind.

    Every page's site chrome starts with an <h1>site name</h1>, which Pagefind
    would otherwise use as the title of *every* result. The document <title> is
    uniform ("<Site> · <Page> · Pandemic Religion"); take its middle segment as
    the real page title (the site name for the home page).
    """
    m = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    if not m:
        return ""
    parts = [p.strip() for p in m.group(1).split("·")]
    if is_home or len(parts) < 3:
        return parts[0] if parts else ""
    return " · ".join(parts[1:-1])


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


def make_search_html(index_text: str, domain: str, slug: str) -> str:
    """Build root search.html from the (already-transformed) home page."""
    text = index_text
    # title:  "<Site> · Home · Pandemic Religion" -> "<Site> · Search · ..."
    m = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    if m:
        parts = [p.strip() for p in m.group(1).split("·")]
        site = parts[0] if parts else slug
        text = text[:m.start()] + f"<title>{site} · Search · Pandemic Religion</title>" + text[m.end():]
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

    leaflet_imgs = out / "modules/Mapping/asset/vendor/leaflet/images"
    if leaflet_imgs.is_dir():
        for img in ("marker-icon.png", "marker-icon-2x.png", "marker-shadow.png"):
            shutil.copy2(_ASSETS / "leaflet" / img, leaflet_imgs / img)
        print(f"[{domain}] added Leaflet marker images (maps)")


def flatten(src: Path, domain: str, out: Path, slug: str | None) -> None:
    print(f"[{domain}] copy {src} -> {out}")
    copy_tree(src, out)
    copy_assets(out, domain)

    slug = slug or detect_slug(out)
    print(f"[{domain}] slug = {slug}")

    pruned = prune_junk(out)
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
        text = replace_footer(text, _depth_prefix(rel))
        text = remove_browse_controls(text)
        # Capture the home BEFORE tagging -- search.html is derived from it and
        # must stay untagged (never self-index).
        if rel_posix == "index.html":
            index_text = text
        if is_content_page(rel_posix):
            title = pagefind_title(text, is_home=(rel_posix == "index.html"))
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
    (out / "search.html").write_text(make_search_html(index_text, domain, slug),
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
    args = ap.parse_args()
    if not args.src.is_dir():
        sys.exit(f"error: src {args.src} is not a directory")
    flatten(args.src, args.domain, args.out, args.slug)


if __name__ == "__main__":
    main()
