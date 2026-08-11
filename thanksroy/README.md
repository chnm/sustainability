# thanksroy.org

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://thanksroy.org/`

**Run**

- started:   2026-05-27 16:00:32
- finished:  2026-05-27 16:05:42
- duration:  310s (wrapper) · 5m 10s (wget wall-clock)
- status:    `ok`
- downloaded: 554 files, 8.0M (10.8 MB/s)
- links converted: 534 files in 0.2s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 554 | 2 | 0 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures

None.

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  |   402 |
| `href=` | 3,323 |

**Top broken path prefixes**

| count | prefix                       |
| ----: | ---------------------------- |
|  2444 | `items/`                     |
|   812 | `Imgs/`                      |
|   648 | `items/show/`                |
|   532 | `search`                     |
|   402 | `files/square_thumbnails/`   |

Locally surviving under `files/`: `theme_uploads/`. All Omeka media-derivative dirs were excluded at crawl time. Note: 812 refs to a non-standard top-level `Imgs/` dir (also not crawled).

## Static search (Pagefind)

The original site's search box posted to `https://thanksroy.org/search` (the live
Omeka backend), and the "Advanced Search (Items only)" page was worse than dead:
`wget --convert-links` rewrote its `action` to `browse.html`, so submitting it
silently reloaded an unfiltered browse list. Both were re-implemented
client-side with [Pagefind](https://pagefind.app) — a static search index served
as plain files, no server required.

**What changed**

- `search.html` — the site-wide results page, hosting the Pagefind Default UI.
  It reads the query from `?query=` (the field name the old form used), so
  `/search.html?query=lincoln` is shareable and works on load.
- `items/search.html` — replaces the advanced item search, keeping the facets
  that page offered: **Collection**, **Item Type** and **Tag**, on screen when
  the page loads. Built on Pagefind's *core API* rather than its Default UI,
  because the Default UI only renders its filter panel once a keyword has been
  typed, which would leave an advanced-search page blank on arrival. The core
  API also supports `search(null, {filters})` — filter-only browsing with no
  keyword at all.
- The 171 dead `items/search?…` captures are now small redirect stubs pointing
  at `items/search.html`; a `?tags=X` capture carries through as `?query=X`.
  The zero-delay `<meta http-equiv="refresh">` is WCAG-conformant (F40 / SC
  2.2.1 concern only *delayed* refreshes) and each stub also shows a plain link.
- The site search form on every page (362 pages) now points at `/search.html`.
- `pagefind/` — the prebuilt index, committed, so the site stays a pure static
  deploy with no build step.

**Index scope.** Only the 169 canonical content pages are indexed: the 162 item
pages, the 5 simple pages and the 2 collection pages, each carrying
`data-pagefind-body` on its `<main>`. The wget artifacts — 172 `items/browse?…`
captures, 17 `items?page=N.html` duplicates, `items.html`, `items/tags.html`,
the search stubs — are pagination and facet views of content indexed elsewhere,
so they stay out. The homepage's `#featured-item` and `#recent-items` blocks
carry `data-pagefind-ignore`; the first is randomized at runtime and both merely
repeat text the item pages own.

**Facet data** comes from markup already on each item page, except the item
type: Collection from the `#collection` link, Tag from each `rel="tag"` link,
and Item Type from a new metadata row whose value is read from the page's own
COinS `rft.type`. Note that Pagefind 1.5.2 only reads a filter value from an
element's **text** — the documented `Name[value]` attribute form silently yields
an empty value (verified against `span`, `div` and `meta`) — which is why the
item type is rendered as a visible row rather than hidden. The Omeka theme never
displayed it at all, so this restores information the page was missing.
Multi-value filters use Pagefind's `{any: […]}` operator; a bare array means
AND, so `['Document','Still Image']` would ask for items that are both.

**Deployment note.** The form `action`, the filter results and the logos are
root-absolute, so the archive must be served at a domain root (as it is at
`thanksroy.dev.chnm.gmu.edu`).

**Rebuild the index** after changing page content:

```sh
cd thanksroy
npx -y pagefind@1.5.2      # reads pagefind.yml, rewrites ./pagefind/
```

## Accessibility (WCAG 2.2 AA)

The archive was a raw crawl with no remediation. It was brought to **WCAG 2.2
AA**, following the repo's `plastercast` pattern. Verified with **axe-core
4.12.1** (rulesets `wcag2a/2aa/21a/21aa/22aa` plus best-practice) → **0
violations** across every page type, plus a keyboard pass at 375px and 1280px.

- **Keyboard (2.1.1)**: the mobile menu opener was a `<div>` — not focusable,
  no accessible name — and below 768px `#primary-nav ul.navigation` is
  `display: none`, so **the navigation could not be reached by keyboard at
  all**. It is a `<button>` with `aria-expanded` now.
- **Bypass blocks (2.4.1)**: the skip link used a file-relative `href`, so on
  the homepage (served at `/`) it reloaded the page instead of jumping — Omeka's
  `skipNav()` never calls `preventDefault()`. It targets `#content` now.
- **Landmarks (1.3.1, 2.4.1)**: a real `<main id="content">` on every page;
  redundant `role=` dropped from `header`/`footer`; the duplicate `nav`s named
  (`Main`, `Items`, `Item`, `Pagination` / `Pagination (bottom)`).
- **Contrast (1.4.3)**: `a:visited` was `#8e8e8e` (3.28:1) and placeholders
  `#888` (3.54:1); both darkened. `style.css:1420-1431` hides a *worse* fallback
  palette (`#888`/`#999`/`#777`) that the theme-config inline `<style>` masks —
  the link colours are restated in `a11y.css` so it can never surface.
- **Focus visible (2.4.7, 1.4.11)**: `style.css:558` and `:593` set
  `outline: 0` on every form control, leaving only a 7px blurred shadow with no
  solid perimeter. Restored as a 3px `#ffe000` ring inside a `#1c1c1c` ring, so
  the indicator itself is perceivable on white.
- **Target size (2.5.8)**: padding on pagination, item prev/next and tag-cloud
  links, which were exactly 24px tall with no spacing.
- **Names and labels (1.3.1, 3.3.2, 4.1.2)**: real `<label>`s for the search and
  pagination inputs (they were labelled by `title=`), a submit button for the
  pagination form (it was Enter-only), and names for the image-only links in
  `memorial-events.html`.
- **Headings (1.3.1)**: item pages ran `h1 → h3 → h3 → h2`; the `.element`
  headings are `h2` now. The homepage had no `h1` at all.
- **Unique titles (2.4.2)**: the 8 `[Untitled]` pages are disambiguated by id.
- WCAG 2.2's other AA additions are satisfied without change and were confirmed:
  2.4.11 Focus Not Obscured (the theme has no `position: fixed`/`sticky`),
  2.5.7 Dragging Movements and 3.3.8 Accessible Authentication (neither exists
  here), 3.2.6 Consistent Help and 3.3.7 Redundant Entry (no help mechanism, no
  multi-step flows).

Fixes live in `themes/default/css/a11y.css` (loaded last in every `<head>`, so
it beats both `style.css` and the theme-config inline block) plus the site-wide
HTML edits in `tools/retrofit.py`.

**Outstanding — alt text (1.1.1).** 406 of 943 images carry a URL as their
`alt` (e.g. `alt="http://thanksroy.org/Imgs/roy1007_3856d15c33.jpg"`), and 941
images are the sole content of a link, so that URL is the link's accessible
name. Descriptive alt text is a **deferred follow-up** (a curatorial pass), so
1.1.1, 2.4.4 and 4.1.2 are not yet met for those images even though axe — which
only checks that `alt` is present — reports clean.

## Randomized featured item

Omeka's homepage called `random_featured_items()`, so the "Featured Item" block
showed a different item on every request; the crawl froze it on item 614. It is
randomized client-side again by `themes/default/javascripts/featured-item.js`
(vanilla JS, no jQuery dependency).

The five featured items — 606, 608, 609, 614, 626 — were harvested from
`https://thanksroy.org/items/browse?featured=1` while the origin was still up,
and cross-checked against repeated fetches of the live homepage. Regenerate the
list with `tools/featured_items.py`. With scripting off, the server-rendered
item 614 stays in place.

## Output formats

Item pages linked four output formats and browse listings five, all to the dead
origin. Only **dcmes-xml** is kept, and it points at a real file: 162 per-item
sidecars (`items/show/<id>.dcmes.xml`, matching the naming `mallhistory/` uses)
and 190 per-listing sidecars, harvested by `tools/dcmes_harvest.py` from each
page's own former link. `tools/retrofit.py` refuses to run if any is missing,
rather than emitting a dead link.

## Chrome

- The **RRCHNM archive notice banner** from the `forustheliving.org` archive
  (`futl/`) now appears on every page, with the shared `rrchnm_logo.png`. Two
  deliberate deviations from the futl markup, both accessibility: it is an
  `<aside aria-label="Archive notice">` rather than a `<div>` outside every
  landmark, and `target="_blank"` is paired with `rel="noopener"`.
- The **"Proudly powered by Omeka" footer credit** is replaced by RRCHNM's own
  horizontal wordmark linking to rrchnm.org, following commit `83180e5d9b`,
  which did the same with a GMU logo on the sibling archives. The asset is
  rrchnm.org's `/img/logo-dark.png` — its dark-ink variant, the one that site
  uses on light backgrounds; `/img/logo.png` is the light-ink version for dark
  backgrounds, and this footer is white. 541×100, shown at 200×37. The COinS
  `omeka.org:generator` citation metadata and any Omeka mentions inside archived
  content are untouched.

  Note the banner and the footer deliberately carry *different* marks: the
  banner keeps the square `rrchnm_logo.png` shared byte-for-byte with the other
  sustainability archives, so the notice stays identical across all of them,
  while the footer credit is thanksroy's own and uses the full wordmark.

## Robustness

- **PT Serif is self-hosted** (`themes/default/css/pt-serif.css` + woff2 subsets
  under `themes/default/fonts/`, latin and latin-ext, SIL OFL). Every page used
  to link `fonts.googleapis.com`, which is blocked on some networks — the same
  defect commit `3dc3703896` fixed for mallhistory's Raleway.
- **jQuery 1.12.4 and jQuery UI 1.11.2 are vendored** under
  `application/views/scripts/javascripts/vendor/`. Every page loads them from
  `ajax.googleapis.com` with a `document.write` fallback to a local path — but
  that file was never crawled, so a blocked CDN left `jQuery` undefined,
  `globals.js` and `default.js` both throwing at their IIFE, and every inline
  `jQuery(document).ready(…)` dead, taking the mobile menu with it. Verified by
  blocking both Google hosts in a browser: fonts render, jQuery loads locally,
  and the mobile menu still opens.

## Tools

| script | what it does |
| ------ | ------------ |
| `tools/dcmes_harvest.py` | fetches the 352 dcmes-xml sidecars from the live origin (idempotent) |
| `tools/retrofit.py` | the site-wide search + accessibility + chrome pass; idempotent, `--check` reports without writing |
| `tools/featured_items.py` | regenerates the featured-item list from the live origin |
| `tools/a11ycheck/run.js` | axe-core audit of one page per type, driven by headless Chromium |

```sh
cd thanksroy
python3 tools/dcmes_harvest.py     # first: the sidecars retrofit.py links to
python3 tools/retrofit.py
npx -y pagefind@1.5.2

python3 -m http.server 8765 &      # then verify
node tools/a11ycheck/run.js
```

`a11ycheck` uses a real browser rather than jsdom (as `occupyarchive/tools/a11ycheck`
does), because jsdom cannot compute colour contrast or target size and cannot run
Pagefind's WebAssembly index — the two search pages would audit as empty shells.
It needs `npx playwright install chromium && npx playwright install-deps chromium`.

## Known gaps

- **Alt text** — see the accessibility section above.
- **The origin `thanksroy.org` was still live as of 2026-08-11, and that is
  currently load-bearing.** All 402 image references are absolute URLs to it, so
  item thumbnails render *today* by hot-linking a site that is being retired.
  `files/{original,square_thumbnails,fullsize,thumbnails}/` were excluded at
  crawl time and the deployed archive already 404s them, so **every image breaks
  the moment the origin goes down**. The window to mirror the media is open and
  will close: re-crawl those directories (and the non-standard top-level `Imgs/`,
  812 refs, never crawled), then either commit them or push them to an object
  bucket with a not-found redirect, as `mallhistory/README.md` documents for its
  map tiles. `tools/retrofit.py` already relativizes any absolute origin URL
  whose target exists in-tree, so it will pick them up on the next run.
- ~3,700 absolute `href`/`src` references to the origin remain outside the search
  form (2,444 under `items/`, 812 under `Imgs/`).
- **Search recall is bounded by the data.** Only 72 of 162 items have body text
  on the page (68 `Text`, 4 `URL`); the other 90 are image-only and are indexed
  on title, item type, tags, collection and citation alone. The dcmes-xml
  sidecars do not help — image-only items carry no `dc:description` either.
- `style.css` lines 909, 1107 and 1315 contain an invalid
  `@media screen and (max-width: 48em 16)` query (an upstream Omeka theme bug);
  those blocks never apply. Left as-is.
