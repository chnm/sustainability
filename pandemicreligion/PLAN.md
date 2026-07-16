# Plan: Flatten the Pandemic Religion Omeka S sites into static archives

> **Status:** design only — **to be implemented in a later session.** This
> document is the agreed approach; no conversion has been run yet.

## Context

The Pandemic Religion project comprises **7 live Omeka S sites** (a hub plus
six satellites). For sustainability we want a **flattened static archive** of
each, committed to `chnm/sustainability` under `pandemicreligion/<site>/`, and
deployed via the repo's standard reusable deploy workflow. The static copies
preserve the HTML/browse experience while the live Omeka servers keep serving
the heavy media, so the archives stay lean and survive if Omeka is ever retired
in favor of the static flip.

Source captures already exist: `wget --mirror` runs under
`/workspace/wgets/pandemicreligion/<domain>/`, produced by the
**websites-mirrorer** toolchain at `/workspace/util/websites-mirrorer/`
(`multi-wget.py` driven by `sites.toml`), which deliberately **excluded**
`/files/{original,large,medium,square,thumbnail}` and `/iiif/` — so item media
was never downloaded and is already referenced as absolute URLs on the live
domain. That same toolchain ships `gen-readmes.py`, the README generator we use
below (§3). The most recent completed conversion,
`/workspace/sustainability/plastercast/`, is the template for structure,
Pagefind search, Caddy serving, and README style — but plastercast is Omeka
**Classic** (`items/show/N`) whereas these are Omeka **S** (`/s/<slug>/item/N`),
and plastercast kept media locally whereas here **no media is committed**.

**Decisions locked with the user:** Search = **Pagefind** (as plastercast).
Media = **externalize + drop everything under `/files/`**. Deploy: **prod = the
existing live domain, dev = `<label>.dev.chnm.gmu.edu`**. Scope: **pilot the 3
small collectingthesetimes subsites first (hazon, kahal, onetable)**, verify,
then scale to the four large sites.

`/workspace/omeka-to-hugo` (a DB-dump → Hugo converter) is **reference only** —
we are doing wget-flatten (pre-rendered HTML served as-is), not a DB rebuild.

### `.crawl/` reference artifacts

Each capture has a `<domain>/.crawl/` directory holding the crawler's own logs.
It is **gitignored** (never copied into the static site), but it is the
authoritative reference when a page looks missing or a link 404s during
conversion:

- `wget.log` — the full wget run (every URL fetched, with HTTP status).
- `failures.tsv` — URLs that errored (timeouts / 5xx / 4xx); check here first if
  a content page is absent from the capture.
- `rejected.log` / `excluded.tsv` — URLs wget **intentionally skipped** per the
  crawler's `exclude_dirs` / `exclude_patterns` (media dirs, admin, search/sort
  permutations). If a "missing" page appears here, it was excluded by rule, not
  lost.
- `crawl.log` / `20260707-*_summary.tsv` (in the parent dir) — per-site run
  status and 2xx/3xx/4xx/5xx tallies.

Workflow: if conversion surfaces a broken intra-site link, grep the `.crawl`
logs for that URL to decide whether to (a) re-fetch it from the still-live site,
(b) drop the link as excluded cruft, or (c) treat it as a genuine dead end.

## The 7 sites

| subdir (`pandemicreligion/<site>/`) | Omeka slug(s) | items | notes |
|---|---|---|---|
| `hazon.collectingthesetimes.org` | hazon | 7 | **pilot** |
| `kahal.collectingthesetimes.org` | kahal | 18 | **pilot** |
| `onetable.collectingthesetimes.org` | onetable | 17 | **pilot** |
| `collectingthesetimes.org` | collecting-these-times | 189 | scale |
| `americanjewishlife.org` | american-jewish-life | 685 | scale |
| `preachinggoesviral.org` | preaching-goes-viral | ~6,400 | scale (large) |
| `pandemicreligion.org` | contributions + american-jewish-life + preaching-goes-viral | ~7,500 | scale (hub, large) |

`pandemicreligion.org` is a hub that also serves the AJL and PGV slugs; the two
standalone domains re-serve that same content on their own domain. We keep all 7
as faithful per-domain archives (item media in each capture already points at its
own domain, so no cross-site rewriting is needed).

## Approach

