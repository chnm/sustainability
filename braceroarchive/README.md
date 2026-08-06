# braceroarchive.org

## wget

Crawled by `multi-wget.py` on 2026-05-29.

**Seed:** `https://braceroarchive.org/`

**Run**

- started:   2026-05-29 01:31:57
- finished:  2026-05-29 04:29:13
- duration:  10636s (wrapper) · 2h 57m 16s (wget wall-clock)
- status:    `ok`
- downloaded: 9793 files, 179M (12.7 MB/s)
- links converted: 9740 files in 4.0s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 9793 | 12 | 0 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures

None.

### Excluded (123958)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 3745 |
| LIST | `/files/fullsize` | 2368 |
| LIST | `/files/square_thumbnails` | 6183 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 68203 |
| REGEX | 31157 |
| LIST | 12296 |
| SPANNEDHOST | 6 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).
