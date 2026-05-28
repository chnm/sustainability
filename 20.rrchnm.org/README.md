# 20.rrchnm.org

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