Build **one reusable conversion script** + a **per-site post-processing** step
(Pagefind, Dockerfile, README), then a **single matrixed deploy workflow**. Run
the pipeline on the 3 pilot sites end-to-end and verify before scaling.

### 1. Conversion script — `scripts/pandemicreligion_flatten.py`

New script (siblings the existing `scripts/crawler/`). Signature:
`flatten(src_dir, domain, out_dir)` where `domain` is the wget dir name (== the
live domain, e.g. `hazon.collectingthesetimes.org`). Steps, in order:

1. **Copy tree** `src → pandemicreligion/<site>/`, **excluding** `.crawl/`, the
   old `.gitignore`, and the entire `files/` directory (no media committed).
2. **Prune wget cruft** — delete query-string permutation HTML whose filename
   matches junk patterns (advanced search / facet combos): `item??*`,
   `item?*fulltext_search*`, `item?*property[0]*`, `item?*resource_*id*`,
   `item?*site_id*`, `item/*?page=*`, `*?sort_*`, and malformed
   `item?https*` (URL-in-filename). **Keep** `item/<id>.html`,
   `page/<slug>.html`, `item-set/<id>.html`, the site home `<slug>.html`,
   `index.html`, and the single-param nav browse pages `item?item_set_id=<N>.html`
   (these are linked from the nav). Pilot sites have 0–2 junk files; the rule set
   matters most for the two large sites.
3. **Externalize media** — over every `.html` and `.css`, rewrite relative
   `files/` references to absolute live-domain URLs:
   `(\.\./)+files/` and `"/files/` → `https://<domain>/files/`. Item `<img>`
   srcs are already `https://<domain>/files/{square,large,original}/…` and pass
   through unchanged. Net effect: nothing under `/files/` is referenced locally.
4. **Strip analytics** — remove the inline Matomo `<script>` block
   (`_paq` / `stats.rrchnm.org/matomo`) present in the shared header.
5. **Rewire search → Pagefind** — rewrite the header form
   `action="https://<domain>/s/<slug>/index/search"` to
   `action="search.html" method="get"` with input `name="query"` (root-relative
   `search.html`). Keeps the existing search box UI; Pagefind powers it.
6. **Neutralize dead submit forms** — the Collecting "contribute/share" pages and
   reCAPTCHA POST to the live server. For the pilot, leave the pages but disable
   the submit (mark as a known limitation in the README); revisit for scale.
7. **Keep as-is**: `application/`, `themes/`, `modules/` CSS/JS/fonts (essential,
   referenced relatively with the `%3F…` literal-`?` filename convention, served
   fine by Caddy — same pattern as plastercast), per-slug `css-editor.css`, and
   CDN scripts (jQuery via googleapis, Foundation via jsdelivr).
8. **Regenerate `.gitignore`** — minimal (`.DS_Store`, `errors.log`); the media
   exclusions are moot since `files/` isn't copied.

Internal nav links are already relative and `.html`-suffixed (e.g.
`../../hazon.html`, `../page/about.html`, `25092.html`,
`../item%3Fitem_set_id=129.html`), so **no link-rewriting is needed** beyond the
media/search/analytics passes above.

### 2. Pagefind search (per site)

Mirror plastercast (`/workspace/sustainability/plastercast/search.html`,
README §Search):
- Add root `search.html` hosting the Pagefind UI; it reads `?query=` and calls
  `ui.triggerSearch(q)`.
- Tag indexable content: add `data-pagefind-body` to the theme's main content
  container and `data-pagefind-ignore` to header/nav/footer. **Identify the exact
  content selector** in these Omeka S themes during the pilot (likely
  `#content`/`.page-content`) — the script injects the attributes.
- Build and commit the index: `cd pandemicreligion/<site> && npx pagefind@1.5.2 --site .`
  (committed because the deploy only copies files — no build step).
- Index only item/page/item-set content; exclude browse/search/media-metadata
  pages.

### 3. Serving + docs (per site)

- `Dockerfile` — copy plastercast's verbatim (Caddy `file_server`; `%3F`→`?`
  filename resolution handled automatically).
