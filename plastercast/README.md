# George Mason University Plaster Cast Collection

**A flattened static archive of the Omeka site `plastercast.gmu.edu`.**

## About

The George Mason University Plaster Cast Collection documents a ten-year effort,
led by Dr. Carol Mattusch (Mathy Professor of Art History), to acquire and
research plaster casts originally from the Metropolitan Museum of Art. The
interdisciplinary project brought together students, scholars, and staff to
catalogue the casts, which came to GMU by way of the 2006 Sotheby's dispersal of
the Met's cast collection.

The catalogue contains **64 entries**, one per identified cast, grouped into
**six collections** by the period they represent. Each entry includes a
description, bibliography, location, and photographs. Narrative history pages and
two interactive exhibits round out the site.

## Structure

- Root pages: `index.html`, `about.html`, `history.html`, `research.html`,
  `plaster-casts-at-gmu.html`, `the-last-casts.html`, the four-part auction
  narrative (`part-i-the-viewing.html` … `part-iv-arrival-and-parting-thoughts.html`),
  student pages, `acknowledgements.html`, `contact-us.html`, etc.
- `items/show/<n>.html` — 64 cast catalogue entries
- `collections/show/<n>.html` — 6 collection pages (ids 7–12)
- `exhibits/show/*.html` — 2 exhibits
- `items/browse.html`, `items/map.html`, `items/tags.html`, `items/search.html`,
  `geolocation/map/browse.html` — browse/landing pages
- Navigational browse permutations kept as-is (see below):
  `items/browse?collection=<n>.html`, `items/browse?page=<n>.html`, etc.
- `files/original/` (272 images), `files/square_thumbnails/` (235),
  `files/theme_uploads/` — media
- `themes/`, `plugins/`, `application/` — the Omeka "seasons" theme + plugin CSS/JS

## Provenance & cleanup

This directory was flattened from a `wget --mirror` capture of the live Omeka
site. The capture was complete (every referenced image and CSS/JS asset is
present), but wget followed every sort/feed permutation link, producing ~4,400
duplicate files. The following cleanup was applied when copying the mirror here:

**Removed**
- Feed / API exports — every `?output=atom|rss2|json|dcmes-xml|dc-rdf|omeka-xml`
  file (~3,500).
- Sort-order duplicate pages — every `?sort_field=` / `?sort_dir=` variant (~900).
- `.DS_Store` files.
- Feed-discovery `<link rel="alternate">` tags and the visible "Output Formats"
  and "Sort by" link blocks from every page (their targets were removed above).

**Kept**
- All content pages, media, and theme/plugin assets.
- Navigational query-string pages (pagination `?page=N`, collection filter
  `?collection=N`) **with their literal `?` filenames**, matching the other
  flattened Omeka sites in this repo (`harambeecity/`, `cyh/`). When served, the
  browser sends the reference as `%3F…` and the server maps it back to the `?`
  file, so in-site navigation works. The 12 theme/plugin assets that wget saved
  with a `?v=2.7.1` version suffix are likewise kept as-is and referenced via
  `%3Fv=2.7.1`.
- Two absolute intra-site links in `part-ii-auction-chi.html` were rewritten to
  their local targets (`items/show/60.html`, `exhibits/show/…`).

### Known limitations (inherent to a static capture)

- **The "history of plaster cast collecting" exhibit is not included.** It was
  never public (unpublished in Omeka) and was never captured; the one link to it
  (in `part-ii-auction-chi.html`) now points at the catalogue item it referenced
  (`items/show/60.html`).

## Reconstructed exhibit sub-pages (2026-07)

The two public exhibits have interactive section pages
(`exhibits/show/<exhibit>/<page>.html`) that the original `wget` never captured.
They were **reconstructed from the Omeka database** rather than re-fetched,
because the site's later redeployment returns HTTP 500 (truncated HTML) on every
exhibit sub-page — ExhibitBuilder fatals while rendering the item-image block.

Nine pages were rebuilt (8 for *A Short Tour…*, 1 for *The Last Casts*):

- Page text, captions, layout, and item/file attachments came from the Omeka
  DB dump (`plstcst_exhibit_pages` / `_page_entries`), matching ExhibitBuilder's
  layout templates (`text-image-left`, `image-list-left`, `gallery-full-left`).
- The correctly-rendered page scaffolding (head, nav, exhibit page-list) was
  kept from the live pages; only the content block below it was rebuilt.
