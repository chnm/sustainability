# 20.rrchnm.org

## Retrofit

The crawled mirror still behaved like a live Omeka site: search posted to a
server that will not exist, the browse map fetched its markers over AJAX from a
dead endpoint, every item image pointed at the origin host, and the footer
credited Omeka. `tools/` turns it into a self-contained archive.

**Rebuild from a fresh crawl, or after any content change:**

```sh
cd 20.rrchnm.org
python3 tools/harvest.py          # origin-only data; must run first
python3 tools/retrofit.py         # the 693 crawled pages, in place
python3 tools/make_search_pages.py # search.html, items/search.html, 63 stubs
npx -y pagefind@1.5.2             # rewrites pagefind/ -- always LAST

node tools/serve.js . 8765 &      # then verify (Range support: PMTiles needs it)
node tools/a11ycheck/run.js       # axe-core: 30 pages, 0 A/AA violations
node tools/a11ycheck/verify.js    # map, search, keyboard, reflow, network
```

Order matters twice. `harvest.py` first, because `retrofit.py` refuses to start
without the data it fetches rather than emit dead links. `pagefind` last,
because it indexes the HTML as committed — running it earlier bakes the dead
absolute origin into the result thumbnails.

`retrofit.py` is idempotent: a second run must leave `git diff` empty, and
`--check` reports what would change without writing.

| what | where |
|---|---|
| Static search | `pagefind/` (committed — the deploy only copies files), `pagefind.yml`, `search.html`, `items/search.html` |
| Accessibility | `themes/a11y.css`, plus markup fixes in `retrofit.py` and the keyboard fixes in `themes/Berlin/javascripts/globals.js?v=3.0.1` |
| Map data | `geolocation/map.kml` — all 55 markers, merged from the origin's two paginated pages |
| Basemap | `basemap/*.pmtiles` + `protomaps-leaflet` — self-hosted OSM vector tiles, replacing CARTO |
| Timeline data | `data/neatline-timeline-1.json` — 58 events, rendered statically |
| Media | referenced as `/files/…`; the objects themselves live in the bucket |

### Media

The 1,405 objects under `files/{original,square_thumbnails,fullsize,thumbnails}`
were excluded at crawl time and are **not in this repo** (`.gitignore` blocks
all four). `tools/harvest.py` stages them outside the tree with a manifest:

```sh
python3 tools/harvest.py --media-dir /path/outside/the/repo
```

The bucket and the web server's `/files/` redirect are live on
20th.dev.chnm.gmu.edu: both `/files/square_thumbnails/…` and
`/files/original/….pdf` return 200 there. They 404 under a bare
`python3 -m http.server`, which is expected — that is why
`tools/a11ycheck/run.js` blocks the host rather than treating a missing bucket
as an accessibility regression. `files/theme_uploads/` is committed and served
from the repo.

### Basemap

The 60 pages that draw a map (the 3 browse-map pages, 55 `items/show/`, 2
`exhibits/show/pwd/item/`) used to fetch raster tiles from CARTO. CARTO's
basemaps are *"available exclusively with an Enterprise license"*, so the
archive was leaning on a service it probably was not licensed for — and on an
endpoint that has already moved once.

They are now drawn from `basemap/protomaps-basemap-z0-5.pmtiles`: a single
14 MB file of OpenStreetMap-derived vector tiles (ODbL), read straight out of
static storage with HTTP range requests by `protomaps-leaflet`. No API key, no
account, no vendor. See `basemap/PROVENANCE.txt` for exactly how it was built
and how to rebuild it.

It carries zoom 0–5, which is every zoom the archive opens at — the browse map
at z4, the per-item maps at z5 (50 of 57) and z4 (4). Above that the renderer
over-zooms the z5 geometry, so `map.js` caps the zoom controls at 9 rather than
letting people zoom into an empty rectangle; the three items authored at z15–17
clamp to it. Buying more detail means a bigger file: world z0–6 is 43 MB, z0–7
is 178 MB. A `--region` extract would put detail only around the 37 marker
locations, but `pmtiles extract --region` crashes with `concurrent map writes`
in go-pmtiles 1.30.3 and 1.31.2, so that is blocked upstream for now.

**Local preview needs `tools/serve.js`, not `python3 -m http.server`** — the
latter ignores `Range` and returns the whole 14 MB archive for every tile
request, so the map silently fails to draw.

### Not fixable from markup

- **Three videos** (`items/show/{389,390,451}.html`) have no captions and no
  transcript. There is no `<track>` anywhere in the archive; SC 1.2.2 needs
  someone to transcribe them.
- **Roughly half the `alt` values are filenames** (`"Screen Shot 2016-10-05 at
  8.57.57 PM.png"`). Every `<img>` *has* an `alt`, so axe reports zero
  `image-alt` violations and the archive still fails 1.1.1 in substance.
- **The 81 embedded PDFs** are 1990s–2000s scans in the bucket; their internal
  accessibility is out of reach from HTML.
- **The KnightLab timeline** on `exhibits/show/timeline.html` is gone at source
  — its Google spreadsheet returns 410 and the Internet Archive has no capture,
  so the embed is replaced by a note pointing at the exhibit's five sections.

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://20.rrchnm.org/`

**Run**

- started:   2026-05-27 16:00:32
- finished:  2026-05-27 16:08:53
- duration:  501s (wrapper) · 8m 21s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 818 files, 14M (11.0 MB/s)
- links converted: 768 files in 0.3s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 818 | 11 | 1 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (1)

| status | url |
|--------|-----|
| 404 | https://20.rrchnm.org/exhibits/show/histories-of-the-national-mall/mallhistories.org |

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered (`-X`, `--reject-regex`, `--exclude-directories`) stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  | 1,801 |
| `href=` | 5,338 |

**Top broken path prefixes**

| count | prefix                       |
| ----: | ---------------------------- |
|  4218 | `items/`                     |
|  1718 | `files/square_thumbnails/`   |
|  1102 | `files/original/`            |
|   757 | `search`                     |
|   352 | `items`                      |

Locally surviving under `files/`: `show/`, `theme_uploads/`. The Omeka media-derivative dirs (`files/{original,square_thumbnails,fullsize,thumbnails}/`) were excluded at crawl time.
