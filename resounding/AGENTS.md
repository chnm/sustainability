# AGENTS.md

A self-contained static archive of [resoundingthearchives.org](https://resoundingthearchives.org/) — a digital-humanities project from RRCHNM/GMU + UVA + Virginia Tech that collected 17 World War I sheet-music recordings performed by student musicians. The original was a Drupal 7 site that was being decommissioned; this repo is the preservation copy. The audio plays, the PDFs render, and there are no third-party runtime dependencies.

This document is the rapid orientation. **PLAN.md** has the full multi-phase plan, the rationale for each decision, and the Phase A → D narrative.

## Layout

```
resounding/
├── PLAN.md                            # planning + decisions log (committed)
├── AGENTS.md                          # this file (committed)
├── CLAUDE.md                          # symlink → AGENTS.md (committed)
├── README.md                          # ← TODO: not yet written
├── .gitignore                         # excludes the gitignored paths below
├── index.html, browse.html, about.html
├── <17 song slug pages>.html          # canonical song URLs
├── node/<N>.html                      # alias pages: /node/N → song page
├── sites/all/                         # Drupal theme assets (CSS-referenced images)
├── sites/default/files/   [GITIGNORED] # heavy regenerable content (~162 MB):
│                                      #   51 MP3s, 17 PDFs, song images,
│                                      #   Drupal-aggregated CSS/JS bundles,
│                                      #   vendored Google Fonts woff2
├── pagefind/              [GITIGNORED] # client-side search index (~860 KB)
├── scripts/               [GITIGNORED] # build tooling
└── manifests/             [GITIGNORED] # Phase B crawl artifacts
```

The committed tree is small (≈1.5 MB). Everything heavy is regenerable by `scripts/export.py` from the wget mirror + Drupal backups + `npx pagefind`.

## Live endpoints (docker-host)

| Port | What | Why |
|---|---|---|
| `http://10.112.113.211:8080/` | Live Drupal restore — real Drupal 7 + MySQL 5.7 fed from the original DB backup | Ground truth for `scripts/verify.py` |
| `http://10.112.113.211:8081/` | This static archive served by `caddy:alpine` | The thing we're shipping |

Both run on the same docker-host, attached to the `resounding_default` compose network so a single Playwright session can compare them.

## Common operations

| I want to… | Run |
|---|---|
| Rebuild the static site from sources | `python3 scripts/export.py` |
| Redeploy the static site to docker-host | `bash scripts/deploy.sh` |
| Re-verify static vs live (Phase D) | drive `scripts/verify.py` via the playwright/python container — see PLAN.md Phase D |
| Re-crawl the live Drupal (Phase B) | `scripts/explore.py` (Playwright over CDP) |
| Bring up / restart the Drupal restore | `bash /workspace/resoundingthearchives.org/scripts/restore_db.sh` |

`scripts/export.py` is idempotent: it wipes the build-output entries (HTML, `node/`, `sites/`, `pagefind/`) without touching `PLAN.md`, `AGENTS.md`, `.gitignore`, `scripts/`, `manifests/`, or `.git`.

`docker` and `docker compose` always run with `DOCKER_HOST=ssh://docker-host`. The deploy + restore scripts set this themselves; if you're running raw docker commands, export it.

## Build tooling lives outside git

`scripts/` (export.py, explore.py, verify.py, deploy.sh) is intentionally **gitignored** — only served content lives in this repo. The local working tree has them; a fresh clone won't. To recreate them:

- **PLAN.md** describes what each script does in enough detail to rebuild from scratch — Phase A.5 (restore_db.sh), Phase B (explore.py), Phase C.1 (export.py), Phase D (verify.py).
- The Drupal-restore tooling (`compose/drupal.yml`, `compose/web.Dockerfile`, `compose/settings.local.php`, `restore_db.sh`) lives separately at `/workspace/resoundingthearchives.org/{compose,scripts}/`, also outside git.

If you're an agent working on a fresh clone and `scripts/` is missing, **stop and ask the user** — don't speculatively rebuild.

## Conventions

- **URLs.** Canonical song URLs are slug-based (`over-there.html`); `/node/N.html` exists as an alias for the same content. Internal links use slug URLs everywhere except the `node/*.html` aliases themselves. The browse-page card "View" buttons were rewritten from `node/N.html` to slug URLs at export time so search-result URL matching is direct.
- **No live-host references.** `https://resoundingthearchives.org/...` must not appear in any committed text-y file. `scripts/export.py` step 8a hard-checks this.
- **Relative paths only.** Every `(href|src)=` resolves to an on-disk file under the repo. `scripts/export.py` step 8b hard-checks this too.
- **Webfonts vendored.** `sites/default/files/fonts/*.woff2` plus inlined `@font-face` rules in the Drupal-bundled CSS — no `fonts.googleapis.com` / `fonts.gstatic.com` requests at runtime.
- **No third-party runtime requests.** Matomo, Google Docs PDF viewer, YouTube embeds — all stripped at export time. Verified by Phase B + D.
- **Pagefind annotations.** `data-pagefind-ignore` on `<html>` skips a page from search indexing (used on `browse.html` to avoid dominating every result, and on every `node/N.html` to avoid duplicate slug-page hits). `data-pagefind-meta="title:..."` on indexed pages overrides Pagefind's default title-extraction (which would otherwise pick up the masthead `<h1>` "ReSounding the Archives" everywhere).

## Who decided what

The "why" behind each shape (MySQL 5.7 not 8, Playwright over CDP not local headless, C.1 enrich-the-mirror over C.2 snapshot-export, `<iframe>` not `<embed>` for PDFs, vendored fonts) is documented in PLAN.md alongside the resolved questions and locked decisions. Read PLAN.md before reversing any of those.
