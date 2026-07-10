# American Jewish Life

**A flattened static archive of the Pandemic Religion Omeka S site `americanjewishlife.org`.**

Flattened from a `wget --mirror` capture with
`scripts/pandemicreligion_flatten.py --keep-browse-controls`. The browse spans
multiple pages here, so the pagination controls are kept and the default-sorted
paginated browse (item and item-set) pages are retained — next/prev works.

## Media is external

**No media is committed.** Item images/downloads reference absolute
`https://americanjewishlife.org/files/...` URLs on the live host; flattening dropped
everything under `files/`.

## Search

**[Pagefind](https://pagefind.app/)** header search (committed `pagefind/`;
rebuild with `npx pagefind@1.5.2 --site .`). The sort dropdown and
advanced-search link are inert in a static mirror; Pagefind is the working
search.

## Local preview

```sh
cd americanjewishlife.org
python3 -m http.server 8000   # open http://localhost:8000/index.html
```

## Known limitations

- Submission/contribute forms are replaced with a note (dead in a static mirror).
- Analytics (Matomo) removed. Item maps use the committed Leaflet marker images.

---

## Crawl provenance

### wget

Crawled by `multi-wget.py` on 2026-07-09.

**Seed:** `https://americanjewishlife.org/`

**Run**

- started:   2026-07-09 18:37:55
- finished:  2026-07-09 19:05:30
- duration:  1655s (wrapper) · 27m 35s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 1384 files, 191M (22.7 MB/s)
- links converted: 1252 files in 0.7s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 1384 | 4 | 8 | 0 |

#### Failures (8)

| status | url |
|--------|-----|
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/svara.org |
| 404 | https://americanjewishlife.org/%20 |
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/tiny.cc/jewishmentalhealth |
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/asktherav.com |
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/CrownHeights.info |
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/kosherwine.com |
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/kashrut.com |
| 404 | https://americanjewishlife.org/s/american-jewish-life/item/onetable.org |

#### Excluded (16570)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 1797 |
| LIST | `/files/large` | 1422 |
| LIST | `/files/medium` | 3053 |
| LIST | `/files/square` | 839 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 9295 |
| REGEX | 164 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).
