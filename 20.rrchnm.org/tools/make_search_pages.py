#!/usr/bin/env python3
"""Generate the two Pagefind search pages from the archive's own chrome.

Both are derived from already-retrofitted pages rather than hand-maintained, so
they inherit the banner, nav, Matomo, footer and a11y stylesheet automatically
and cannot drift out of sync with the other 756 pages:

  search.html        <- index.html          (root depth, site-wide PagefindUI)
  items/search.html  <- items/browse.html   (depth 1, keeps the items-nav strip)

The #content region is emitted UNTAGGED, so neither search page is itself
indexed by Pagefind.

Run after tools/retrofit.py, and before `npx pagefind`:

    python3 tools/make_search_pages.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPEN_RE = re.compile(r'<main id="content"[^>]*>')
CLOSE = "</main><!-- end content -->"


def chrome(rel):
    """(head, tail) of a page, split at its #content region."""
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        s = fh.read()
    m = OPEN_RE.search(s)
    i = s.find(CLOSE)
    if not m or i < 0:
        sys.exit(f"error: could not locate the #content region in {rel}; "
                 "has tools/retrofit.py been run?")
    return s[:m.start()], s[i:]


def set_title(head, title):
    return re.sub(r"<title>.*?</title>", f"<title>{title}</title>", head,
                  count=1, flags=re.S)


def add_head_assets(head, prefix, extra=""):
    """Pagefind's stylesheet, loaded after a11y.css so the page can override it."""
    link = (f'<link href="{prefix}pagefind/pagefind-ui.css" media="all" '
            f'rel="stylesheet" type="text/css" >\n')
    return head.replace("</head>", link + extra + "</head>", 1)


# ---------------------------------------------------------------------------
# search.html -- site-wide, driven by the header search box
# ---------------------------------------------------------------------------

SEARCH_BODY = """<main id="content" tabindex="-1">
<div id="search-page">
    <h1>Search</h1>

    <noscript>
        <p>Search requires JavaScript to be enabled in your browser. You can
        still <a href="items/browse.html">browse all items</a>,
        <a href="exhibits.html">browse the exhibits</a>, or
        <a href="items/map.html">browse the map</a>.</p>
    </noscript>

    <p id="search-empty">Type a term in the search box above to search this site.</p>

    <div id="search"></div>
</div><!-- end search-page -->

"""

SEARCH_SCRIPT = """
<script src="pagefind/pagefind-ui.js"></script>
<script>
    /* The header search box is the single search field on this page: Pagefind's
       own input is visually hidden (see themes/a11y.css) and driven from here,
       so there are not two boxes competing. Same approach as the thanksroy and
       mallhistory archives. */
    (function () {
        function getParam(name) {
            return new URLSearchParams(window.location.search).get(name);
        }

        window.addEventListener('DOMContentLoaded', function () {
            new PagefindUI({
                element: '#search',
                showImages: false,
                showSubResults: true,
                pageSize: 10
            });

            var headerInput = document.getElementById('query');
            var emptyMsg = document.getElementById('search-empty');

            function pfInput() {
                return document.querySelector('#search .pagefind-ui__search-input');
            }

            /* Pagefind's own input is a visually hidden conduit -- the header
               box is the real control. Take it out of the tab order and out of
               the accessibility tree so screen-reader and keyboard users meet
               one search field, not an invisible second one whose only
               accessible name is a title attribute. */
            function hidePagefindInput() {
                ['.pagefind-ui__search-input', '.pagefind-ui__search-clear']
                    .forEach(function (sel) {
                        var el = document.querySelector('#search ' + sel);
                        if (el) {
                            el.setAttribute('aria-hidden', 'true');
                            el.setAttribute('tabindex', '-1');
                        }
                    });
            }

            function run(q) {
                var el = pfInput();
                if (!el) { return; }
                el.value = q;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                if (emptyMsg) { emptyMsg.style.display = q ? 'none' : ''; }
            }

            hidePagefindInput();
            // Pagefind re-renders its form as results arrive, so re-apply.
            if (window.MutationObserver) {
                new MutationObserver(hidePagefindInput)
                    .observe(document.getElementById('search'),
                             { childList: true, subtree: true });
            }

            var initial = getParam('query') || getParam('q') || '';
            if (headerInput) { headerInput.value = initial; }
            if (initial) { run(initial); }

            // Progressive enhancement: search as you type, keep the URL shareable.
            if (headerInput) {
                var t;
                headerInput.addEventListener('input', function () {
                    clearTimeout(t);
                    var v = headerInput.value;
                    t = setTimeout(function () {
                        run(v);
                        var url = new URL(window.location);
                        if (v) { url.searchParams.set('query', v); }
                        else { url.searchParams.delete('query'); }
                        window.history.replaceState(null, '', url);
                    }, 200);
                });
                var form = document.getElementById('search-form');
                if (form) {
                    form.addEventListener('submit', function (e) {
                        e.preventDefault();
                        run(headerInput.value);
                    });
                }
            }
        });
    })();
</script>
"""


