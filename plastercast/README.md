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

- **Search is non-functional.** The header search box and `items/search.html`
  form post to the original Omeka server; they render but do nothing. (A
  client-side MiniSearch index could be added later per the repo's `DEVNOTES.md`.)
- **The interactive geolocation map is inert.** `items/map.html` and
  `geolocation/map/browse.html` depend on the live map/tile service. The
  per-item map-marker data (embedded JS on `items/show/*.html`) still contains
  absolute `plastercast.gmu.edu` URLs; these are left untouched because they are
  escaped JS strings, not page links.
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
