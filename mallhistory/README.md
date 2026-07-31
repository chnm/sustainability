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