- Primary images use the `fullsize` derivative (added under `files/fullsize/`,
  re-fetched from the live site's static files); gallery thumbnails reuse the
  `files/square_thumbnails/` already in the archive; the three ExhibitBuilder
  layout CSS files were added under `plugins/ExhibitBuilder/.../exhibit_layouts/`.
- All links/assets were flattened to the same relative, `?`-in-filename
  convention as the rest of the archive.

## Geolocation map, rebuilt with Leaflet (2026-07)

The original map used the Google Maps API (keyless `maps.google.com`, now dead)
plus a dynamic `/geolocation/map.kml` endpoint — neither works in a static
mirror. It was replaced with a self-contained **Leaflet + OpenStreetMap** map:

- Leaflet 1.9.4 is vendored under `assets/leaflet/` (CSS, JS, marker icons); map
  tiles load from OpenStreetMap (the only part that needs internet).
- The 51 cast locations (lat/lng, title, thumbnail) were extracted from each
  item page's own `OmekaMapSingle` data; the `files/thumbnails/` derivative used
  in the popups was re-fetched from the live site (51 images).
- The browse maps (`geolocation/map/browse.html`, `items/map.html`) plot all 51
  casts; each `items/show/<n>.html` shows its single location. Popups link to the
  item page. The dead Google-Maps/KML scripts were removed site-wide.

## Search, rebuilt with Pagefind (2026-07)

The original header search posted to the Omeka server (`/search`) and is dead in
a static mirror. It was replaced with **[Pagefind](https://pagefind.app/)**, a
fully client-side static search:

- The header search box on every page now submits (`?query=`) to `search.html`,
  which hosts the Pagefind UI and runs the query.
- Only real content is indexed: item, collection, exhibit, and narrative pages
  carry `data-pagefind-body` on their `#content`; browse/list/map/utility pages
  are excluded. Results match the old Omeka search closely (e.g. "parthenon" →
  4 results).
- The prebuilt index lives in **`pagefind/`** and is committed, because the
  deploy pipeline only copies files (no build step).

**Rebuild the index whenever page content changes:**

```sh
cd plastercast
npx pagefind@1.5.2 --site .   # regenerates pagefind/
```

## Accessibility (WCAG 2.2 AA, 2026-07)

The archive was remediated toward **WCAG 2.2 AA**, following the repo's `1989`
accessibility pattern. Verified with **axe-core 4.10** (rulesets
`wcag2a/2aa/21a/21aa/22aa`) → **0 violations** across every page type (narrative,
item, collection, exhibit, browse/listing, map, search), plus a keyboard pass.

- **Contrast (1.4.3)**: darkened nav links (`#6d6d6d`→`#3a3a3a` on the `#bdbdbd`
  bar) and reworked buttons (`#f4f4f4` on `#4b4b4b`) and the submenu background.
- **Use of color (1.4.1)**: in-text links are underlined.
- **Focus visible (2.4.7)**: 3px `#ffe000` focus ring on all interactive
  elements.
- **Keyboard (2.1.1)**: nav dropdowns open on `:focus-within`, not just hover.
- **Bypass/landmarks (2.4.1, 1.3.1)**: a "Skip to main content" link and
  `<main id="content">` on every page; `<nav aria-label="Main">`.
- **Names/labels (4.1.2)**: `aria-label` on the search and pagination inputs.
- **Headings (1.3.1)** and **unique titles (2.4.2)** normalized.
- All of the above live in an appended `/* WCAG 2.2 AA */` block in
  `themes/seasons/css/style.css` plus site-wide HTML edits.

**Outstanding — alt text (1.1.1):** image `alt`s are still the original
filename strings (e.g. `alt="34final.jpg"`). Descriptive alt text is a **deferred
follow-up** to be done separately (curatorial pass), so 1.1.1 is not yet fully
met even though axe (which only checks that `alt` is present) reports clean.

## Image viewer, replaced (2026-07)

Item pages had an "Image Viewer" that called the **Zoom.it** deep-zoom service —
shut down by Microsoft in 2016 (and an `http://` call blocked as mixed content),
so it was dead. Replaced with a **self-contained accessible lightbox**
(`assets/lightbox.js`, no dependencies): click an image to open a modal viewer
with a zoom toggle, pan (scrollbars or arrow keys — no dragging required),
prev/next, and Esc/click-out to close. It's a WCAG 2.2 AA modal dialog (focus
moved in and trapped, returned on close; keyboard-operable) and passes axe with
0 violations while open.

## Local preview

```sh
cd plastercast
python3 -m http.server 8000
# open http://localhost:8000/index.html
```

Most static servers (including Python's `http.server` and nginx) resolve the
`?`-in-filename navigation pages correctly. If a host strips query strings,
those browse permutations won't resolve, but every cast is still reachable
directly via its collection page and `items/show/<n>.html`.

## Credits

- **Project lead:** Dr. Carol Mattusch, Mathy Professor of Art History, GMU
- Roy Rosenzweig Center for History and New Media (RRCHNM), George Mason University
