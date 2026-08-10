# mallhistory.org

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://mallhistory.org/`

**Run**

- started:   2026-05-27 16:00:32
- finished:  2026-05-27 16:16:08
- duration:  937s (wrapper) · 15m 37s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 1220 files, 42M (7.64 MB/s)
- links converted: 890 files in 0.4s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 1220 | 351 | 16 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (16)

| status | url |
|--------|-----|
| 404 | https://mallhistory.org/themes/mall/images/spencer.jpg |
| 404 | https://mallhistory.org/explorations/show/%5C%22%5C/explorations%5C/show%5C/wwii%5C/item%5C/450%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22https:%5C/%5C/mallhistory.org%5C/files%5C/square_thumbnails%5C/052fb014c10357cbc986dfe3b00ef6fe.jpg%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22%5C/explorations%5C/show%5C/castle%5C/item%5C/520%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22%5C/application%5C/views%5C/scripts%5C/images%5C/fallback-video.png%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22%5C/explorations%5C/show%5C/korean-war%5C/item%5C/449%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22https:%5C/%5C/mallhistory.org%5C/files%5C/square_thumbnails%5C/7a9cf3c801c6e222d15a237a28be8071.jpg%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22%5C/explorations%5C/show%5C/grant-memorial%5C/item%5C/447%5C%22 |
| 404 | https://mallhistory.org/explorations/show/%5C%22https:%5C/%5C/mallhistory.org%5C/files%5C/square_thumbnails%5C/0240e36b6a3ea75a2352b578654aba55.jpg%5C%22 |
| 404 | https://mallhistory.org/exhibits |
| 404 | https://mallhistory.org/items/show/185http:/mallhistory.org/items/show/195 |
| 404 | https://mallhistory.org/Guide/xmlrpc.php |
| 404 | https://mallhistory.org/items/show/vvmf.org |
| 404 | https://mallhistory.org/Guide/introduction/%22http:/mallhistory.org/items/show/41 |
| 404 | https://mallhistory.org/maps |
| 404 | https://mallhistory.org/explorations/show/vietnammemorial/item/vvmf.org |

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  | 1,407 |
| `href=` | 7,432 |

**Top broken path prefixes**

| count | prefix                       |
| ----: | ---------------------------- |
|  3994 | `items/`                     |
|  1782 | `items/show/`                |
|   836 | `files/original/`            |
|   740 | `files/fullsize/`            |
|   739 | `search`                     |

Locally surviving under `files/`: `theme_uploads/`. All Omeka media-derivative dirs (`files/{original,square_thumbnails,fullsize,thumbnails}/`) were excluded at crawl time.

## Static search (Pagefind)

