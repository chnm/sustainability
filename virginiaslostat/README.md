# virginiaslostat.org

*Virginia's Lost AT* — the 300 miles of Appalachian Trail that ran along the
Blue Ridge escarpment, the Dan River Gorge and the Iron Mountains until the
route moved 50 miles west in 1952.

## Retrofit

The crawled mirror still behaved like a live Omeka site. Its centrepiece — a
3 MB R `leaflet` map of the old route — did not render at all; the "Map" page
drew an empty basemap because its markers came over AJAX from an endpoint a
static host does not have; the advanced item search silently discarded every
field you filled in; every image pointed at the origin; the theme fetched its
type and its JavaScript from Google on each page view; and the footer credited
Omeka. This directory is the result of fixing that, and holds only what gets
served.

The transformations were made by a set of one-off scripts that are **not kept
here** — this repository is deployment artifacts, and `context_root` is copied
to the web root wholesale, so anything else in this directory would be served
publicly. What they did is recorded below, in enough detail to redo it. They
were idempotent and each took a `--check` flag, so a second run left `git diff`
empty; the archive as committed is a fixed point.

Their order mattered in three places, which is worth knowing before repeating
any of it. The origin data had to come first, because everything downstream
would otherwise emit dead links. The two search pages were built by lifting the
head and body chrome off an already-transformed page — `about.html` for the
root one and `items/browse.html` for the one a level down, chosen so every
relative path in the chrome was already correct — so that the header,
navigation, footer and Matomo block could not drift from the other 190. And the
Pagefind index was built last, because it indexes the HTML as committed.

| what | where |
|---|---|
| Static search | `pagefind/` (committed — the deploy only copies files), `pagefind.yml`, `themes/search.js`, `search.html`, `items/search.html` |
| Accessibility | `themes/a11y.css`, plus the markup itself |
| Interactive map | `at_interactive_map.html` (repaired) |
| Map data | `geolocation/map.kml` — the one geolocated item |
| Basemap | `basemap/protomaps-basemap.pmtiles` + `protomaps-leaflet` — self-hosted OSM vector tiles, replacing Esri and CARTO |
| Fonts | `themes/.../css/fonts.css` + `fonts/*.woff2` — Ubuntu, Enriqueta, Oswald |
| Media | referenced as `/files/…`; the objects themselves live in the bucket |
| URL repair | `redirects.caddy` |

### The interactive map

The homepage and `interactivemap.html` embed `at_interactive_map.html`, an R
`leaflet` htmlwidget. **It was completely dead.** Its marker data is a JSON
payload in a `<script type="application/json">` block, and
`wget --convert-links` found the escaped `href=`/`src=` attributes inside that
JSON's popup HTML, resolved them as if they were real links, and wrote them back
wrapped in *unescaped* double quotes — which closes the JSON string early. The
committed copy fails `JSON.parse` at byte 2,344,196, so htmlwidgets never
initialised and both pages showed a white box. This is the same wget failure
mode that killed mallhistory's four scavenger-hunt maps, but here it took the
whole map.

It is not repairable from the crawl alone: six of the 87 popups were malformed
*at source* — two with an unterminated `src` (one of which also ate the `t` of
`title=`), one with a curly `”` where the closing quote of `href` belongs, one
with a stray space inside `href`, and two running `target="_blank"class=` — so
no single substitution reconstructs the original. The origin's pristine copy
was fetched instead, while the origin was still up, and all 87 popups rebuilt
from their extracted fields — which fixes those six as a side effect: two had a
broken image and one a broken link on the live site too.

The basemap changed too. The widget asked for two **Esri** raster
layers — `WorldShadedRelief` with `WorldImagery` over it at 50% — and gave its
inset MiniMap OpenStreetMap over plain `http://`, which an HTTPS archive blocks
as mixed content, so that inset had been an empty box for years. Both now draw
from the archive's own Protomaps tiles. **This is a visible change**: the shaded
relief and the aerial imagery are gone, and a vector basemap cannot reproduce
them. The trade was deliberate — Esri's basemaps are a licensed product, and an
archive nobody is watching should not depend on one. The widget's own content
(the 1931/1941/current trail polylines, the county boundaries, the 87 markers)
is vector data drawn by Leaflet and is unaffected.

