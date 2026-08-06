# OneTable: Shabbat Together

**A flattened static archive of the Pandemic Religion Omeka S site
`onetable.collectingthesetimes.org`.**

One of the *Collecting These Times* sub-collections in the Pandemic Religion
project, preserved as a self-contained static copy of the live Omeka S site for
long-term sustainability. Flattened from a `wget --mirror` capture with
`scripts/pandemicreligion_flatten.py`.

## Media is external

To keep the archive lean, **no media is committed**. Item images, downloads, and
site assets are referenced root-relatively (`/files/...`); flattening dropped
everything under `files/`. In deployment, Caddy serves `/files/...` from the
shared Pandemic Religion object-storage bucket (the seven Omeka S sites shared a
single `files/` store, so every site fronts the same bucket). In a bare local
preview (`python3 -m http.server`) media requests 404; page text and chrome are
unaffected.

## Search

Search is powered by **[Pagefind](https://pagefind.app/)**, a fully client-side
static index — the original Omeka search POSTed to the server and is dead in a
static mirror. The header search box submits (`?query=`) to `search.html`, which
runs the query. Only item, item-set, page, and home content is indexed;
browse/search permutation pages are excluded.

Rebuild the index whenever page content changes:

```sh
cd onetable.collectingthesetimes.org
npx pagefind@1.5.2 --site .   # regenerates pagefind/
```

The prebuilt `pagefind/` index is committed, because the deploy pipeline only
copies files (no build step).

## Local preview

```sh
cd onetable.collectingthesetimes.org
python3 -m http.server 8000
# open http://localhost:8000/index.html
```

Static servers (Python's `http.server`, nginx, Caddy) resolve the
`?`-in-filename Omeka S browse pages via `%3F` in the request URL. Or preview
with the bundled `Dockerfile` (Caddy `file_server`).

## Known limitations (inherent to a static capture)

- **Submission forms are disabled.** The Collecting "contribute / share your
  story" forms (and reCAPTCHA) POSTed to the live Omeka server; they cannot work
  statically and have been neutralized (`onsubmit="return false"`).
- **Analytics re-tagged.** The live pages carried two Matomo
  (`stats.rrchnm.org`) blocks (site + project roll-up, double-counting
  pageviews); the archive carries a single block, siteId `85`.

---

## Crawl provenance

### wget

Crawled by `multi-wget.py` on 2026-07-07.

**Seed:** `https://onetable.collectingthesetimes.org/`

**Run**

- started:   2026-07-07 01:18:39
- finished:  2026-07-07 01:19:32
- duration:  53s (wrapper) · 53s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 72 files, 8.5M (43.8 MB/s)
- links converted: 38 files in 0.02s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 72 | 2 | 1 | 0 |

#### Failures (1)

| status | url |
|--------|-----|
| 404 | https://onetable.collectingthesetimes.org/s/onetable/item/onetable.org |

#### Excluded (211)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 17 |
| LIST | `/files/large` | 18 |
| LIST | `/files/medium` | 7 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 164 |
| REGEX | 5 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).