- `README.md` — **generated by the mirrorer's
  `/workspace/util/websites-mirrorer/gen-readmes.py`**, not hand-written per
  plastercast. That script reads each capture's `summary.tsv` +
  `<domain>/.crawl/{wget.log,crawl.log,failures.tsv,excluded.tsv}` and bakes the
  crawl provenance — seed URL, run timestamps, wget wall-clock/transfer numbers,
  the 2xx/3xx/4xx/5xx response table, startup warnings, the full failure list,
  and the collapsed excluded-rule summary — into a standalone `README.md`. This
  is the **durable record of the crawl**, since `.crawl/` itself is gitignored
  and never committed to the static site. Because `gen-readmes.py` reads from a
  `./mirrors/wget/` layout, the flatten step runs it against the captures (point
  `mirrors/wget` at `/workspace/wgets/pandemicreligion/` and its timestamped
  `*_summary.tsv` at `mirrors/wget/summary.tsv`) and lands the result as
  `pandemicreligion/<site>/README.md`. We then **prepend a short static-archive
  header** — one-line "flattened static archive of `<domain>`", the
  media-is-external note, the Pagefind rebuild command, and a local-preview
  snippet (as plastercast documents) — above the generated crawl section.
- Add a row per site to `/workspace/sustainability/README.md`, and fill this
  directory's top-level `README.md`.

### 4. Single deploy workflow — `.github/workflows/pandemicreligion--deploy.yml`

One file, **detect job (change detection) → matrixed deploy job** calling the
repo's external reusable workflow `chnm/.github/.github/workflows/static--deploy.yml@main`.
Validated design (matrix feeding a `uses:` job is supported; `include:` from an
empty array skips cleanly; the `uses:` path itself must stay a static literal):

```yaml
name: "Deploy Static Websites -- pandemicreligion"
on:
  workflow_dispatch:
    inputs:
      site:
        description: "Force-deploy one site, or 'all'"
        type: choice
        default: all
        options: [all, americanjewishlife.org, collectingthesetimes.org,
          hazon.collectingthesetimes.org, kahal.collectingthesetimes.org,
          onetable.collectingthesetimes.org, pandemicreligion.org,
          preachinggoesviral.org]
  push:
    branches: ["**"]
    paths: ['pandemicreligion/**', '!.github/**']

jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }   # need history for git diff
      - id: set
        env:
          DISPATCH_SITE: ${{ github.event.inputs.site }}
          BEFORE: ${{ github.event.before }}
        run: |
          sites=(americanjewishlife.org collectingthesetimes.org \
                 hazon.collectingthesetimes.org kahal.collectingthesetimes.org \
                 onetable.collectingthesetimes.org pandemicreligion.org \
                 preachinggoesviral.org)
          declare -A dev=(
            [americanjewishlife.org]=americanjewishlife.dev.chnm.gmu.edu
            [collectingthesetimes.org]=collectingthesetimes.dev.chnm.gmu.edu
            [hazon.collectingthesetimes.org]=hazon.dev.chnm.gmu.edu
            [kahal.collectingthesetimes.org]=kahal.dev.chnm.gmu.edu
            [onetable.collectingthesetimes.org]=onetable.dev.chnm.gmu.edu
            [pandemicreligion.org]=pandemicreligion.dev.chnm.gmu.edu
            [preachinggoesviral.org]=preachinggoesviral.dev.chnm.gmu.edu )
          # prod FQDN == the live domain (the site key itself)
          # choose changed set:
          if [ -n "$DISPATCH_SITE" ] && [ "$DISPATCH_SITE" != "all" ]; then
            changed=("$DISPATCH_SITE")
          elif [ "$DISPATCH_SITE" = "all" ] && [ -n "$DISPATCH_SITE" ]; then
            changed=("${sites[@]}")
          else
            base="$BEFORE"
            if [ -z "$base" ] || ! git cat-file -e "$base^{commit}" 2>/dev/null; then base="HEAD^"; fi
            mapfile -t files < <(git diff --name-only "$base" HEAD || git ls-files)
            changed=()
            for s in "${sites[@]}"; do
              printf '%s\n' "${files[@]}" | grep -q "^pandemicreligion/$s/" && changed+=("$s")
            done
          fi
          # emit JSON array of include objects (default '[]')
          json='[]'
          for s in "${changed[@]}"; do
            json=$(jq -c --arg s "$s" --arg dev "${dev[$s]}" \
              '. += [{site:$s, context_root:("pandemicreligion/"+$s), devl:$dev, prod:$s}]' <<<"$json")
          done
          echo "matrix=$json" >> "$GITHUB_OUTPUT"

  deploy:
    needs: detect
    if: ${{ needs.detect.outputs.matrix != '[]' }}
    strategy:
      fail-fast: false
      matrix:
        include: ${{ fromJSON(needs.detect.outputs.matrix) }}
    uses: chnm/.github/.github/workflows/static--deploy.yml@main
    secrets: inherit
    with:
      context_root: ${{ matrix.context_root }}
      website-devl-fqdn: ${{ matrix.devl }}
      website-prod-fqdn: ${{ matrix.prod }}
      runner_labels: '["self-hosted","IncusOS"]'
```

