# SPEC.md

> For technical implementation details, architecture, and developer documentation, see [AGENTS.md](./AGENTS.md).

---

## Table of Contents

- [Overview](#overview)
- [Users & Roles](#users--roles)
- [Business Rules](#business-rules)
- [Features](#features)
- [User Flows](#user-flows)
  - [Flow 1: Browsing by Taxonomy](#flow-1-browsing-by-taxonomy)
  - [Flow 2: Viewing a Document](#flow-2-viewing-a-document)
- [Out of Scope](#out-of-scope)
- [Open Questions](#open-questions)

---

## Overview

The **Papers of the War Department** (PWD) is a digital archive of documents from the U.S. War Department, 1784-1800, originally destroyed in a fire in 1800. The project, housed at the Roy Rosenzweig Center for History and New Media (RRCHNM) at George Mason University, reconstructed the collection by locating copies in repositories across the country.

The original site ran on Omeka S (a PHP/MySQL CMS for cultural heritage collections). This project converts it to a **Hugo static site** for long-term sustainability — no server, no database, no PHP runtime required. The static site preserves all documents, collections, repositories, 25 editorial pages, and associated media files using a Hugo-native architecture with taxonomies.

**Target audience:** Researchers, historians, educators, and students interested in early American military and government history.

**Primary goals:**
- Preserve all content and functionality of the original site in a server-free format
- Maintain URL compatibility for documents, collections, and repositories (`/s/home/item/{id}` redirects)
- Provide browsing, searching, and viewing of 42,880 documents, 818 collections, and 241 repositories
- Use Hugo taxonomies for cross-referencing (authors, recipients, notable persons/locations/items, collections, doc types)
- Ensure the site can be hosted on any static file server (S3, GitHub Pages, Netlify, etc.)

**Success metrics:**
- All documents, collections, and repositories accessible and rendering correctly
- Taxonomy pages correctly aggregate related documents
- Old URLs for retained types redirect to new locations
- Full-text search across collection via Pagefind
- Site builds and deploys without a database or application server

---

## Users & Roles

This is a **read-only public archive** with no authentication or user accounts.

### Public Visitor
- Full read access to all content
- Can browse items by type, paginated list
- Can search the collection
- Can view individual item detail pages with metadata and transcriptions
- Can access editorial pages (About, Guides, Teaching resources)
- Can view news/blog posts
- Cannot: edit, create, or delete any content

### Site Maintainer
- Runs Python fetch scripts to pull data from Omeka API
- Runs Hugo build to generate static site
- Deploys generated `public/` directory to hosting
- Can update editorial content by re-running fetch scripts or editing markdown files directly

---

## Business Rules

### URL Compatibility
- Document, Collection, and Repository pages have Hugo aliases for `/s/home/item/{omeka_id}`
- Every editorial page must have a Hugo alias for `/s/home/page/{slug}`
- Old URLs should 301 redirect to new Hugo paths
- Removed types (Image, Name, Microfilm, Publication) will 404 — no redirect stubs

### Item Data Integrity
- Items are fetched from the Omeka S REST API, not parsed from HTML
- Each item belongs to exactly one resource type determined by its `@type` in the API
- Multi-valued fields (notable persons, locations, items) must have leading/trailing whitespace stripped
- Documents with transcriptions store human-transcribed text in the markdown body

### Content Types
- 3 content types with pages: Document (42,880), Collection (818), Repository (241)
- 4 former types eliminated: Image (30,958), Name (4,180), Microfilm (128), Publication (56) — replaced by taxonomies and data lookups
- 7 taxonomies: authors, recipients, notable_persons, notable_locations, notable_items, collections, doc_types
- Documents are the primary content type with the richest metadata (authors, recipients, date, transcription, notable persons/locations/items)

### Editorial Pages
- 27 pages fetched from API, 25 written (home and collection slugs are skipped)
- Page content is raw HTML from Omeka block layout system
- Internal links in page HTML are rewritten to Hugo paths

---

## Features

### Feature: Document Browse

**Description:**
Paginated list of documents with thumbnails and titles.

**Functionality:**

- Paginated at 25 items per page
- Each document shows thumbnail (if available), title, and resource type
- Links to individual document detail page

---

### Feature: Document Detail View

**Description:**
Individual page for each document showing metadata, images, and transcription.

**Functionality:**

- Document pages display: description, date, authors (linked to taxonomy), recipients (linked), sent from, collection (linked to both taxonomy and content page), image gallery (via media map), document number, notable persons/locations/items (linked to taxonomies), transcription
- Transcription panel with tabbed UI: human transcription (from `.Content`) and AI transcription (future, from `data/transcriptions_ai.json`)
- Repository pages display: name, MARC code, address, phone, note
- Collection pages display: linked repository, note, and list of documents in the collection

---

### Feature: Taxonomy Browse

**Description:**
Browse documents by author, recipient, notable person, location, item, collection, or document type.

**Functionality:**

- Taxonomy list pages (e.g., `/authors/`) show all terms alphabetically with document counts
- Taxonomy term pages (e.g., `/authors/joseph-nourse/`) show paginated list of related documents

---

### Feature: Editorial Pages

**Description:**
Static editorial content pages (About, Guides, Teaching resources, etc.) pulled from Omeka site pages.

**Functionality:**
- Raw HTML content preserved from Omeka block system
- Internal links rewritten to Hugo paths
- Navigation menu with links to all editorial pages

---

### Feature: Search (Planned)

**Description:**
Full-text search across all 79,261 items using Pagefind.

**Functionality:**
- Post-build indexing via `npx pagefind --site public`
- Client-side search with filtering by type and year
- Search page at `/search/`

---

### Feature: News/Blog (Planned)

**Description:**
~51 blog posts from the original WordPress-based news section.

**Functionality:**
- Extracted from wget'd HTML files
- Individual post pages with author, date, categories
- Paginated news index

---

## User Flows

### Flow 1: Browsing by Taxonomy

**Goal:** Researcher finds documents by a specific author, recipient, or topic

**Starting Point:** Homepage or navigation menu

**Steps:**
1. User navigates to a taxonomy page (e.g., `/authors/`)
2. Sees alphabetical list of all authors with document counts
3. Clicks an author name (e.g., "Joseph Nourse")
4. Lands on paginated list of documents by that author
5. Clicks a document of interest

**Success Outcome:** User reaches document detail page with full metadata

---

### Flow 2: Viewing a Document

**Goal:** Researcher reads a document's metadata and transcription

**Starting Point:** Document detail page (via browse, search, taxonomy, or direct URL)

**Steps:**
1. User arrives at `/document/{id}/`
2. Sees document metadata: title, description, date, linked authors and recipients
3. Views document images (if available)
4. Reads transcription text via tabbed interface (human vs. AI)
5. Clicks linked author name to see taxonomy page with other documents by same person
6. Clicks linked collection to see the archival collection context

**Success Outcome:** User reads document transcription and navigates related documents via taxonomies

---

## Out of Scope

### Explicitly Excluded
- **Scripto/Transcribe functionality** — the original site had a crowdsourced transcription tool (Scripto); this requires a server and is not reproducible in a static site
- **User accounts and authentication** — no login, no user-created content
- **Matomo/analytics tracking** — removed from the static site
- **Dynamic search facets** — Pagefind provides full-text search but not Omeka-style faceted search by metadata field
- **IIIF image viewer** — the original site had a deep zoom viewer; static site shows thumbnail images only
- **Omeka admin interface** — content is managed via fetch scripts and Hugo builds, not a CMS

### Future Considerations
- Media gap-fill: downloading the ~58k media files not captured by wget from the API
- Enhanced search with Pagefind filters for year, resource type, author
- AI transcriptions via `data/transcriptions_ai.json` with tabbed comparison UI (infrastructure already in place)

---

## Open Questions

### Content Questions
- **Q:** Should the Transcription Project item set (set 8) items be surfaced differently?
  - **Context:** 1,246 items are in this set, representing the crowdsourced transcription effort
  - **Status:** Not yet addressed

- **Q:** How should we handle the static archive banner?
  - **Context:** Site should indicate it's a preserved archive, not an active project
  - **Options:** Top banner, homepage notice, footer text
  - **Status:** Planned for Phase 6

### Technical Questions
- **Q:** What hosting platform will the static site be deployed to?
  - **Context:** Affects baseURL configuration and deployment process
  - **Options:** GitHub Pages, Netlify, S3 + CloudFront, university hosting
  - **Status:** TBD

---
*Last Updated: 2026-03-11*
*This document is maintained for AI agent context and onboarding.*
