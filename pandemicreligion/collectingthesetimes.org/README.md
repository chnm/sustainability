# Collecting These Times

**A flattened static archive of the Pandemic Religion Omeka S hub site `collectingthesetimes.org`.**

Flattened from a `wget --mirror` capture with
`scripts/pandemicreligion_flatten.py --keep-browse-controls`. The browse spans
multiple pages here, so the pagination controls are kept and the default-sorted
paginated browse (item and item-set) pages are retained — next/prev works.

## Media is external

To keep the archive lean, **no media is committed**. Item images, downloads, and
site assets are referenced root-relatively (`/files/...`); flattening dropped
everything under `files/`. In deployment, Caddy serves `/files/...` from the
shared Pandemic Religion object-storage bucket (the seven Omeka S sites shared a
single `files/` store, so every site fronts the same bucket). In a bare local
preview (`python3 -m http.server`) media requests 404; page text and chrome are
unaffected.

## Search

**[Pagefind](https://pagefind.app/)** header search (committed `pagefind/`;
rebuild with `npx pagefind@1.5.2 --site .`). The sort dropdown and
advanced-search link are inert in a static mirror; Pagefind is the working
search.

## Local preview

```sh
cd collectingthesetimes.org
python3 -m http.server 8000   # open http://localhost:8000/index.html
```

## Known limitations

- Submission/contribute forms are replaced with a note (dead in a static mirror).
- Analytics (Matomo) removed. Item maps use the committed Leaflet marker images.

---

## Crawl provenance

### wget

Crawled by `multi-wget.py` on 2026-07-09.

**Seed:** `https://collectingthesetimes.org/`

**Run**

- started:   2026-07-09 14:11:32
- finished:  2026-07-09 14:32:25
- duration:  1258s (wrapper) · 20m 53s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 1269 files, 119M (2.31 MB/s)
- links converted: 1139 files in 6.2s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 1269 | 2 | 7 | 0 |

#### Failures (7)

| status | url |
|--------|-----|
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/svara.org |
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/tiny.cc/jewishmentalhealth |
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/asktherav.com |
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/CrownHeights.info |
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/kosherwine.com |
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/kashrut.com |
| 404 | https://collectingthesetimes.org/s/collecting-these-times/item/onetable.org |

#### Excluded (9901)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/admin` | 9 |
| LIST | `/files/original` | 1810 |
| LIST | `/files/large` | 1447 |
| LIST | `/files/medium` | 742 |
| LIST | `/files/square` | 834 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 5022 |
| REGEX | 37 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).
