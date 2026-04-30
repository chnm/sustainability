# PLAN — Static rebuild of resoundingthearchives.org

## Context

The original site is a Drupal 7 install of "ReSounding the Archives" (RRCHNM/GMU + UVA + VT — WWI sheet music recordings by student performers). It is being decommissioned and we want a self-contained archival copy that opens from any static web server with no PHP, no database, and no dependency on the live `resoundingthearchives.org` host or third-party services.

Two source trees already exist:

- `/workspace/resoundingthearchives.org/wget/` — wget mirror of all rendered HTML, CSS, JS, theme assets, and most images. **Missing**: 51 MP3s and 17 PDFs (wget didn't follow them), and possibly other assets that were behind JS.
- `/workspace/resoundingthearchives.org/backups/var/{www/html/web,lib/mysql}/` — full `/var/www/html/web` PHP tree (Drupal 7.99) and a binary InnoDB MySQL data directory containing the `resoundthearch` database. Schema markers (`engine_cost`, `gtid_executed`, MyISAM system tables) point at **MySQL 5.7**.

### Why we are not just rewriting the wget mirror

A first pass at this would copy `wget/` → `site/`, fix relative paths, inline `<audio>` tags, and copy in the missing media. That works mechanically — but the original Drupal site was heavily JS-driven (jQuery audio replacement, Panels behaviors, possibly client-side filtering on the Browse page, Drupal AJAX). The wget mirror captures the **pre-JS DOM** for each URL it crawled. Anything the original site rendered or revealed via JS is invisible to wget. Guessing what those interactions did from the static HTML and then "restoring" them by hand is a recipe for silently losing features.

The right approach is to **stand the original Drupal site back up** in Docker on the remote `docker-host`, drive a real browser against it with Playwright, and **observe** what the live site actually does. Then export to static using the live site as ground truth, and verify the static export matches the live site by replaying the same Playwright traces.

## Infrastructure

### Remote Docker host

Containers run on the remote `docker-host` over SSH. **All `docker` and `docker compose` commands in this plan run from the local workspace shell with `DOCKER_HOST=ssh://docker-host` set; the daemon executes on the remote host.** Do not run containers locally — local CLI is aarch64, remote is x86_64, and most images we need are x86_64-only.

**SSH config** (`~/.ssh/config`):

```
Host docker-host
    HostName 10.112.113.211
    User moby
    IdentityFile ~/.ssh/id_ed25519_claude
```

**One-time setup before any docker command:**

```bash
# Accept the host key so the docker SSH dialer doesn't fail with "Host key verification failed"
ssh -o StrictHostKeyChecking=accept-new docker-host true

# Activate the SSH-based Docker context
export DOCKER_HOST=ssh://docker-host

# Install aarch64 buildx CLI plugin locally (the remote's x86_64 buildx won't run here)
mkdir -p ~/.docker/cli-plugins
curl -sSL -o ~/.docker/cli-plugins/docker-buildx \
  https://github.com/docker/buildx/releases/download/v0.21.1/buildx-v0.21.1.linux-arm64
chmod +x ~/.docker/cli-plugins/docker-buildx
```

**Networking quirks:**

- `docker-host` is not in local DNS. To curl deployed HTTP endpoints, use the IP: `http://10.112.113.211:<port>/`.
- Volume mounts in `docker run`/`compose` paths refer to paths on the **remote** filesystem (the daemon's view), not local paths. Sync data to `docker-host:/srv/<project>/` first via `rsync`, then mount that remote path.

**Inspection limitation:** Some images on docker-host (e.g. `stagex/*` distroless bases) have no shell — `docker exec <ctr> sh` fails. Use `docker cp <ctr>:/path /tmp/out` to inspect the filesystem instead.

### Playwright

A Playwright-enabled Chromium runs in a sidecar container on docker-host (image `mcr.microsoft.com/playwright:v1.44.0-jammy` or similar) with `--remote-debugging-port=9222` exposed on the host. Local Python scripts use `playwright.chromium.connect_over_cdp("ws://10.112.113.211:9222")` to drive it. This lets us observe JS behavior, capture network traffic, and assert against rendered DOM without installing a headed browser locally.

### Why explore live with Playwright instead of trusting the wget mirror

`wget --mirror` captures the **pre-JS DOM** for each URL it crawls. For a Drupal 7 site with jQuery-driven audio replacement, AJAX, possible client-side filtering on the Browse page, and Panels behaviors, anything rendered or replaced by JS is **invisible to wget**. Inferring those interactions by reading the JS source is fragile and silently loses features. The right move on any dynamic site is: restore the live site, drive it with a real browser, observe what actually happens, and let the manifest from that observation decide the export strategy. The wget mirror is still useful as a fallback baseline (Phase C.1) — but only after Phase B confirms it captures everything visible.

## Output layout

```
/workspace/resounding/
├── PLAN.md            # this file
├── README.md          # how to rebuild and serve
├── compose/
│   └── drupal.yml     # docker-compose for the live Drupal restore (MySQL 5.7 + PHP-Apache)
├── scripts/
│   ├── restore_db.sh  # bring up MySQL 5.7, point it at the backup, verify
│   ├── explore.py     # Playwright crawl of the live site — dumps a DOM/network manifest
│   ├── export.py      # Playwright-driven static export (renders each page, saves DOM + assets)
│   └── verify.py      # Playwright comparison of static `site/` vs live container
└── site/              # the publishable static site (output of export.py)
    ├── index.html
    ├── browse.html
    ├── about.html
    ├── <17 song slug pages>.html
    ├── node/<N>.html
    └── sites/{all,default}/...   # CSS, JS, images, MP3s, PDFs
```

## Phase A — Restore the live Drupal site in Docker

The MySQL data directory is a binary InnoDB snapshot, not a logical SQL dump. To read it we need the same major version of MySQL that wrote it.

### A.1 — Identify the source MySQL version

Indicators in `/workspace/resoundingthearchives.org/backups/var/lib/mysql/`:

- `mysql/engine_cost.frm` and `mysql/gtid_executed.frm` — both introduced in MySQL **5.7**.
- MyISAM-format system tables (`db.MYD`, `user.MYD`, etc.) — characteristic of MySQL 5.7 (8.0 dropped these).
- `auto.cnf` server UUID present.
- `ibdata1` is 76 MiB; `ib_logfile{0,1}` are 48 MiB each — default InnoDB layout.

Conclusion: restore with **`mysql:5.7`** (Docker Hub official image). MariaDB and MySQL 8 are likely to refuse or silently corrupt this data directory; do not substitute.

### A.2 — `compose/drupal.yml`

Two services on a private bridge network:

- **`db`** — `mysql:5.7`, volume-mounts `/workspace/resoundingthearchives.org/backups/var/lib/mysql/` read-write (we'll let it apply any needed upgrade). `MYSQL_ROOT_PASSWORD` set to a throwaway value but unused (auth comes from the existing `mysql.user` table). No port published — only reachable from `web`.
- **`web`** — `php:7.4-apache` with `mysqli`/`pdo_mysql`/`gd` extensions (built from a small Dockerfile), volume-mounts `/workspace/resoundingthearchives.org/backups/var/www/html/web/` to `/var/www/html`. Publish port 8080 → 80.

The compose file should mount the backup paths via the local-side path; since `DOCKER_HOST=ssh://docker-host`, the *daemon* sees those paths on the docker-host filesystem, so we'll need to either (a) sync the backup tree to `docker-host:/srv/resounding-restore/` first via `rsync`, or (b) build the data into a one-shot container image. Option (a) is simpler — a `scripts/restore_db.sh` runs `rsync -a /workspace/resoundingthearchives.org/backups/ docker-host:/srv/resounding-restore/` then `docker compose -f compose/drupal.yml up -d`.

### A.3 — `scripts/restore_db.sh` (sequence)

1. `rsync -a /workspace/resoundingthearchives.org/backups/ docker-host:/srv/resounding-restore/` (preserves permissions and timestamps; idempotent).
2. `docker compose -f compose/drupal.yml up -d db`.
3. Wait for healthcheck: `docker compose exec db mysqladmin -uroot ping`.
4. **Drupal `settings.php` rewrite.** Read `backups/.../web/sites/default/settings.php`; the DB host is whatever the original was (likely `localhost` via socket). Patch the database array to point at host `db`, port 3306 — write a sed/awk one-liner inside the container or supply a `sites/default/settings.local.php` override. The original DB credentials must match what's in `mysql.user`; if not, reset via `ALTER USER ... IDENTIFIED BY ...` after MySQL is up.
5. **Disable Drupal cache and Drupal-side trusted-host filter** via `settings.local.php` (`$conf['cache'] = 0;` and unset `$settings['trusted_host_patterns']`) so we can hit the site at `http://10.112.113.211:8080/` without a 400.
6. `docker compose -f compose/drupal.yml up -d web`.
7. Smoke test: `curl -sf http://10.112.113.211:8080/ | grep -q 'ReSounding the Archives'`.
8. If MySQL 5.7 refuses to start citing redo-log incompatibility, fall back to: stop the container, delete `ib_logfile0`/`ib_logfile1` from the rsynced copy (MySQL will recreate them), restart. Keep the original log files in `backups/` untouched.

### A.4 — Risks and mitigations

| Risk | Mitigation |
|------|------------|
| MySQL 5.7 refuses the data dir (collation, schema upgrade, etc.) | Try `--skip-grant-tables` first to bypass auth, then run `mysql_upgrade`. As a last resort, run an older 5.7 patch (`5.7.36`, `5.7.43`) — Docker tags are still available. |
| Drupal can't connect | Confirm credentials by reading `settings.php` from the backup; reset password in `mysql.user` if needed. |
| Trusted-host / base-url checks redirect to live URL | Set `$base_url = 'http://10.112.113.211:8080';` in `settings.local.php`. |
| File permissions inside `sites/default/files/` block writes | Drupal won't try to write at runtime if cache is off and admin isn't used. |
| Mail / outbound network in the container | `php.ini` set `sendmail_path = /bin/true`. |

## Phase B — Explore live behavior with Playwright

Goal: produce a manifest of every URL, every JS-driven interaction, every network request, so we know what "complete" means before exporting.

`scripts/explore.py` uses Playwright (Python, `playwright` package) over CDP to a Chromium running on docker-host. It does:

1. **Crawl from `/`**, following same-origin links breadth-first. Save a list of all reachable URLs.
2. For each page:
   - Wait for `networkidle`, then capture the post-JS DOM (`page.content()`).
   - Diff against the wget-captured HTML for the same URL. Any *added* DOM nodes are JS-rendered content we need to preserve in the export. Any *removed* nodes (e.g. `<div class="replaceme">` becoming `<audio>`) tell us what JS replacements happen.
   - Capture every network request (URL, status, content-type) — this surfaces lazy-loaded assets that wget missed.
3. **Click every visible interactive element** at least once: nav links, song "View" buttons, audio `<audio controls>` play buttons (assert audio loads), the PDF embed (assert it renders), any tab/accordion/filter on Browse, any modal triggers. Record each interaction's DOM diff.
4. **Browse-page filtering / search** — if the Browse page has client-side filtering or sorting, exercise each control and record the resulting DOM/URL state.
5. Output a JSON manifest at `manifests/live.json`: `{ urls: [...], js_added_selectors: {...}, network: [...], interactions: [...] }`.

Run output: a definitive list of (a) URLs to capture, (b) per-page JS-rendered content, (c) all assets the live site actually loads.

## Phase C — Static export

Two viable approaches; pick whichever the manifest says is cheaper:

### C.1 — Default: enrich the existing wget mirror

If Phase B shows the JS work is limited to (i) replacing `<div class="replaceme">` with `<audio>`, (ii) Drupal admin/menu chrome we don't need, and (iii) the Google Docs PDF iframe — i.e. nothing the user actually sees beyond the documented patterns — then a small rewrite script over `wget/` is sufficient. Steps:

1. Copy `wget/` → `site/`, excluding `wget.log`.
2. Rename the four `<thumb>?itok=<token>` files in `site/sites/default/files/styles/homepage_thumbs/public/` to drop the suffix. Same for any `?1382488163` files under the omega theme.
3. Copy from `backups/.../web/sites/default/files/`: all 17 `*.pdf`, all 51 `*.mp3`, plus any image referenced by HTML and not already in the wget tree.
4. Rewrite every `*.html` under `site/`:
   - Strip `https?://resoundingthearchives\.org/`. For `node/*.html`, prefix the now-relative paths with `../`.
   - Replace `<div class="replaceme">URL</div>` with `<audio controls><source src="URL" type="audio/mpeg">…</audio><div class="dllink"><a href="URL">Download Audio</a></div>` (mirrors the JS in `js_qq4t63...js`).
   - Replace the Google Docs PDF iframe with `<embed src="<local-pdf>" width="600" height="780" type="application/pdf">`.
   - Drop IE-conditional `<!--[if lte IE 8]>...<![endif]-->` blocks pointing at the live host, and the Matomo `<script>` block (`_paq`).
   - Strip `?itok=...` and `?1382488163` from `src=`/`href=` (handles raw `?` and `%3F`).
   - Strip `<link rel="canonical">` and `<link rel="shortlink">`.
5. Apply the same `?1382488163` strip to all `css_*.css` bundles.
6. Hard-check: zero `resoundingthearchives.org` substrings remain anywhere in `site/`, and every `(href|src)="..."` resolves to an on-disk file. Exit non-zero on violation.

### C.2 — Fallback: Playwright-driven snapshot export

If Phase B reveals JS-rendered content beyond the documented patterns (e.g. Browse-page client filtering, lazy-loaded assets, AJAX-injected nodes), `scripts/export.py` runs Playwright against the live container and saves the **post-JS DOM** for every URL in the manifest, plus every networked asset. Implementation: for each URL, `await page.goto(url, wait_until='networkidle')`, `await page.content()`, then for each network response cached during the load, write its body to `site/<path>` using the URL path. Strip absolute hosts and rewrite the same way as C.1 step 4.

Decide between C.1 and C.2 after running Phase B — don't pre-commit. The manifest from B will make the choice obvious.

## Phase D — Verify the static export against the live site

`scripts/verify.py`: Playwright opens the same URL twice — once against `http://10.112.113.211:8080/<path>` (live) and once against a local `python3 -m http.server` rooted at `site/`. Asserts:

1. `page.title()` matches.
2. The post-JS DOM tree (after stripping known dynamic attributes like `data-drupal-link-system-path` and the `<script>` and `<link>` tags whose hashes differ) is structurally identical.
3. The list of network responses matches in path and content-type. (Status 200 on the static side, possibly 200/304 on the live side.)
4. For each song page: live and static both have a working `<audio>` (audio metadata loads, `audio.duration > 0`) and a rendering PDF.
5. Visual diff via `page.screenshot()` + a pixelmatch threshold (allow ≤ 0.5% diff for font rendering jitter).

A green run of `verify.py` is the completion signal.

## Critical files

- `/workspace/resoundingthearchives.org/wget/` — pre-JS HTML mirror, baseline for Phase C.1
- `/workspace/resoundingthearchives.org/backups/var/lib/mysql/` — InnoDB data directory restored in Phase A; rsync target on docker-host
- `/workspace/resoundingthearchives.org/backups/var/www/html/web/` — Drupal 7 PHP tree restored in Phase A; volume-mounted into the `web` container
- `/workspace/resoundingthearchives.org/backups/var/www/html/web/sites/default/settings.php` — patch in Phase A.3 to point Drupal at the `db` service
- `/workspace/resoundingthearchives.org/backups/var/www/html/web/sites/default/files/` — source of MP3s and PDFs missing from the wget mirror
- `/workspace/resounding/compose/drupal.yml` — to be created in Phase A
- `/workspace/resounding/scripts/{restore_db.sh,explore.py,export.py,verify.py}` — to be created in Phases A–D

## Verification (end-to-end)

1. `bash scripts/restore_db.sh` brings up MySQL 5.7 + PHP-Apache; `curl -s http://10.112.113.211:8080/` returns the homepage HTML containing "ReSounding the Archives".
2. `python3 scripts/explore.py` writes `manifests/live.json` covering every reachable URL and interaction; exits 0.
3. `python3 scripts/export.py` writes the static site to `site/`; the script's hard-checks pass (no leftover absolute URLs, every referenced asset exists).
4. `cd site && python3 -m http.server 8000` serves the static site locally.
5. `python3 scripts/verify.py` passes against both endpoints.
6. Manual spot-check via Playwright in headed mode: each of the 17 song pages plays both audio versions, renders the PDF inline, shows all bio images. Browse and About work.

## Decisions already locked

- **PDF embed:** native `<embed src="local.pdf">` (not Google Docs viewer).
- **`?itok=` thumbnails:** rename to drop the suffix.
- **MySQL version:** 5.7 in Docker (not MariaDB, not 8.0).
- **Container host:** `docker-host` (`moby@10.112.113.211`) over SSH; do not run containers locally.
- **Browser automation:** Playwright (Python) over CDP to a Chromium on docker-host.

## Open questions to resolve in Phase A

- Does the Drupal site have any non-public URLs we should *not* include in the static export (admin pages, user profile pages, search forms requiring POST)? Phase B's crawler should default to following only links inside `<main>` / outside the admin region, but the exact boundary depends on what the live site exposes. Decide after the first Playwright crawl.
