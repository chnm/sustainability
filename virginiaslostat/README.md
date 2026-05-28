# virginiaslostat.org

## wget

Crawled by `multi-wget.py` on 2026-05-28.

**Seed:** `https://virginiaslostat.org/`

**Run**

- started:   2026-05-28 16:47:24
- finished:  2026-05-28 16:49:29
- duration:  124s (wrapper) · 2m 4s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 212 files, 6.8M (9.85 MB/s)
- links converted: 199 files in 0.09s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 212 | 4 | 1 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (1)

| status | url |
|--------|-----|
| 404 | https://virginiaslostat.org/%5C%22https://virginiaslostat.org/items/show/53%E2%80%9D |

### Excluded (2703)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 471 |
| LIST | `/files/fullsize` | 110 |
| LIST | `/files/square_thumbnails` | 343 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 1182 |
| REGEX | 597 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered (see the `### Excluded` section above) stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  |   912 |
| `href=` |   628 |

**Top broken path prefixes**

| count | prefix                       |
| ----: | ---------------------------- |
|   479 | `files/original/`            |
|   343 | `files/square_thumbnails/`   |
|   340 | `items/`                     |
|   112 | `files/fullsize/`            |
|    75 | `\&quot;/items/show/`        |

No local `files/` dir; the `files/{original,square_thumbnails,fullsize}/` counts here line up with the `LIST` exclude counts above (471 / 343 / 110) — those dirs were explicitly excluded by the crawler's `-X` filter.
