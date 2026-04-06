# AGENTS.md

> For feature specifications, business rules, and domain models, see [SPEC.md](./SPEC.md).

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Initialization](#project-initialization)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
  - [Data Pipeline](#data-pipeline)
  - [Template Dispatch](#template-dispatch)
  - [Omeka S API Reference](#omeka-s-api-reference)
- [Development Workflow](#development-workflow)
  - [Fetching Content](#fetching-content)
  - [Building the Site](#building-the-site)
  - [Serving Locally](#serving-locally)
- [Best Practices & Key Conventions](#best-practices--key-conventions)
- [Notes for AI Agents](#notes-for-ai-agents)

---

## Project Overview

Static Hugo site conversion of the Papers of the War Department (wardepartmentpapers.org), an Omeka S digital humanities archive. Uses a Hugo-native architecture with 3 content types (Document, Collection, Repository) and 7 taxonomies. Content is pulled from the live Omeka S REST API and rendered as static HTML. The site requires no database or application server.

---

## Tech Stack

### Static Site Generator
- **Hugo** v0.128.0+ (extended edition, with deploy support)
- Configuration: `hugo/hugo.toml`
- Requires `markup.goldmark.renderer.unsafe = true` for raw HTML content
- Uses `pagination.pagerSize` (not deprecated `paginate`)

### Data Extraction Scripts
- **Python 3** with `requests`, `beautifulsoup4`, `pyyaml`, `markdownify`
- Dependencies listed in `hugo/scripts/requirements.txt`
- Scripts fetch data from Omeka S REST API at `https://www.wardepartmentpapers.org/api/`

### Build Orchestration
- **GNU Make** via `hugo/Makefile`

### Search (Planned)
- **Pagefind** — post-build static search indexer

---

## Project Initialization

Prerequisites:
- Hugo extended v0.128.0+ (`brew install hugo`)
- Python 3 with pip

Setup:
```bash
cd hugo
uv pip install --system -r scripts/requirements.txt
```

If content files don't exist yet:
```bash
make fetch-pages    # ~30 seconds, fetches 27 editorial pages
make fetch-items    # ~60 minutes, fetches ~43,939 items from API
```

Static media files need to be symlinked from the wget'd copy:
```bash
ln -s ../../wardepartmentpapers.org/files static/files
```

Build and serve:
```bash
make build          # hugo --minify
make serve          # hugo server on localhost:1313
```

---

## Project Structure

```
pwd/
├── hugo/                          # Hugo project root
│   ├── hugo.toml                  # Site configuration (incl. taxonomies)
│   ├── Makefile                   # Build commands
│   ├── content/
│   │   ├── _index.md              # Homepage content
│   │   ├── {slug}.md              # 25 editorial pages (markdown)
│   │   ├── document/
│   │   │   └── {id}.md            # 42,880 documents (front matter + transcription body)
│   │   ├── collection/
│   │   │   └── {id}.md            # 818 collections
│   │   ├── repository/
│   │   │   └── {id}.md            # 241 repositories
│   │   └── news/
│   │       └── _index.md          # News index
│   ├── data/
│   │   ├── media_map.json         # image_id → [filenames] lookup
│   │   └── transcriptions_ai.json # AI transcriptions keyed by omeka_id (future)
│   ├── layouts/
│   │   ├── _default/
│   │   │   ├── baseof.html        # Base template (head, nav, footer partials)
│   │   │   ├── single.html        # Default single page (editorial content)
│   │   │   ├── list.html          # Default list page
│   │   │   ├── taxonomy.html      # Taxonomy list (all terms, e.g. /authors/)
│   │   │   └── term.html          # Taxonomy term (e.g. /authors/joseph-nourse/)
│   │   ├── index.html             # Homepage
│   │   ├── document/
│   │   │   └── single.html        # Document detail (metadata + transcription tabs)
│   │   ├── collection/
│   │   │   └── single.html        # Collection detail + linked documents
│   │   ├── repository/
│   │   │   └── single.html        # Repository detail
│   │   ├── news/
│   │   │   ├── single.html        # Blog post
│   │   │   └── list.html          # News index
│   │   └── partials/
│   │       ├── head.html           # CSS/JS includes
│   │       ├── nav.html            # Navigation menu
│   │       ├── footer.html         # Footer
│   │       └── item/
│   │           ├── document.html   # Document metadata partial
│   │           ├── repository.html
│   │           ├── collection.html
│   │           └── shared.html     # Shared notes partial
│   ├── static/
│   │   ├── files/                 # Symlink → wardepartmentpapers.org/files/
│   │   ├── css/style.css          # Main theme CSS
│   │   ├── css/iconfonts.css      # Font Awesome
│   │   ├── img/                   # Theme images
│   │   ├── fonts/                 # Font Awesome font files
│   │   ├── js/                    # JavaScript (tablesaw, global)
│   │   └── assets/                # Teaching PDFs
│   ├── static-media/
│   │   └── files/
│   │       └── media_catalog.json # Full media catalog from API
│   └── scripts/
│       ├── fetch_pages.py         # Fetch editorial pages from API
│       ├── fetch_items.py         # Fetch items (Document/Collection/Repository)
│       ├── fetch_media.py         # Fetch media catalog/files from API
│       ├── build_media_map.py     # Generate data/media_map.json
│       ├── html_to_markdown.py    # Convert editorial HTML to markdown
│       └── requirements.txt       # Python dependencies
├── wardepartmentpapers.org/       # wget'd copy of original site (reference)
│   ├── files/                     # ~26k media files (large/, original/, square/)
│   ├── s/home/                    # Original HTML pages
│   └── news/                      # WordPress blog posts
├── CLAUDE.md
├── SPEC.md
├── AGENTS.md
└── CHANGELOG.md
```

---

## Architecture

### Data Pipeline

```
Omeka S API (wardepartmentpapers.org/api/)
    │
    ├── /api/site_pages ──→ fetch_pages.py ──→ content/{slug}.md (markdown body)
    │
    ├── /api/items ────────→ fetch_items.py ──→ content/document/{id}.md (front matter + transcription body)
    │                                        ──→ content/collection/{id}.md
    │                                        ──→ content/repository/{id}.md
    │
    └── /api/media ────────→ fetch_media.py ──→ static-media/files/media_catalog.json
                                   │
                                   ▼
                           build_media_map.py ──→ data/media_map.json
                                                      │
                                                      ▼
                                              Hugo Build (hugo --minify)
                                                      │
                                                      ▼
                                              public/ (static HTML)
```

**Document content files** have transcription text in the markdown body (`.Content`). Metadata lives in YAML front matter and uses taxonomy lists (authors, recipients, etc.).

**Editorial pages have markdown body content** (converted from Omeka's HTML blocks). Some raw HTML remains, requiring `unsafe = true`.

### Template Dispatch

Each content type has its own layout directory:

| Type | Layout | Partial | Key Fields |
|---|---|---|---|
| Document | `document/single.html` | `item/document.html` | description, date, authors, recipients, sent_from, collections, image_id, doc_types, notable_persons/locations/items, transcription (body) |
| Collection | `collection/single.html` | `item/collection.html` | repository_name, repository_id, linked documents via `where` query |
| Repository | `repository/single.html` | `item/repository.html` | name, marc_code, address, phone |

Cross-references use Hugo taxonomies (authors, recipients, etc.) with links to `/authors/{slug}/`, `/recipients/{slug}/`, etc. Collections link to content pages at `/collection/{id}/`.

### Omeka S API Reference

Base URL: `https://www.wardepartmentpapers.org/api/`

Key endpoints used:
- `GET /items?per_page=100&page={n}&sort_by=id&sort_order=asc` — paginated items
- `GET /site_pages?per_page=100` — editorial pages
- `GET /media?per_page=100&page={n}` — media files (for future download script)

Pagination: Total count in `Omeka-S-Total-Results` response header.

Resource class IDs: 168=Repository, 169=Collection, 170=Microfilm, 171=Publication, 172=Name, 173=Image, 174=Document.

Item set IDs: 1=Repositories, 2=Collections, 3=Microfilms, 4=Publications, 5=Names, 6=Documents, 7=Images, 8=Transcription Project.

---

## Development Workflow

### Fetching Content

```bash
cd hugo
make fetch-pages     # ~30s, writes 25 editorial page files
make fetch-items     # ~60min, writes ~43,939 item files (0.1s delay between API pages)
```

The fetch scripts are idempotent — they overwrite existing files. Network errors auto-retry after 5 seconds.

To generate the media map (required for image display):
```bash
python3 scripts/fetch_media.py --catalog-only   # ~15min, writes media_catalog.json
python3 scripts/build_media_map.py               # instant, writes data/media_map.json
```

### Building the Site

```bash
make build           # hugo --minify, outputs to public/
```

Build produces ~49,000-54,000 pages (content + taxonomy terms + paginator pages + alias redirects).

### Serving Locally

```bash
make serve           # hugo server --bind 0.0.0.0, live reload
```

Hugo dev server at `http://localhost:1313/`.

---

## Best Practices & Key Conventions

### Front Matter Conventions
- Documents use `type: document`, collections use `type: collection`, repositories use `type: repository`
- Editorial pages use `type: page`
- `aliases` array provides old Omeka URL redirects (for Document/Collection/Repository only)
- `omeka_id` preserves the original Omeka item ID
- Taxonomy fields (`authors`, `recipients`, `collections`, `doc_types`, `notable_persons`, `notable_locations`, `notable_items`) are lists of strings
- Documents with transcriptions have the text in the markdown body (`.Content`)

### CSS/Asset Conventions
- CSS lives in `static/css/`, not Hugo's `assets/` pipe (no processing needed)
- Theme images in `static/img/`, media files symlinked in `static/files/`
- Font Awesome served locally from `static/fonts/`

### Template Conventions
- `baseof.html` defines `bodyclass` and `main` blocks
- Homepage sets `bodyclass` to `"page home"` to match original CSS selectors
- Partials use `{{ with .Params.field }}` pattern to skip empty fields
- Taxonomy links: `{{ "authors" | relURL }}/{{ . | urlize }}/`
- Collection content page links: `/collection/{{ .Params.collection_id }}/`
- Image resolution: `{{ index $.Site.Data.media_map (string .Params.image_id) }}`

---

## Notes for AI Agents

### Critical Constraints
- `get_all_literals()` in `fetch_items.py` must `.strip()` values — the Omeka API returns multi-valued properties with leading spaces.
- Hugo v0.128.0+ removed `paginate` in favor of `[pagination] pagerSize`. Do not use the old syntax.
- Editorial page HTML requires `markup.goldmark.renderer.unsafe = true` in `hugo.toml`.
- The `collections` taxonomy (`/collections/{slug}/`) and `collection` content type (`/collection/{id}/`) coexist — different URL patterns, no collision.
- `data/media_map.json` (~5MB) is loaded into Hugo memory at build time. Keep it as a flat lookup.

### When Modifying Fetch Scripts
- Changes to `fetch_items.py` require re-running the full fetch (~60 minutes, 793 API pages).
- For bulk fixes to existing files, prefer a Python script that modifies files in-place over re-fetching.
- Always test with `hugo` build after changes — YAML errors in content files will fail the build.

### When Modifying Templates
- Test with a representative item of each resource type. Good test items:
  - Document: document 79270 (has transcription, notable persons, all fields populated)
  - Collection: collection 783 (linked documents)
  - Repository: check low-numbered IDs (< 1000)
- Taxonomy pages: check `/authors/`, `/authors/{slug}/` for correct document listings.

### What Not to Do
- Do not add server-side functionality (PHP, Node, etc.) — the site must be purely static
- Do not remove Hugo aliases on Document/Collection/Repository pages — they preserve old URL compatibility
- Do not parse wget'd HTML for item data — always use the API (more complete, cleaner)
- Do not create content pages for Image, Name, Microfilm, or Publication types — these were intentionally removed

---
*Last Updated: 2026-03-11*
*This document is maintained for AI agent context and onboarding.*