def build_search():
    head, tail = chrome("index.html")
    head = set_title(head, "Search &middot; RRCHNM20")
    head = add_head_assets(head, "")
    tail = tail.replace("</body>", SEARCH_SCRIPT + "</body>", 1)
    return head + SEARCH_BODY + tail


# ---------------------------------------------------------------------------
# items/search.html -- faceted, on Pagefind's core API
# ---------------------------------------------------------------------------

ITEMS_NAV = """<nav class="items-nav navigation secondary-nav" aria-label="Items">
    <ul class="navigation">
    <li>
        <a href="browse.html">Browse All</a>
    </li>
    <li>
        <a href="tags.html">Browse by Tag</a>
    </li>
    <li class="active">
        <a href="search.html">Search Items</a>
    </li>
    <li>
        <a href="map.html">Browse Map</a>
    </li>
</ul></nav>"""

ITEMS_BODY = """<main id="content" tabindex="-1">
<h1>Search Items</h1>

""" + ITEMS_NAV + """

<div id="search-page">
    <noscript>
        <p>Search requires JavaScript to be enabled in your browser. You can
        still <a href="browse.html">browse all items</a> or
        <a href="map.html">browse the map</a>.</p>
    </noscript>

    <p id="search-intro">Type a term in the search box above, or narrow the
    archive with the filters below. Values within a filter combine: choosing two
    item types finds items that are either one.</p>

    <form id="facets" aria-label="Narrow these items">
        <div id="facet-groups"></div>
        <p><button type="button" id="facet-reset" class="button">Clear all filters</button></p>
    </form>

    <h2 id="results-heading">Results</h2>
    <p id="results-status" role="status" aria-live="polite">Loading the search index&hellip;</p>
    <ol id="results" class="items-list"></ol>
    <p id="results-more-wrap" hidden><button type="button" id="results-more" class="button">Show more items</button></p>
</div><!-- end search-page -->

"""

