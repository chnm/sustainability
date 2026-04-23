# occupyarchive.org — Static Mirror

Self-contained static mirror of the Omeka Classic 1.4.2 site at
`occupyarchive.org`, served by a single Caddy container. This repo
holds the post-processed HTML, Pagefind search index source, JSON data
snapshots, and the Dockerfile. The ~2.3 GB of binary media lives
**outside this repo** — see [Archive storage](#archive-storage) below.

## Archive storage

The `archive/` directory (images, audio, video, zips, PDFs — ~2.3 GB
across ~4,500 files) is **not tracked in git** (`.gitignore`d). It's
hosted separately in an S3-compatible bucket and provided to the
Caddy container at build or run time.

Contents:

| Subdir | Files | Size | Purpose |
|---|---|---|---|
| `archive/files/` | 2,491 | 2.1 GB | originals (jpg, pdf, mp3, mp4, zip, …) |
| `archive/fullsize/` | 981 | 181 MB | image derivative — display size |
| `archive/square_thumbnails/` | 981 | 25 MB | image derivative — listing thumbnails |
| `archive/theme_uploads/` | 1 | <1 MB | site logo |

Omeka's proportional `archive/thumbnails/` derivative is intentionally
omitted — the theme uses `square_thumbnails/` exclusively.

### Supplying `archive/` to a running image

Two supported patterns:

**A. Fetch at image build time from S3 / R2 / object store.**
Extend the Dockerfile with a build-arg and a single tarball fetch
after the `COPY . /srv` line:

```dockerfile
ARG ARCHIVE_URL
RUN curl -fsSL "$ARCHIVE_URL" | tar -xz -C /srv
```

Bucket layout: a single `archive.tar.gz` at the bucket root, or
shard by subdirectory (`files.tar.gz`, `fullsize.tar.gz`,
`square_thumbnails.tar.gz`, `theme_uploads.tar.gz`) if uploads need
to stay under per-object limits.

**B. Bind-mount at runtime.** Keep the image lean (~250 MB) and
mount the archive at container start:

```bash
docker run --rm -p 8080:80 \
  -v /path/to/archive:/srv/archive:ro \
  occupyarchive-static
```

Caddy serves `/archive/*` with a year-long immutable cache header, so
either pattern behaves identically to the client.

### Integrity

All 4,454 files on disk are referenced by HTML or `data/files.json`,
and every reference resolves — `archive/` is in sync with the rest
of the static site. Keep it that way if you regenerate it from the
Omeka source.

## Outcomes at a glance

| Artifact | Count / Size |
|---|---|
| Static HTML pages | 8,327 |
| Item show pages | 3,528 |
| Type-filtered browse pages restored | 141 (5 landings + 136 paginated) |
| Collection-filtered browse pages restored | 298 (202 landings + 96 paginated) |
| Tag-cloud anchors restored on `/items/tags.html` | 1,824 |
| Pages with search form injected | 8,327 |
| Pages stripped of Google Analytics | 8,327 |
| Pages stripped of FakeCron (external + inline) | 8,327 |
| Pagefind index | 37 MB, 8,325 pages, 40,462 words, 3 filters |
| Featured-item randomizer pool | 11 items |
| Map pins (GeoJSON) | 79 (from 88 rows in `omeka_locations`) |
| Archive media (sidecar, not in repo) | 4,454 files, ~2.3 GB |
| Serve image base | `stagex/user-caddy` |

## Upstream source tree

Raw inputs live in a sibling directory, **not in this repo**:

```
occupyarchive.org_omeka/        INPUT    — Omeka source, SQL dump, build/
occupyarchive.org_wget/         RAW      — wget --mirror output
occupyarchive.org_static/       ARTIFACT — this repo's contents
```

All build tooling (`postprocess.py`, `inject_pagefind.py`, …) lives
under `occupyarchive.org_omeka/build/`. Those scripts generated the
HTML in this repo; they aren't needed to build or serve the static
mirror, only to regenerate it from an updated SQL dump or wget crawl.

## Build scripts

All scripts are idempotent and safe to re-run.

| Script | Purpose |
|---|---|
| `postprocess.py` | (pre-existing) `_wget/` → `_static/`: link rewrite, form strip. |
| `inject_pagefind.py` | Swap the Omeka search form for a GET-form pointing at `/search.html`; generate `/search.html` from `index.html` with a Pagefind UI mount that reads `?q=` from the URL. |
| `rescue_type_filters.py` | Recover 141 `?type=N` filtered browse pages that `postprocess.py` dropped; rename into a clean URL scheme; fix nav. |
| `rescue_collection_filters.py` | Same shape as the type rescue, but for `?collection=N`; recovers 298 pages and patches `collections/show/*` hrefs. |
| `rescue_tag_cloud.py` | Re-inject the 1,824 anchors on `/items/tags.html` that `postprocess.py` stripped; rewrite hrefs from the dropped `?tags=X` scheme to the slug-based `/items/browse/tag/X.html` canonical URLs. |
| `generate_featured.py` | Extract `featured=1 AND public=1` items from SQL → `featured-pool.json`; inject a small randomizer script into `index.html`. |
| `generate_map.py` | Replace the broken Omeka Geolocation + Google Maps v3 page with Leaflet + OSM, fed from a static `data/geodata.geojson`. |
| `strip_ga.py` | Remove the baked-in Google Analytics `<script>` block (UA-3026200-6). Matomo (rrchnm) left intact. |
| `strip_fakecron.py` | Remove both the external `fakecron.js` `<script src>` and the inline `var FakeCron = {}` config block. |

## Work completed

### 1. Caddy serve image (`Dockerfile`)

Two-stage image on `stagex/user-caddy`. Stage 1 (Node) rebuilds the
Pagefind index from `data/items.json` via `pagefind_index.mjs`.
Stage 2 (Caddy) ships the static site.

- `COPY . /srv` with `.dockerignore` excluding `archive/`, `pagefind/`,
  `Dockerfile`, `.git`, etc. The freshly built Pagefind index is
  overlaid from stage 1.
- `COPY --from=stagex/core-musl / /` provides runtime libs.
- Caddyfile:
  - `auto_https off`, `admin off`, `:80`.
  - `try_files {path} {path}.html` — handles extensionless URLs (e.g. `/items/show/1000` → `items/show/1000.html`, `/items/browse/type/6/page/100` → `.../page/100.html`). `file_server`'s default `index` directive serves `index.html` for directory requests natively, so no third fallback arm is needed.
  - Long-cache `public, max-age=31536000, immutable` for `/archive/*`, `/pagefind/*`, `/themes/*`.
  - `encode gzip zstd` — Pagefind `.pagefind` shards are pre-compressed and skipped by Caddy's default MIME detection.

Build + run (archive bind-mounted; see [Archive storage](#archive-storage)
for the S3-fetch alternative):

```bash
docker build -t occupyarchive-static .
docker run --rm -p 8080:80 -v /path/to/archive:/srv/archive:ro occupyarchive-static
```

### 2. Client-side search (Pagefind)

Chose Pagefind (Rust-built indexer + WASM runtime) over alternatives
(MiniSearch, Fuse.js, Stork, Tinysearch, SQLite-WASM). Reasons:
sharded index loads only shards needed per query, actively
maintained, no ongoing maintenance cost for a frozen archive.

**Index build** (run from the directory containing this repo):

```bash
npx -y pagefind@latest --site occupyarchive
```

Or, in the Docker build, stage 1 runs `node pagefind_index.mjs` to
produce `/srv/pagefind/` from `data/items.json`.

Result: 8,028 pages indexed, 40,357 words, 36 MB output, 3 filters
(`type`, `collection`, `tag`). Annotation pass done: every page has
`data-pagefind-body` on `<div id="primary">` so only the main content
is indexed (chrome is skipped); show pages carry a hidden facet block
sourced from `data/items.json` (authoritative, no HTML scraping). The
PagefindUI renders filter checkboxes automatically when the index
contains filters.

**UI wiring** (`inject_pagefind.py`):

- Replaces every page's `<div id="search-wrap">...</div>` with a plain
  form: `<form action="/search.html" method="get">` + `<input name="q">`.
- No Pagefind JS on content pages — just a GET form.
- `/search.html` is a new page cloned from `index.html` with `#primary`
  replaced by a Pagefind UI mount. Init script:
  - `new PagefindUI({ element: "#search", showImages: false, autofocus: true, resetStyles: false })`
  - reads `?q=` from URL on load, calls `ui.triggerSearch(q)`.
- Shareable links like `/search.html?q=seattle` work.
- Title rewritten to `Search | Occupy Archive`.
- Removed the "Advanced Search" link on all pages (the Omeka advanced
  form doesn't function statically).

**Result**: 8,032 pages carry the new form; 7 pages skipped (admin /
error fragments without the main theme header).

### 3. Item type filters (Images / Documents / Websites / Audio / Video)

`postprocess.py` had dropped every file whose name contained a literal
`?`, which wiped out all 146 `?type=N` filter pages that wget had
faithfully crawled.

`rescue_type_filters.py` recovers them:

- Reads `_wget/.../items/browse/*?type=*.html`.
- Two filename patterns:
  - `items/browse/index.html?type=N.html` → `items/browse/type/N/index.html`
  - `items/browse/P?type=N.html` → `items/browse/type/N/page/P.html`

  The landing is written as `N/index.html` (not a flat `N.html`) so it
  doesn't collide with the `N/page/` pagination subtree sharing its
  name. When a `.html` file and a directory share a basename, both
  Apache's `!-d` mod_rewrite clause and Caddy's `try_files` match the
  directory first and never consult the sibling file, 404'ing the
  canonical `/items/browse/type/N` URL. Writing it inside the
  directory as `index.html` is served natively by `DirectoryIndex` /
  `file_server`'s default `index`.
- Rewrites link targets:
  - `/items/browse/?type=N` → `/items/browse/type/N`
  - `href="N?type=M"` (relative pagination) → `/items/browse/type/M/page/N`
  - `href="../advanced-search?type=N"` → `/items/advanced-search.html`
  - Handles both raw `?` and URL-encoded `%3F` (wget's `--convert-links` encodes it).
- Absolutizes every relative href/src against the wget base
  `/items/browse/` via `urllib.parse.urljoin` — fixes a critical bug
  where `../tags.html` from a depth-3 relocated file resolved to the
  404 URL `/items/browse/tags.html`.
- Fixes the double-`current` class bug: Omeka's theme marks both
  `nav-all` and `nav-<type>` as `current` on filtered landings; only
  `nav-<type> current` is kept.
- Strips `<link rel="alternate" type="application/(rss|atom)+xml">`
  feeds (matches postprocess's behavior).
- For every *existing* `_static/**/*.html` file, re-injects `<a>` tags
  on the stripped type nav items
  (`<li class="nav-images">Images</li>` → `<li class="nav-images"><a href="/items/browse/type/6">Images</a></li>`).

**Result**: 141 files copied, 4,133 existing pages patched with new
nav anchors, all relative links absolutized.

### 3a. Collection filters

Same bug, same fix, different facet. `postprocess.py` dropped every
`?collection=N` page too, so the "Browse items in this collection"
link on all 202 `collections/show/<id>.html` pages (plus 10 on
`collections.html`) 404'd.

`rescue_collection_filters.py` mirrors the type-filter rescue:

- Landing: `_wget/items/browse?collection=N.html` →
  `_static/items/browse/collection/N/index.html` (same shadowing-avoidance rationale as type landings above).
- Paginated: `_wget/items/browse/P?collection=N.html` →
  `_static/items/browse/collection/N/page/P.html`
- Absolutizes relatives with different bases per source location
  (landings resolved against `/items/`, paginated against
  `/items/browse/`).
- Rewrites site-wide `href="...items/browse%3Fcollection=N.html"` →
  `href="/items/browse/collection/N"` (both URL-encoded `%3F` and raw
  `?`). Paginated-form hrefs too, though none happened to exist.

Post-rescue pages need the same content cleanups applied to the rest
of the site, so the following were run with `STATIC_ROOT=/workspace/occupyarchive`:

- `strip_ga.py` — removed GA from 298 new pages.
- `strip_fakecron.py` — removed FakeCron from 298 new pages.
- `inject_pagefind.py` — wired the Pagefind search form on 298 new pages.
- `data-pagefind-body` annotation added to `<div id="primary">` on 298 new pages.

**Result**: 298 files rescued (202 landings + 96 paginated), 664
hrefs patched across 256 existing pages. Zero remaining `collection=`
404s.

### 3b. Tag cloud anchors (`/items/tags.html`)

Same root cause as 3 and 3a, different symptom. `postprocess.py`
dropped querystring files wholesale and then stripped the now-broken
anchors on `/items/tags.html` rather than rewriting them, leaving
1,824 bare `<li class="…popular">tagname</li>` entries — visible
text, no link.

wget had captured two URL forms for every tag (the `?tags=X`
querystring variant, deleted in postprocess, *and* the slug-based
`/items/browse/tag/X` canonical, which is still on disk). The cloud
just needed its hrefs rewritten to the surviving form.

`rescue_tag_cloud.py`:

1. Pulls the `<ul class="popularity">` block verbatim from
   `_wget/items/tags.html` (the original cloud, anchors intact).
2. Rewrites each `href="[./]?browse%3Ftags=SLUG.html"` →
   `href="/items/browse/tag/SLUG.html"`.
3. Verifies each target file exists on disk; warns on any miss.
4. Swaps the block into `_static/items/tags.html`.

Using the wget HTML as the source of truth sidesteps having to
reinvent Omeka's tag-name-to-slug transformation (which is non-trivial
— slugs preserve literal `:`, `=`, `+`, and non-ASCII characters).

**Result**: 1,824 anchors re-injected, 0 missing on disk.

### 4. Randomized featured items on the homepage

Live Omeka calls `random_featured_items(2)` on every render.
`generate_featured.py` replicates this client-side:

1. Parse `db_occupyarch.sql` for `featured=1 AND public=1` rows in
   `omeka_items` → 11 item IDs.
2. For each, read the matching `items/show/<id>.html`, extract
   `<h1>title</h1>` and the first `square_thumbnails/<hash>.<ext>`.
3. Write `_static/featured-pool.json` (11 entries).
4. Inject a `<script>` before `</body>` in `_static/index.html` marked
   with `<!-- pagefind-featured-randomizer -->`. On load it fetches
   the pool, shuffles, and rewrites `#featured-item` to two random
   `<a class="image"><img></a>` entries. The baked-in items (958, 654)
   remain as no-JS fallback.

### 5. Browse Map rebuild (Leaflet + OpenStreetMap)

The original map was broken on the live site too:
- `http://maps.google.com/maps/api/js?sensor=false` — no longer works without a keyed billing account.
- Mixed content over HTTPS.
- Pin data came from a dynamic `/geolocation/map.kml` endpoint the crawler never hit.

`generate_map.py` replaces it with a static Leaflet view:

1. Parse `omeka_locations` from SQL (schema: id, item_id, latitude,
   longitude, zoom_level, map_type, address). 88 rows; filter out
   `(0,0)` sentinels and private items → **79 valid pins**.
2. For each, scrape the item's title from the rendered show page.
3. Emit `_static/data/geodata.geojson`:

   ```json
   { "type": "FeatureCollection", "features": [
     { "type": "Feature", "geometry": { "type": "Point", "coordinates": [lon, lat] },
       "properties": { "id": 5, "url": "/items/show/5.html", "title": "..." } }
   ] }
   ```
4. Rewrite `_static/items/map.html`:
   - Strip the Geolocation plugin's script/style blocks and the
     `var mapDisplayOmekaMapBrowse = ...` init.
   - Inject Leaflet 1.9.4 CSS/JS from `unpkg.com` with SRI hashes.
   - Replace `#primary` with a 600px `<div id="map-display">` and a
     small init script: create `L.map`, add the OSM tile layer, fetch
     the GeoJSON, bind a popup (`<a href="${url}">${title}</a>`) to
     each feature, call `map.fitBounds(...)`.
5. Delete the 4 paginated `/items/map/{1..4}.html` files — one
   client-side map covers all 79 pins.

### 6. Tracker / cron cleanup

- `strip_ga.py` — removed the inline `<script>var _gaq...</script>`
  block (UA-3026200-6, `www.google-analytics.com/ga.js`) from 8,030
  pages. Matomo (`stats.rrchnm.org`, site id 8) left intact per
  site-owner preference.
- `strip_fakecron.py` — removed both:
  - External: `<script src="...plugins/FakeCron/.../fakecron.js">`.
  - Inline: `<script>var FakeCron = {}; FakeCron.baseURL=...; FakeCron.tasks=[...]</script>`.
  FakeCron simulates cron by POSTing from the browser on every page
  load; meaningless on a static mirror.

### 7. Dead plugin purge

Omeka's per-item Geolocation widget was broken on the live site too:
it loaded `http://maps.google.com/maps/api/js?sensor=false`, which
stopped serving without a keyed billing account, and then called
`new OmekaMapSingle(...)` into an empty 200×200 `<div>`. Stripped
from 84 item show pages (the full block: Google Maps script, plugin
`map.js`, `<h3>Location</h3>` heading, inline styles, map div, and
CDATA init script). Also stripped two sitewide `<link>` tags and
two `<script>` tags from `share.html` referencing the same plugin.

All Omeka plugin directories removed from the repo:

- `plugins/FakeCron/` — no references.
- `plugins/Geolocation/` — no references after the widget strip. The
  rebuilt `/items/map.html` uses Leaflet + OSM (see §5) and does not
  depend on this plugin.
- `plugins/Contribution/` — only referenced by `share.html`, which
  was removed (see §8). `plugins/` directory deleted entirely.

### 8. Share page removal

The "Share Your Story" flow on the live Omeka site collected user
contributions through the Contribution plugin. On a frozen static
mirror that form can't work — POSTs have nowhere to go. Removed:

- `share.html` — the contribution form page.
- `contribution/terms.html` — terms-of-service fragment only
  referenced by `share.html`.
- `plugins/Contribution/` — plugin assets, now orphaned.
- `<div id="share-box">` ("Share Your Story" sidebar) from
  `index.html` and `search.html`.
- `<li class="nav-share"><a href="share.html">Share</a></li>`
  from the main and footer nav on 16,650 occurrences across all pages.
- An empty `<li class="nav-"><a href="share.html"></a></li>` nav
  artifact from 8,325 pages.
- A prose link `<a href="share.html">We want to hear from you.</a>`
  in `about.html` (paragraph rewritten to drop the call-to-action).

Also removed: the `<p>Follow us: <a>@occupyarchive</a></p>` footer
line across 8,326 pages (the Twitter account is inactive).

## Directory snapshot (this repo)

```
.
├── .gitignore                  (excludes archive/, Dockerfile)
├── README.md                   (this file)
├── index.html                  (featured-item randomizer injected)
├── search.html                 (Pagefind UI, reads ?q=)
├── about.html, contact.html, items.html, collections.html
├── featured-pool.json          (11 featured items)
├── pagefind_index.mjs          (Node script: items.json → pagefind/)
├── data/
│   ├── items.json              (3,528 items — authoritative for facets)
│   ├── collections.json
│   ├── files.json              (2,490 file records)
│   ├── tags.json
│   └── geodata.geojson         (79 map pins)
├── pagefind/                   (36 MB sharded index + WASM)
├── archive/                    (GITIGNORED — see "Archive storage")
├── items/
│   ├── advanced-search.html    (orphan — link removed, file still on disk)
│   ├── map.html                (Leaflet + OSM)
│   ├── tags.html
│   ├── browse.html
│   ├── browse/
│   │   ├── <N>.html            (pagination: all items)
│   │   ├── tag/<slug>/         (tag-filtered)
│   │   ├── type/               (RESTORED — see rescue_type_filters)
│   │   │   └── {1,4,5,6,7}/
│   │   │       ├── index.html  (type landing — Documents / Images / …)
│   │   │       └── page/<P>.html
│   │   └── collection/         (RESTORED — see rescue_collection_filters)
│   │       └── <N>/
│   │           ├── index.html  (collection landing, 202 total)
│   │           └── page/<P>.html (where present)
│   └── show/
│       └── <N>.html            (3,528 item pages)
├── collections/
├── themes/
└── application/
```

## Rebuild execution order

Running from a fresh `_wget/` (skip step 1 if already done):

1. **Crawl** (not performed in this session — `_wget/` was pre-existing):
   - Stand up Omeka 1.4.2 legacy container from `build/docker-compose.yml`
     (not present; see `PLAN.md` step 1).
   - `build/crawl.sh` → `_wget/`.
2. `python3 build/postprocess.py` — `_wget/` → `_static/` (pre-existing).
3. `python3 build/rescue_type_filters.py` — restore type filter pages + fix nav.
4. `python3 build/rescue_collection_filters.py` — restore collection filter pages + fix `collections/show/*` hrefs.
5. `python3 build/rescue_tag_cloud.py` — re-inject anchors on `/items/tags.html`.
6. `python3 build/strip_ga.py` — drop Google Analytics.
7. `python3 build/strip_fakecron.py` — drop FakeCron.
8. `python3 build/inject_pagefind.py` — wire up search form + `/search.html`.
9. `python3 build/generate_featured.py` — featured-item randomizer + pool JSON.
10. `python3 build/generate_map.py` — GeoJSON + Leaflet map page.
11. Migrate filter landings to `index.html` form (see rescue sections for why):

    ```bash
    for dir in items/browse/type items/browse/collection; do
      find "$dir" -maxdepth 1 -type f -name '*.html' | while read f; do
        base="${f%.html}"; mkdir -p "$base"
        [ -e "$base/index.html" ] || mv "$f" "$base/index.html"
      done
    done
    ```

    The rescue scripts currently emit flat `N.html` landings next to
    the `N/page/` pagination subtree, which shadows the landing on
    any directory-aware server (mod_rewrite `!-d`, Caddy `try_files`).
    Either patch the rescue scripts to write `N/index.html` directly,
    or run the loop above.
12. `npx -y pagefind@latest --site occupyarchive.org_static` — build the search index (reads `data-pagefind-body` + facet spans).
13. `docker build -t occupyarchive-static occupyarchive.org_static` — ship image.

Steps 3–11 are order-independent among each other (no cross-dependencies);
keep them before step 12 so Pagefind indexes the final HTML.

## Deferred / known issues

- **Orphan `/items/advanced-search.html`**: still on disk, no nav
  links to it. Safe to delete.
- **PHP 5.3 container / crawl tooling**: `build/php53/`,
  `build/docker-compose.yml`, `build/crawl.sh`, `build/extract_json.py`
  described in `PLAN.md` are not yet in this tree — the `_wget/`
  snapshot was created elsewhere on 2026-04-16.
- **Paginated filter pagination UI**: the rescued type pages
  (`/items/browse/type/6/page/N`) still use Omeka's pagination widget;
  verify links resolve correctly end-to-end.
- **Privacy**: Matomo (`stats.rrchnm.org`, site id 8) remains active
  on every page per site-owner preference. Remove with a sibling strip
  script if policy changes.

## Verification checklist

Smoke-test against the serving container:

- [ ] `/` renders; reload swaps the two featured items.
- [ ] `/items/browse` paginates to the last page.
- [ ] `/items/browse/type/6` (Images) renders; pagination links work.
- [ ] `/items/show/<id>` — sample 20 pages; images load from `/archive/`.
- [ ] `/items/tags.html` renders and every tag is a clickable `<a>`; a sampled tag navigates to its `/items/browse/tag/<slug>.html` page.
- [ ] `/items/map.html` shows a US-centered map with 79 pins; popups link to show pages.
- [ ] `/search.html?q=seattle` returns ranked results; clicking a result goes to the item page.
- [ ] Network tab: no requests to `localhost:8080`, `www.google-analytics.com`, `maps.google.com`, or `fake-cron`.
- [ ] Matomo request to `stats.rrchnm.org/matomo.js` present.