Two smaller repairs there: Leaflet could not find its own marker images (the
widget inlines its stylesheet as a `data:` URI, so Leaflet's detection fails and
the R package hardcodes `http://cdn.leafletjs.com/leaflet/v1.3.1/images/`, a
host that no longer resolves), so all 87 pins were broken images; and the widget
passed `alt: ""` for every marker, so tabbing the map hit 87 focusable stops
that announced nothing. Pins now come from `plugins/Geolocation/…/leaflet/images/`
and each is named from its own popup title.

### Basemap

Three more pages draw an Omeka Geolocation map — `geolocation/map/browse.html`
and the two copies of item 53 — and those used `CartoDB.Voyager`. CARTO's
basemaps are *"available exclusively with an Enterprise license"*, so the
archive was leaning on a service it probably was not licensed for.

Everything is drawn from `basemap/protomaps-basemap.pmtiles` now: a single
31 MB file of OpenStreetMap-derived vector tiles (ODbL) read straight out of
static storage with HTTP range requests. No API key, no account, no vendor. See
`basemap/PROVENANCE.txt` for exactly how it was built, including the go-pmtiles
crash it has to be retried around.

It carries **the world at z0–5 and the trail corridor at z6–11**, merged into
one archive, because this site needs both: the browse map opens at z5 over a
whole-mid-Atlantic view and the interactive map's MiniMap runs five zoom levels
below the main map, while the argument the site is making — where the trail ran
through Floyd, Carroll, Grayson and Patrick counties — is only legible at z10–11.
The one geolocated item was authored at z18, which no archive of a sane size can
carry, so `map.js` caps the controls at 13, two levels past the data.

**A local preview needs a server that honours HTTP `Range`.**
`python3 -m http.server` ignores it and returns the whole 31 MB archive for
every tile request, so the basemap silently fails to draw against it. Behind
Caddy on the deployed host this is a non-issue.

### Static search

The site shipped with **no search box at all**: Omeka rendered nothing into the
two empty `<li>` the theme left in `.top-bar-right`, so the only route to search
was a "Search Items" tab on the Archive page — and that page's form was worse
than dead, because `wget --convert-links` rewrote its `action` to `browse.html`,
so submitting it silently reloaded an unfiltered browse listing.