ITEMS_SCRIPT = r"""
<script type="module">
    /* Replaces Omeka's "Advanced Search (Items only)" form, whose action wget
       could not preserve: it submitted a query string the static server ignores,
       so it always returned unfiltered page 1 -- a fully labelled control that
       silently did nothing.

       Built on Pagefind's core API rather than its Default UI, because the
       Default UI only renders its filter panel once a query has been typed,
       which would leave this page blank on arrival -- the opposite of what an
       advanced search form is for. The core API also supports
       search(null, {filters}), i.e. filter-only browsing with no keyword. */
    const PAGE = 20;

    const state = {};          // { "Item Type": Set(...), Collection: Set(...) }
    let pagefind = null, results = [], shown = 0, universe = {};

    const $ = (id) => document.getElementById(id);

    /* This page is the Items section's search, so it is pinned to the 422
       item pages -- without this it would also return the home page, the two
       About pages, the exhibits and the collections, which are not items and
       carry none of the facets below. retrofit.py stamps the Record value on
       every indexed page; search.html deliberately leaves it unset. */
    const SCOPE = { Record: { any: ['Item'] } };
    const HIDDEN = new Set(['Record']);

    function selectedFilters() {
        // Wrap every group in `any`. Handing Pagefind a bare array means AND --
        // {'Item Type': ['Person','Project']} asks for items that are both,
        // which is always empty. The old Omeka form ORed within a field too.
        const out = Object.assign({}, SCOPE);
        for (const [group, values] of Object.entries(state)) {
            if (values.size) { out[group] = { any: [...values] }; }
        }
        return out;
    }

    function readUrlFilters() {
        /* ?filter=Group:Value, repeatable. The People nav link on every page
           points here as ?filter=Item+Type:Person. */
        const params = new URLSearchParams(window.location.search);
        for (const raw of params.getAll('filter')) {
            const i = raw.indexOf(':');
            if (i < 0) { continue; }
            const group = raw.slice(0, i).trim();
            const value = raw.slice(i + 1).trim();
            if (!group || !value) { continue; }
            (state[group] = state[group] || new Set()).add(value);
        }
        return params.get('query') || params.get('q') || '';
    }

    function writeUrl(query) {
        const url = new URL(window.location);
        url.searchParams.delete('filter');
        for (const [group, values] of Object.entries(state)) {
            for (const v of values) { url.searchParams.append('filter', group + ':' + v); }
        }
        if (query) { url.searchParams.set('query', query); }
        else { url.searchParams.delete('query'); }
        window.history.replaceState(null, '', url);
    }

    function renderFacets(counts) {
        /* The value LIST comes from the full universe, never from the current
           result set: values inside one group are OR-ed, so ticking "Person"
           must not make "Project" vanish -- ticking it too would widen the
           results, not narrow them. The COUNTS come from Pagefind's
           totalFilters, which reports each value as if its own group were not
           yet applied, i.e. how many items ticking it would add. */
        const wrap = $('facet-groups');
        wrap.textContent = '';
        for (const group of Object.keys(universe).sort()) {
            if (HIDDEN.has(group)) { continue; }
            const values = counts[group] || {};
            const names = Object.keys(universe[group]).sort();
            if (!names.length) { continue; }
            const fs = document.createElement('fieldset');
            fs.className = 'facet-group';
            const lg = document.createElement('legend');
            lg.textContent = group;
            fs.appendChild(lg);
            for (const name of names) {
                const id = 'facet-' + group.replace(/\W+/g, '-') + '-' +
                           name.replace(/\W+/g, '-');
                const label = document.createElement('label');
                label.className = 'facet-value';
                label.htmlFor = id;
                const box = document.createElement('input');
                box.type = 'checkbox';
                box.id = id;
                box.checked = !!(state[group] && state[group].has(name));
                box.addEventListener('change', () => {
                    const set = state[group] = state[group] || new Set();
                    if (box.checked) { set.add(name); } else { set.delete(name); }
                    if (!set.size) { delete state[group]; }
                    search();
                });
                label.appendChild(box);
                label.appendChild(document.createTextNode(
                    ' ' + name + ' (' + (values[name] || 0) + ')'));
                fs.appendChild(label);
            }
            wrap.appendChild(fs);
        }
    }

    function renderPage() {
        const list = $('results');
        const slice = results.slice(shown, shown + PAGE);
        Promise.all(slice.map((r) => r.data())).then((data) => {
            for (const d of data) {
                const li = document.createElement('li');
                li.className = 'item record';
                const h3 = document.createElement('h3');
                const a = document.createElement('a');
                a.href = d.url;
                a.textContent = d.meta && d.meta.title ? d.meta.title : d.url;
                h3.appendChild(a);
                li.appendChild(h3);
                if (d.excerpt) {
                    const p = document.createElement('p');
                    p.className = 'item-description';
                    // Pagefind escapes the excerpt itself and adds <mark>.
                    p.innerHTML = d.excerpt;
                    li.appendChild(p);
                }
                list.appendChild(li);
            }
            shown += slice.length;
            $('results-more-wrap').hidden = shown >= results.length;
        });
    }

    async function facetCounts(q) {
        /* One query per group, with that group's OWN selections removed, so a
           value's count answers "how many items would ticking this show?".
           r.filters alone cannot: with Person ticked it reports Project as 0,
           because no item is both -- true, but misleading when values inside a
           group are OR-ed. Pagefind's totalFilters is meant for exactly this
           but returns all zeros for a filter-only (null) query, so it cannot be
           relied on here. Two groups, two extra searches -- negligible over a
           494-page index. */
        const out = {};
        for (const group of Object.keys(universe)) {
            if (HIDDEN.has(group)) { continue; }
            const f = selectedFilters();
            delete f[group];
            const r = await pagefind.search(q || null, { filters: f });
            out[group] = r.filters[group] || {};
        }
        return out;
    }

    function search() {
        if (!pagefind) { return; }
        const q = $('query') ? $('query').value.trim() : '';
        writeUrl(q);
        $('results-status').textContent = 'Searching…';
        pagefind.search(q || null, { filters: selectedFilters() }).then(async (r) => {
            results = r.results;
            shown = 0;
            $('results').textContent = '';
            $('results-status').textContent = results.length === 1
                ? '1 item' : results.length + ' items';
            renderFacets(await facetCounts(q));
            renderPage();
        });
    }

    window.addEventListener('DOMContentLoaded', () => {
        const initial = readUrlFilters();
        const header = $('query');
        if (header && initial) { header.value = initial; }

        import('../pagefind/pagefind.js').then(async (pf) => {
            await pf.options({ excerptLength: 30 });
            await pf.init();
            pagefind = pf;
            // Seed the panel with every value, so the facets are on screen
            // before anything is typed -- the Default UI only draws its filter
            // panel after a query, which is the opposite of what an advanced
            // search page is for.
            universe = await pf.filters();
            renderFacets(universe);
            search();
        }).catch(() => {
            $('results-status').textContent =
                'The search index could not be loaded.';
        });

        if (header) {
            let t;
            header.addEventListener('input', () => {
                clearTimeout(t);
                t = setTimeout(search, 200);
            });
        }
        const form = $('search-form');
        if (form) {
            form.addEventListener('submit', (e) => { e.preventDefault(); search(); });
        }
        $('facet-reset').addEventListener('click', () => {
            for (const k of Object.keys(state)) { delete state[k]; }
            search();
        });
        $('results-more').addEventListener('click', renderPage);
    });
</script>
"""


