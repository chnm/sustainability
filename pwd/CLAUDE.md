# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Hugo static site conversion of the **Papers of the War Department** (wardepartmentpapers.org), originally an Omeka S digital humanities site. The goal is a sustainable, server-free archive of ~43,939 content pages (documents, collections, repositories), 25 editorial pages, and news posts.

Two top-level directories:
- `hugo/` — the Hugo static site (active development)
- `wardepartmentpapers.org/` — wget'd copy of the original site (reference/source for media files)

## Build & Serve Commands

All commands run from `hugo/`:

```bash
make build          # hugo --minify
make serve          # hugo server --bind 0.0.0.0
make fetch          # Run fetch-pages + fetch-items
make fetch-pages    # python3 scripts/fetch_pages.py (27 editorial pages from API)
make fetch-items    # python3 scripts/fetch_items.py (~43,939 items from API, ~1hr)
make clean          # rm -rf public/
```

Requires Hugo extended v0.128.0+ (uses `pagination.pagerSize` not deprecated `paginate`).

## Architecture

### Data Flow

Content is pulled from the live Omeka S REST API at `https://www.wardepartmentpapers.org/api/`:
1. `scripts/fetch_pages.py` → fetches `/api/site_pages`, writes `content/{slug}.md` with markdown body
2. `scripts/fetch_items.py` → paginates `/api/items` (100/page, 793 pages), writes content files for 3 resource types only
3. `scripts/fetch_media.py --catalog-only` → paginates `/api/media`, writes `static-media/files/media_catalog.json`
4. `scripts/build_media_map.py` → reads media catalog, writes `data/media_map.json` (image_id → filenames)

### 3 Resource Types (Hugo-native architecture)

The site uses a Hugo-native architecture with taxonomies instead of Omeka's ID-based cross-references. Only 3 resource types produce content pages:

| Type | Count | Directory | Template |
|------|-------|-----------|----------|
| Document | 42,880 | `content/document/` | `layouts/document/single.html` |
| Collection | 818 | `content/collection/` | `layouts/collection/single.html` |
| Repository | 241 | `content/repository/` | `layouts/repository/single.html` |

Image, Name, Microfilm, and Publication types are **not** generated as content pages. Images are resolved at build time via `data/media_map.json`. People and places are handled by Hugo taxonomies.

### Taxonomies

Configured in `hugo.toml`, these replace ID-based cross-references:

| Taxonomy | Singular | Example URL |
|----------|----------|-------------|
| `authors` | `author` | `/authors/joseph-nourse/` |
| `recipients` | `recipient` | `/recipients/john-pierce/` |
| `notable_persons` | `notable_person` | `/notable_persons/george-washington/` |
| `notable_locations` | `notable_location` | `/notable_locations/philadelphia/` |
| `notable_items` | `notable_item` | `/notable_items/dollars/` |
| `collections` | `collection` | `/collections/numbered-record-books/` |
| `doc_types` | `doc_type` | `/doc_types/autograph-letter-signed/` |

### Template Dispatch

Each resource type has its own layout directory (`layouts/document/`, `layouts/collection/`, `layouts/repository/`). Taxonomy pages use `layouts/_default/taxonomy.html` and `layouts/_default/term.html`. Editorial pages use `layouts/_default/single.html`. The homepage uses `layouts/index.html`.

### Transcriptions

Documents with transcriptions store the human-transcribed text in the markdown body (`.Content`). AI transcriptions (future) will be stored in `data/transcriptions_ai.json` keyed by `omeka_id`. The document template has a tabbed UI to toggle between human and AI transcriptions.

### URL Compatibility

Documents, collections, and repositories have Hugo `aliases` for old Omeka URLs (e.g., `/s/home/item/79270` redirects to `/document/79270/`). Removed types (Image, Name, Microfilm, Publication) will 404 — no redirect stubs.

### Static Assets

- `static/files/` — symlinked to `wardepartmentpapers.org/files/` (26k+ media files)
- `static/css/` — extracted from Omeka theme CSS
- `static/img/`, `static/fonts/`, `static/js/` — theme assets

## Known Constraints

- `markup.goldmark.renderer.unsafe = true` is required — editorial page content contains raw HTML from Omeka blocks
- The fetch scripts have 0.1s delay between API pages and 5s retry on network errors
- Multi-valued fields (notable_persons, notable_locations, notable_items) are `.strip()`'d in `get_all_literals()` to clean API whitespace
- `data/media_map.json` (~5MB) maps Image omeka_ids to filenames — loaded into memory by Hugo at build time
- The `collections` taxonomy and `collection` content type coexist at different URL paths (`/collections/{slug}/` vs `/collection/{id}/`)

## Migration Phases

Phases 1-4 are complete. Phases 5-7 remain.

- **Phase 1 (DONE):** Hugo scaffolding — `hugo.toml`, base templates, partials, static asset migration (CSS, JS, fonts, images), symlinked media files.
- **Phase 2 (DONE):** Editorial pages — `scripts/fetch_pages.py` fetches 25 pages from `/api/site_pages` with HTML block content and internal link rewriting. Converted to clean markdown via `scripts/html_to_markdown.py`.
- **Phase 3 (DONE):** Items — initial fetch of all 79,261 items from `/api/items`.
- **Phase 4 (DONE):** Hugo-native restructuring — replaced Omeka's 7-type ID-based model with 3 content types (Document, Collection, Repository) + 7 taxonomies. Eliminated ~35k Image/Name/Microfilm/Publication pages. Transcriptions moved to markdown body with tabbed human/AI UI. Images resolved via `data/media_map.json` data lookup.
- **Phase 5 (TODO):** Media download — `scripts/fetch_media.py` paginates `/api/media` (84,870 items), downloads missing files. Files come in 3 sizes: large, original, square.
- **Phase 6 (TODO):** News posts — write `scripts/extract_news.py` to parse ~51 blog posts from `wardepartmentpapers.org/news/` wget HTML into `content/news/{slug}.md`.
- **Phase 7 (TODO):** Search + polish — Pagefind integration, search page, static archive banner, remove Matomo analytics.