Both are re-implemented client-side with [Pagefind](https://pagefind.app):

- **`search.html`** — site-wide, reading `?query=`, the field name Omeka's own
  `/search` used, so old links of that shape still work.
- **`items/search.html`** — the advanced item search, with **Format**,
  **Creator** and **Tag** facets and filter-only browsing (leave the keyword box
  empty and tick a facet). It also answers to `?tags=`, the field name the old
  advanced form used.
- **A search form in the header of every other page**, in the slot the theme
  had left empty.
- `pagefind/` — the prebuilt index, committed, so the site stays a pure static
  deploy with no build step.

Both pages are built on Pagefind's **core API** rather than its Default UI. The
Default UI renders its own input, which would be a second search box on a page
whose header already has one — the sibling archives work around that by hiding
Pagefind's input and driving it from the header, leaving an invisible control in
the DOM — and it only draws its filter panel once a keyword has been typed,
which would leave an advanced-search page blank on arrival. The core API takes
`search(null, {filters})`, so filters alone are a valid query.

**Index scope.** 103 canonical content pages: the 76 items, the 23 exhibit pages
and `index`/`about`/`teaching-case-studies`/`interactivemap`. The 74
`items/browse…` captures, `items/tags.html`, the map browse page and the 12
`exhibits/show/history/item/N.html` pages are pagination, facet views or
exhibit-scoped restatements of content indexed elsewhere.

**Facet values ride on `data-` attributes**, not on the elements that display
them, so they can be normalised without touching what the page shows — the
origin's Format values run to 13 spellings of 9 formats ("Black and White
Photograph" beside "Black and white photograph", plus one "Color photograh") and
would otherwise split into near-duplicate buckets. Worth recording, because
`thanksroy/README.md` reports the opposite: that Pagefind 1.5.2 silently yields
an empty value for the documented `Name[attr]` form. That does not reproduce —
verified against 1.5.2 with `span` + `data-*`, and the facets here are built on
it.

### Accessibility (WCAG 2.2 AA)

The archive was a raw crawl with no remediation. Verified with **axe-core**
(`wcag2a`/`2aa`/`21a`/`21aa`/`22aa`) → **0 violations** across 23 pages, one per
structural variant, plus a keyboard pass and a reflow pass at 320px and 375px,
all driven through real headless Chromium — jsdom cannot compute colour contrast
or target size, cannot run Pagefind's WebAssembly index, and cannot render
Leaflet, so the pages that matter most here would audit as empty shells.

- **Landmarks (1.3.1)**: the theme's `<header>` was *empty* — the site title and
  the whole navigation sat outside it as bare siblings — and there was no
  `<main>` or `<footer>` anywhere. The title and nav are inside `<header>` now,
  `#primary` is a `<main>`, the two footer `<div>`s are one `<footer>`, and
  every nav is named.
- **Bypass blocks (2.4.1)**: no page had a skip link, and every page opens with
  eight tab stops before the content.
- **Duplicate ids (4.1.1)**: `id="footer"` on all 191 pages, `id="pagination-next"`
  on 88, `id="primary"` on 3. The last also meant `#primary`'s 50px padding
  applied twice, so those pages were indented 100px against the rest.
- **Headings (1.3.1)**: item pages ran `h1 → h4`, skipping two levels; the 11
  metadata labels are `h2` now, sized by `.element-label` to render exactly as
  the `h4` did. The site title is a `<p>` on the 189 pages that have a real
  content heading, so each page has one `h1`. The homepage's lead paragraph was
  an `<h4>` inside a `<p>`.
- **Contrast (1.4.3)**: the site title and the navigation sit directly on a
  background photograph — `.tinted-image`, the class on the title's column, has
  no CSS anywhere, so nothing was ever tinted. Sampling the actual pixels behind
  the text at 1280px, the darkest trunk under the nav gives 4.07:1 for the
  resting link and **2.42:1 for hover**. A scrim plus restoring app.css's own
  `.top-bar li a:hover` colour (which the theme's blanket
  `a:hover … !important` was overriding) takes both past 6:1. Separately,
  Foundation's `h1 small { color: #cacaca }` — the item count on every browse
  page — was 1.63:1.
- **Use of colour (1.4.1)**: links in prose are `#9c4d23` with no underline,
  which is only 2.96:1 against the surrounding body text. Underlines are
  restored in running text; lists of links are left alone.
- **Reflow (1.4.10)**: the map was embedded as a fixed
  `<iframe width="1000">`, and at 72px the word "Virginia's" in the site title
  is 331px wide. No page scrolls horizontally at 320px now.
- **Names (1.1.1, 2.4.4, 4.1.2)**: the mobile menu button was an empty
  `<button>`, so below 40em the only route to the navigation announced as
  "button". Browse listings render each item twice — a title link and a
  thumbnail link to the same page — and the thumbnail's accessible name was the
  image's `alt`, a filename; those are hidden from assistive technology now, and
  the download link on item pages is named from the item title. The two footer
  wordmarks carried their own content hashes as `alt`.
- **Target size (2.5.8)**, **focus visible (2.4.7)**: in `themes/a11y.css`.
- WCAG 2.2's other AA additions are satisfied without change and were confirmed:
  2.4.11 Focus Not Obscured (nothing is `position: fixed`/`sticky`), 2.5.7
  Dragging Movements and 3.3.8 Accessible Authentication (neither exists here),
  3.2.6 Consistent Help and 3.3.7 Redundant Entry (no help mechanism, no
  multi-step flows).

**Outstanding — alt text (1.1.1).** Most `alt` values are filenames
(`alt="Dixons Ferry.jpg"`). Every `<img>` *has* an `alt`, so axe reports zero
`image-alt` violations and the archive still fails 1.1.1 in substance.
Descriptive alt text is a **deferred follow-up** — a curatorial pass, not
something a script can invent.

### Chrome

- The **"Proudly Powered by Omeka" footer credit** is replaced by the **GMU
  Department of History and Art History** logo, following commit `83180e5d9b`
  and the `20.rrchnm.org` archive. The COinS citation metadata and any Omeka
  mentions inside archived content are untouched.
- The **RRCHNM and Virginia Humanities wordmarks** in the footer were hot-linked
  from `virginiaslostat.org/files/original/` — the origin, and the crawl's
  excluded media directory, so they would have broken twice over. They are
  committed under `assets/` with real alt text.

### Robustness

Nothing outside the archive is fetched any more except Matomo. Verified in a
browser with every other third-party host blocked.

- **Three Google Fonts families are self-hosted**, by two different routes and
  the second is easy to miss: `<link>` tags in every `<head>` for **Ubuntu**,
  and an `@import` at `foundation.css:17` for **Enriqueta** and **Oswald** —
  the theme's actual body and heading faces, which no HTML file mentions. With
  Google unreachable the whole site fell back to Helvetica.
  The `@font-face` blocks in `themes/.../css/fonts.css` are Google's own,
  taken verbatim from the stylesheets it returns for the two family requests
  this theme made, so nothing is hand-transcribed.
- **Font Awesome 4.7 is vendored** (`application/views/scripts/css/`). Every
  page loaded it from `maxcdn.bootstrapcdn.com` for 1,306 decorative icons,
  which now also carry `aria-hidden`.
- **jQuery 3.6.0 and jQuery UI 1.12.1 are vendored.** Every page loaded them
  from `ajax.googleapis.com` with a `document.write` fallback — but neither
  fallback could ever have worked: one pointed at a file the crawl never
  downloaded, the other at `…/jquery.js?v=3.0.1`, where the `?v=` is a real
  query string to a web server but part of the *filename* on disk. A blocked CDN
  therefore left `jQuery` undefined, taking the Foundation menu, both map types
  and the advanced-search form with it.
- **`</body>` and `</html>` are closed.** Omeka's footer template ended at the
  last `</div>`, so all 191 pages simply stopped. Browsers recover, which is why
  nobody noticed.
- The RSS/Atom `<link rel="alternate">` to the origin are gone.
  `leaflet-providers.js` is no longer loaded by any page (kept in the tree, as
  `20.rrchnm.org` keeps its copy).

### Analytics

Matomo, site id **12**, at `https://stats.rrchnm.org/`. All 191 crawled pages
already carried it, in the older Omeka-emitted shape with a protocol-relative
`//stats.rrchnm.org/` that would speak plain http to an http visitor; they are
normalised to one identical modern block, and the two generated search pages
inherit it with the rest of the chrome.

`at_interactive_map.html` deliberately does **not** carry Matomo: it is an
iframe payload on two pages that do, and tracking it would double-count every
homepage visit.

### Redirects

`redirects.caddy` repairs the extensionless URLs the export renamed
(`/items/show/53` → `/items/show/53.html`), plus two query-carrying cases the
generic rule would otherwise swallow: `/search?query=…`, the old Omeka endpoint,
and `/items/browse?tags=…`, which lands on the faceted item search with the tag
already applied. Every rule was checked with `caddy validate` and exercised
against a running Caddy 2.10.2.

### Deployment note

The archive must be served **at a domain root**. The footer wordmarks, the
basemap, the Protomaps renderer, the `/files/` media and every Pagefind result
link are root-absolute, as they are on the sibling archives. It is at `valostat.dev.chnm.gmu.edu` for development and
`virginiaslostat.org` in production — the archive takes over the origin's own
domain.

That last point makes one thing work that would otherwise be a loose end: the
`<span class="citation-url">` permalink on each item page still reads
`https://virginiaslostat.org/items/show/10`, which is what a citation printed
before the migration should keep saying. Served at that domain, and with
`redirects.caddy` in front, those citations resolve again — the extensionless
URL 301s to `/items/show/10.html`. Nothing in the archive *fetches* from that
host; the references are text, and every `href`, `src` and `action` is
relative.

### Media

The 317 objects under `files/{original,fullsize,thumbnails,square_thumbnails}`
(78.9 MB) were excluded at crawl time and are **not in this repo** (`.gitignore`
blocks all four). They were fetched from the origin into a staging tree outside
this repository, with a `manifest.tsv` recording each object's URL, size and
sha256, for loading into the object bucket.

Until the bucket and the web server's `/files/` redirect are live on the
deployed host, every item image 404s — they previously rendered only by
hot-linking the origin. Check with:

```sh
curl -sIL https://valostat.dev.chnm.gmu.edu/files/thumbnails/85c6fcf497da7379b936ef7473d0a706.jpg
```

They 404 under a local preview too, which is expected — the accessibility audit
blocks the bucket host rather than treating a missing object as a regression.

### Known gaps

- **Alt text** — see the accessibility section above.
- **The Esri shaded relief and aerial imagery are gone** from the interactive
  map — see above. Nothing else about that map changed.
- Above z11 the basemap over-zooms: lines stay sharp, no new detail appears.
  Panning the browse map outside the trail corridor at z6+ shows no basemap at
  all; the interactive map cannot be panned out of the corridor, because the
  widget's own `setMaxBounds` sits inside the extract.
- **Search recall is bounded by the data.** Only 2,918 words are indexed across
  103 pages: most items are a photograph with a two-sentence description.
- The theme's `#site-title` is set in Ubuntu by `app.css` overriding
  Foundation's Oswald for headings — worth knowing before editing
  `themes/a11y.css`, which has to restate it for the demoted `<p>` version.

## wget

Crawled by `multi-wget.py` on 2026-05-28.

**Seed:** `https://virginiaslostat.org/`

**Run**

- started:   2026-05-28 16:47:24
- finished:  2026-05-28 16:49:29
- duration:  124s (wrapper) · 2m 4s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 212 files, 6.8M (9.85 MB/s)
- links converted: 199 files in 0.09s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 212 | 4 | 1 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (1)

| status | url |
|--------|-----|
| 404 | https://virginiaslostat.org/%5C%22https://virginiaslostat.org/items/show/53%E2%80%9D |

That 404 is the crawler following the curly-quote typo in the interactive map's
popup for item 53 — the same one the interactive-map repair fixes.

### Excluded (2703)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 471 |
| LIST | `/files/fullsize` | 110 |
| LIST | `/files/square_thumbnails` | 343 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 1182 |
| REGEX | 597 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).

## Surviving absolute URLs to dead origin

In-tree HTML scan at crawl time (2026-05-28). `--convert-links` only rewrites
refs to files wget actually downloaded — anything filtered stayed as the
absolute origin URL and would 404 once the live site is gone.

| attr    | at crawl | after retrofit |
| ------- | -------: | -------------: |
| `src=`  |   912 | 0 |
| `href=` |   628 | 0 |

**Top broken path prefixes, at crawl time**

| count | prefix                       |
| ----: | ---------------------------- |
|   479 | `files/original/`            |
|   343 | `files/square_thumbnails/`   |
|   340 | `items/`                     |
|   112 | `files/fullsize/`            |
|    75 | `\&quot;/items/show/`        |

No `href`, `src` or `action` anywhere in the archive now resolves to
`virginiaslostat.org`. The 88 plain-text mentions that remain are the
`<span class="citation-url">` permalinks on item pages, which are what a
citation printed before the migration should keep saying, and are not fetched.
