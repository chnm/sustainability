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
