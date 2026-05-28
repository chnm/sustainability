# transatlanticencounters.rrchnm.org

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://transatlanticencounters.rrchnm.org/`

**Run**

- started:   2026-05-27 16:05:42
- finished:  2026-05-27 16:12:02
- duration:  380s (wrapper) · 6m 20s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 645 files, 26M (23.4 MB/s)
- links converted: 607 files in 0.3s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 645 | 0 | 3 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (3)

| status | url |
|--------|-----|
| 404 | https://transatlanticencounters.rrchnm.org/photos/sena-cabre.jpg |
| 404 | https://transatlanticencounters.rrchnm.org/a |
| 404 | https://transatlanticencounters.rrchnm.org/kadaster.nl |

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  | 1,985 |
| `href=` | 6,973 |

**Top broken path prefixes**

| count | prefix                       |
| ----: | ---------------------------- |
|  4832 | `items/`                     |
|  1704 | `items/show/`                |
|  1557 | `files/square_thumbnails/`   |
|  1275 | `files/original/`            |
|   597 | `search`                     |

Locally surviving under `files/`: `theme_uploads/`. All Omeka media-derivative dirs (`files/{original,square_thumbnails,fullsize,thumbnails}/`) were excluded at crawl time.
