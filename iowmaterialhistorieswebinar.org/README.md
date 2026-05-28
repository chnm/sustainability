# iowmaterialhistorieswebinar.org

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://iowmaterialhistorieswebinar.org/`

**Run**

- started:   2026-05-27 16:13:12
- finished:  2026-05-27 16:13:49
- duration:  37s (wrapper) · 37s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 57 files, 1.2M (42.5 MB/s)
- links converted: 49 files in 0.03s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 57 | 3 | 1 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (1)

| status | url |
|--------|-----|
| 404 | https://iowmaterialhistorieswebinar.org/s/Material-Histories/page/four-objects-video |

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered stays as the absolute origin URL, will 404 when live site is gone.

| attr    | count |
| ------- | ----: |
| `src=`  |     0 |
| `href=` |    19 |

**Top broken path prefixes**

| count | prefix                            |
| ----: | --------------------------------- |
|    46 | `s/Material-Histories/index/`     |
|    17 | `files/original/`                 |
|     2 | `s/Material-Histories/page/`      |

No local `files/` dir; all Omeka media-derivative dirs were excluded at crawl time. The 19 broken `href`s are mostly absolute-form references to local `s/Material-Histories/...` HTML twins that wget didn't rewrite — they'd resolve if the host were stripped.