def build_items_search():
    head, tail = chrome("items/browse.html")
    head = set_title(head, "Search Items &middot; RRCHNM20")
    head = add_head_assets(head, "../")
    # The advanced-search page's own body class, matching what Omeka emitted.
    head = re.sub(r'<body class="theme-berlin items browse">',
                  '<body class="theme-berlin items advanced-search">', head)
    tail = tail.replace("</body>", ITEMS_SCRIPT + "</body>", 1)
    return head + ITEMS_BODY + tail


# ---------------------------------------------------------------------------
# the 63 dead items/search?... captures
# ---------------------------------------------------------------------------

STUB = """<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<title>Search Items &middot; RRCHNM20</title>
<link rel="canonical" href="/items/search.html">
<meta http-equiv="refresh" content="0; url=/items/search.html">
</head>
<body>
<p>This page has moved to <a href="/items/search.html">Search Items</a>.</p>
</body>
</html>
"""


def write_stubs():
    """Omeka's advanced search produced 63 paginated result captures. They are
    inert -- every one is a duplicate of the unfiltered browse listing -- and
    they gave 64 pages the same <title>. Redirect rather than delete, so any
    inbound link still lands somewhere."""
    d = os.path.join(ROOT, "items")
    n = 0
    for name in sorted(os.listdir(d)):
        if name.startswith("search?") and name.endswith(".html"):
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(STUB)
            n += 1
    return n


def main():
    for rel, build in (("search.html", build_search),
                       (os.path.join("items", "search.html"), build_items_search)):
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
            fh.write(build())
        print(f"wrote {rel}")
    print(f"wrote {write_stubs()} redirect stubs for items/search?*.html")


if __name__ == "__main__":
    main()
