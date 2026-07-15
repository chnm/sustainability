# Preaching Goes Viral

**A flattened static archive of the Pandemic Religion Omeka S site `preachinggoesviral.org`.**

~12,800 items — the project's largest sub-collection. Flattened from a
`wget --mirror` capture with `scripts/pandemicreligion_flatten.py
--keep-browse-controls`; the browse spans many pages, so pagination controls and
the default-sorted paginated browse (item + item-set) pages are kept.

## Media is external

To keep the archive lean, **no media is committed**. Item images, downloads, and
site assets are referenced root-relatively (`/files/...`); flattening dropped
everything under `files/`. In deployment, Caddy serves `/files/...` from the
shared Pandemic Religion object-storage bucket (the seven Omeka S sites shared a
single `files/` store, so every site fronts the same bucket). In a bare local
preview (`python3 -m http.server`) media requests 404; page text and chrome are
unaffected.

## Search

**[Pagefind](https://pagefind.app/)** header search (committed `pagefind/`,
~56 MB over 12,830 pages; the browser only fetches the shards a query needs).
Rebuild with `npx pagefind@1.5.2 --site .`.

## Local preview

```sh
cd preachinggoesviral.org
python3 -m http.server 8000   # open http://localhost:8000/index.html
```

## Known limitations

- Sort dropdown / advanced-search inert in a static mirror (Pagefind is the
  working search). Analytics removed; item maps use committed Leaflet markers.

---

## Crawl provenance

### wget

Crawled by `multi-wget.py` on 2026-07-09.

**Seed:** `https://preachinggoesviral.org/`

**Run**

- started:   2026-07-09 18:37:55
- finished:  2026-07-09 23:25:34
- duration:  17264s (wrapper) · 4h 47m 39s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- links converted: 14038 files in 5.6s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 14063 | 2 | 2 | 0 |

#### Failures (2)

| status | url |
|--------|-----|
| 404 | https://preachinggoesviral.org/s/preaching-goes-viral/item/%20http://www.jstor.org/stable/j.ctv1j13zb3.26 |
| 404 | https://preachinggoesviral.org/s/preaching-goes-viral/item/%20http://www.jstor.org/stable/resrep26356.43 |

#### Excluded (43688)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 4233 |
| LIST | `/files/large` | 2191 |
| LIST | `/files/medium` | 5611 |
| LIST | `/files/square` | 2066 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 29417 |
| REGEX | 170 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).