Dev-FQDN labels are inferred from the user's examples (`onetable.dev.chnm.gmu.edu`,
`kahal…`) — confirm the four full-domain ones (`americanjewishlife`,
`collectingthesetimes`, `pandemicreligion`, `preachinggoesviral`) before first
prod run. **Fallback** if matrix-over-reusable-workflow is ever rejected: keep
`detect` emitting a slug list and use 7 static
`if: contains(fromJSON(needs.detect.outputs.sites), '<site>')`-guarded jobs.

## Pilot scope (first implementation pass) then scale

**First pass:** write `scripts/pandemicreligion_flatten.py`; convert **hazon,
kahal, onetable** into `pandemicreligion/<site>/`; add Pagefind + Dockerfile +
README to each; author `pandemicreligion--deploy.yml`; verify locally. **Scale
(follow-up):** run the same pipeline on `collectingthesetimes.org`,
`americanjewishlife.org`, then the two large sites (`preachinggoesviral.org`,
`pandemicreligion.org`) — where the junk-prune rules and Pagefind index size
(thousands of pages) get real scrutiny.

## Critical files

- **New:** `scripts/pandemicreligion_flatten.py`; `pandemicreligion/<site>/`
  trees; per-site `search.html`, `Dockerfile`, `README.md`, `pagefind/`;
  `.github/workflows/pandemicreligion--deploy.yml`.
- **Edit:** `/workspace/sustainability/README.md` (project rows);
  `pandemicreligion/README.md`.
- **Reference (reuse patterns):** `plastercast/Dockerfile`,
  `plastercast/search.html`, `plastercast/README.md`,
  `.github/workflows/plastercast--deploy.yml`; the mirrorer toolchain at
  `/workspace/util/websites-mirrorer/` (`multi-wget.py`, `sites.toml`, and
  **`gen-readmes.py`** — the README generator run per site); and each capture's
  `<domain>/.crawl/` logs (see above).

## Verification

1. **Pilot build**: run the flatten script for the 3 sites; confirm no `files/`
   dir is committed and `grep -rl '\.\./.*files/' pandemicreligion/<site>` is
   empty (all media externalized).
2. **Local serve**: `cd pandemicreligion/hazon.collectingthesetimes.org &&
   python3 -m http.server 8000`; click through home → page → item → item-set;
   confirm `%3F` browse links resolve.
3. **Media**: in the browser network tab, item images load from
   `https://<domain>/files/…` (live domain), and there are **no** local
   `files/` 404s.
4. **Search**: rebuild Pagefind, load `search.html`, query a known term (e.g. a
   contributor/title), confirm results link to the right item pages.
5. **No dead calls**: confirm no requests to `stats.rrchnm.org` (Matomo removed)
   and the search box no longer POSTs to `/s/<slug>/index/search`.
6. **Workflow**: `actionlint` the YAML; dry-run the `detect` step logic locally
   (simulate `git diff` for a single-site change → matrix has exactly that site;
   no change → `[]` → deploy job skipped).
7. Optional (parity with plastercast): axe-core accessibility pass — treat as a
   later remediation, not a pilot blocker.

## Risks / open items

- **Prod == live domain**: the flip replaces live Omeka's HTML but the host must
  keep serving `/files/…` (media persists outside git) for external image links
  to resolve. Confirm the media dir survives the static flip on the prod host.
- **Dead submission forms** (Collecting contribute/share, reCAPTCHA) can't work
  statically — disabled and documented, not reconstructed.
- **Pagefind index size** on the 6k–7.5k-page sites may be large (committed);
  evaluate during scale (exclude non-content pages aggressively).
- **Content selector** for `data-pagefind-body` must be pinned from the actual
  Omeka S theme markup during the pilot.
- **Dev FQDNs** for the four non-pilot sites need user confirmation before prod.
