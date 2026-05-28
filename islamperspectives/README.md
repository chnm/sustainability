# islamperspectives.org

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://islamperspectives.org/`

**Run**

- started:   2026-05-27 16:00:32
- finished:  2026-05-27 18:05:39
- duration:  7513s (wrapper) · 2h 5m 8s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 9558 files, 375M (17.0 MB/s)
- links converted: 9460 files in 5.6s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 9924 | 160 | 0 | 5 |

_The initial crawl returned 371 HTTP 500s (all transient, never retried by wget1 by default). A follow-up direct `wget --retry-on-http-error=500 --tries=5 --wait=2 --waitretry=10` recovered 366 of them; the 5 still listed below are genuinely server-side permanent 500s. Response counts above are post-retry._

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (5)

| status | url |
|--------|-----|
| 500 | https://islamperspectives.org/rpi/podpriatov_intro |
| 500 | https://islamperspectives.org/rpi/exhibits/show/one/item/8872 |
| 500 | https://islamperspectives.org/rpi/items/show/Duplicates%20http%3A//islamperspectives.org/rpi/items/show/16892 |
| 500 | https://islamperspectives.org/rpi/application/views/scripts/images/blue-arrow.png |
| 500 | https://islamperspectives.org/rpi/application/views/scripts/images/blue-arrow_sm.png |

## Surviving absolute URLs to dead origin

In-tree HTML scan (2026-05-28). `--convert-links` only rewrites refs to files wget actually downloaded — anything filtered stays as the absolute origin URL, will 404 when live site is gone.

| attr    |  count  |
| ------- | ------: |
| `src=`  |   6,509 |
| `href=` | 207,761 |

**Top broken path prefixes**

|  count | prefix                                              |
| -----: | --------------------------------------------------- |
| 198421 | `rpi/items/`                                        |
|  12183 | `rpi/`                                              |
|   9808 | `rpi/commenting/comment/`                           |
|   2965 | `rpi/files/thumbnails/`                             |
|   2490 | `rpi/plugins/Dropbox/files/1916_R/Rosarkhiv_images_PDFs/` |

No local `files/` dir under `rpi/`; all Omeka media-derivative dirs were excluded at crawl time. Note: the vast majority of the 198k `rpi/items/...` `href`s point to item pages that *do* have local HTML twins — wget left them absolute because Omeka emitted them with the full origin URL. They'd resolve if the host were stripped.