The original site's search box posted to `https://mallhistory.org/search` (the
live Omeka backend). In the static archive that endpoint is dead, so search was
re-implemented client-side with [Pagefind](https://pagefind.app) — a static
search index served as plain files, no server required.

**What changed**

- `search.html` — the results page. It hosts the Pagefind UI and reads the
  query from `?query=` (the same field name the old form used), so
  `/search.html?query=lincoln` is shareable and works on load.
- `pagefind/` — the prebuilt index (committed, so the site stays a pure static
  deploy with no build step).
- `pagefind.yml` — index configuration.
- The site search form on every page (739 pages) now points at `/search.html`
  instead of the dead Omeka endpoint.

**Index scope.** Only the 678 canonical Omeka content pages are indexed. Each
carries a `data-pagefind-body` attribute on its `<div role="main">`, so Pagefind
indexes just the real content — the shared header/nav/footer and the wget
artifacts (Atom/RSS feeds, `?page=`/`?tags=` pagination duplicates, the
WordPress "Guide" pages, saved font/JS blobs) are left out.

**Deployment note.** Result links and the form `action` are root-absolute
(`/items/show/…`, `/search.html`), so the archive must be served at a domain
root (as it is at `mallhistory.dev.chnm.gmu.edu`).

**Rebuild the index** after changing page content:

```sh
npx -y pagefind@1.5.2      # reads pagefind.yml, rewrites ./pagefind/
```

## Interactive map (captured data)

The `/map` page is a dynamic Omeka plugin ("MallMap") that renders 346 markers
by POSTing to live server endpoints — `mall-map/index/filter` (marker GeoJSON),
`mall-map/index/get-item` (popup content), and `mall-map/index/historic-map-data`
(era overlays). A wget crawl can't capture POST responses, so the static map
came up empty.

The data was captured from the live server into static JSON, and
`plugins/MallMap/views/public/javascripts/mall-map.js` was rewired to load it
and filter client-side (no server):

- `map/data/markers.json` — full GeoJSON FeatureCollection (id + coordinates).
- `map/data/filters.json` — precomputed id sets per filter value (map era, item
  type, place type, event type). The map filters by intersecting these sets,
  which was verified to match the live server's combined-filter output exactly.
- `map/data/items.json` — per-item popup data (title, dates, description, link).
- `map/data/historic.json` — per-era historic-map overlay metadata (`url`, `title`).

Loaded via root-absolute `/map/data/*.json`, so both `map.html` and
`map/index.html` work.

### Historic-map overlays (object bucket)

The map-era overlays are TMS tile pyramids at
`/plugins/MallMap/maps/<year>/{z}/{x}/{y}.jpg`. These are far too large to commit
(the full-viewport pyramids are ~5 GB), so the **Mall-core** tiles (the app's
`LOCATE_BOUNDS`, which contains 97% of markers), zoom 14–18 for all 8 dated
maps (~9k tiles / ~80 MB), were crawled from the live server and uploaded to the
`mallhistory.org` object bucket (Garage, `10.112.113.223:3900`, region
`rrchnm`). The web server serves them via its not-found → bucket redirect at the
same `/plugins/MallMap/maps/...` paths, so nothing map-tile-related lives in the
repo. Panning outside the Mall core shows no overlay (those tiles 404); the
"2000-present" era has no historic map.

**Known gap:** marker thumbnails point at `mallhistory.org/files/...` (excluded
from the crawl) and will break when the origin goes down, like other archived
image references.

To refresh: re-capture the three `mall-map/index/*` endpoints (markers/filters/
items/historic) while the live server is up, and re-run the tile crawl+upload to
the bucket.

## Scavenger-hunt maps (repaired after wget mangled them)

The four scavenger hunts — `castle`, `grant-memorial`, `korean-war`, `wwii` —
are the only pages with a Geolocation exhibit map, and all four came out of the
crawl dead. The marker data is an inline JS string containing escaped HTML:

```js
... <a href=\"\/explorations\/show\/grant-memorial\/item\/447\" ...
```

`--convert-links` treated that escaped `href` as a real link, resolved it
against the page URL and wrote it back wrapped in *unescaped* double quotes,
which closed the JS string early:

```js
... <a href="https://mallhistory.org/explorations/show/\&quot;\/explorations\/... \&quot;" ...
```

The result was `SyntaxError: Unexpected identifier 'https'`, so the whole
`jQuery(window).on('load', ...)` block never ran and the map div stayed empty.
(The same mangling is why `explorations/show/{castle,grant-memorial,korean-war,
wwii}/item/*` are in the crawl's 404 list — wget followed the corrupted URLs.)

**Fix.** The `map_locations` line in each of the four pages was restored from the
page's own Wayback capture — everything else in the block already matched
byte-for-byte — with the URLs pointed at the archive's own conventions:

- popup link → `/items/show/<id>.html` (what `map/data/items.json` uses);
- popup thumbnail → `/files/square_thumbnails/...` (bucket redirect).

Two runtime assets the crawl never fetched (they are referenced from Leaflet's
JS, not from HTML or CSS) were pulled from Wayback:
`plugins/Geolocation/views/shared/javascripts/leaflet/images/marker-shadow.png`
and `application/views/scripts/images/fallback-video.png` — the latter also
fixes video items' thumbnails in the main map's popups.

**One deliberate deviation:** each map is now built with `"cluster":false`
instead of `"cluster":true`. With clustering on, clicking the marker opens a
278px popup inside the theme's 180px-tall map, Leaflet auto-pans to fit it, the
marker lands outside markercluster's visible bounds and gets removed — so the
marker vanishes and the popup closes. That is upstream behaviour the live site
shared, but it makes the restored map look broken. Clustering does nothing for a
single marker, so it is off; revert by putting `true` back in the four files.

The popup used to be clipped by the theme's `height: 15em !important` map: at
180px it was shorter than a 278px popup, so Leaflet auto-panned to make room
until the marker itself left the view. `.exhibit-geolocation-map` is now
`37.5em`, the height the Geolocation plugin's own `layout.css` asks for. Probing
the popup at 15/20/24/28/30/34/37.5em, 28em is where clipping stops and 34em is
where the marker also stays in frame. This changes how tall the map looks on the
four scavenger hunts — the only pages with an exhibit map.

**Known gap.** Leaflet's retina marker icon (`marker-icon-2x.png`) was never
captured by Wayback, so it still 404s on HiDPI screens.

## Item pages the crawl missed

37 `/items/show/<id>.html` pages were referenced by `map/data/items.json` — one
per map marker — but never crawled: nothing linked to them except JavaScript
wget could not follow. Every one of those markers' popups led to a 404.

`tools/backfill_items.py` rebuilds a page from the Internet Archive's capture of
it. Only `<title>` and the `div[role=main]` content region come from the
capture; the chrome is copied from an item page the crawl did get, so rebuilt
pages carry the archive-wide fixes (Pagefind search form, Matomo, the
accessibility pass) instead of whatever the snapshot froze. The content region
then goes through the same transformations `wget --convert-links` and this
repo's later commits applied to the crawled pages, and pre-2018 captures are
additionally brought up to the markup Omeka emitted by 2026 (image block,
citation span, COinS field names, the geolocation call). Coordinates come from
`map/data/markers.json` — captured from the live server in 2026 — in preference
to the snapshot's. The `dcmes-xml` sidecar is regenerated from the same capture.

**How it was checked.** Rebuilding pages the crawl *did* get, from their own
Wayback captures, and diffing against the committed files: 7 of 7 post-2020
captures and 7 of 11 2014–2017 captures come back byte-identical, the remaining
4 differing only where the item was edited between snapshot and crawl. All
rebuilt pages were then checked for resolving links, one geolocation block with
coordinates matching `markers.json`, and well-formed XML.

**Result:** 33 of the 37 restored — 32 from Wayback, plus item 272 rebuilt from
its exhibit-scoped twin at
`explorations/show/children-on-the-mall/item/272.html`. Rebuild any of them
with:

```sh
python3 tools/backfill_items.py 141 171 177    # from the archive root
```

**The remaining four.** Items 294, 397, 449 and 520 have no capture in Wayback
and no copy anywhere in the archive, so their pages cannot be restored. Rather
than leave links that always 404, their `url` in `map/data/items.json` is now
`null` and `mall-map.js` omits the "view more info" button when it is; the two
that a scavenger-hunt map pointed at (449 on `korean-war`, 520 on `castle`) have
had the link stripped from their popup, which still shows the title and
thumbnail.

The Pagefind index was rebuilt after adding the pages: 711 pages indexed, up
from 678.

## Featured exploration (randomised client-side)

The homepage's "Featured Exploration" block was chosen server-side by Omeka, so
it changed over time (Wayback snapshots show different explorations in 2015,
2021 and 2025). A static crawl freezes whichever one the crawler happened to
get — here, "Scavenger Hunt: World War II Memorial".

`themes/mall/javascripts/featured-exploration.js` restores the rotation in the
browser: it holds all 42 explorations and picks one at random on each page load,
rewriting the block's title, description, "Read More" link and background image.
It is loaded by a plain (parser-blocking) `<script>` tag placed directly after
`#featured-question` in `index.html`, so the swap lands before first paint. With
JavaScript off, the crawled WWII block stands as-is.

**Data.** Baked into the script, all captured from the archive itself:

- titles, exploration URLs and cover images — from the five `explorations`
  listing pages;
- descriptions — from each exploration's own `div.exhibit-description`, trimmed
  the way Omeka's `snippet()` helper trimmed them (200 characters, cut at a word
  boundary, trailing punctuation dropped, `…` appended). Reproduces the three
  Wayback-snapshot renderings exactly.

The four scavenger hunts have no description, and `concerts`,
`pres_inaugurations` and `sports` have no cover image — those three get a solid
`#3d3d3d` background so the theme's white hero text stays readable.

Cover images are `/files/original/...`, served (like the rest of `/files/`) by
the web server's not-found → bucket redirect; all 34 were checked for 200s.

To refresh after adding or editing explorations, re-extract the four fields and
regenerate the `EXPLORATIONS` array in the script.

