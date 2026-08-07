# forustheliving.org Drupal 7 → Static Conversion — Build Log

This document records what was actually built. Reads top-to-bottom as the
operational record + how to re-run any step.

## Goal (delivered)

Drupal 7.99 site at `drupal/var/` → a fully static, login-free archive at
`static/` with client-side search via [Pagefind]. Live URL paths preserved.
Spam triaged before mirror. JS-driven content rendered as static markup
where possible; the few necessary interactions (home-page module modal,
header search button) re-implemented as ~20 lines of vanilla JS.

## Final state of `static/`

- **311 MB** total
- **459 HTML pages** at clean URL paths (no `.html` suffixes)
- **333 pages** indexed by Pagefind
- Theme assets at `sites/all/themes/{omega,arlington}/` (12 MB after pruning)
- Drupal core static at `misc/` (168 KB after pruning) and `modules/{book,comment,field,file,node,search,system,user}/`
- **Auth-surface audit:** 0 login forms, 0 user/login/register/password links, 0 `Drupal.settings` inline JSON, 0 `webform-client-form` / `comment-form` elements, 0 `http://web/` literal references, 0 `<link rel="shortlink">` to deleted feeds
- **Console-error audit (Playwright):** 0 errors / 0 failed requests across home, content, node, look-closer, resource, teach, search pages

## Inputs

| Path | What it is |
| --- | --- |
| `drupal/var/www/html/web/` | Drupal 7.99 docroot. Theme `arlington` (Omega base). |
| `drupal/var/lib/mysql/` | Raw MySQL data dir. Database `futl`, 449 InnoDB tables. |
| `drupal/var/www/html/web/sites/default/files/` | 297 MB uploads + cache. Kept: `webform/` (19 files), `pictures/` (3 files). |
| `drupal/var/www/html/web/sites/default/settings.php` | DB creds: db=`futl`, user=`futl`, host=`db`. |

## Outputs

- `static/` — flat HTML mirror with Pagefind search, login-free
- `wget/` — local pre-conversion copy of the raw wget mirror (preserved before any post-processing)
- `seed-urls.txt` — list of public URLs given to `wget`
- `compose.yml` — Drupal stack used for triage + crawl source
- `runtime/` — supporting scripts (compose helpers, crawl runner, scrub orchestrator, render+screenshot tools, cleanup scripts)
- `scripts/` — Python scripts (spam triage, deletion executor, scrub, asset copy, PHP 7.4 patches)
- (build-only on docker-host) `~/futl-flatten/artifacts/` — build logs (`wget.log`, `pagefind.log`); never copied into `static/`

## Infrastructure

All containers run on remote Docker host `moby@10.112.113.211` (SSH alias `docker-host`). Reserved ports 8000–9000.

`~/.ssh/config`:
```
Host docker-host
    HostName 10.112.113.211
    User moby
    IdentityFile ~/.ssh/id_ed25519_claude
    IdentitiesOnly yes
```

Local docker has `compose` plugin missing, so compose commands run via `ssh docker-host docker compose ...` rather than `DOCKER_HOST=ssh://docker-host docker compose ...`.

Stack at `compose.yml` (mounts the rsynced docroot + InnoDB data dir at fixed paths on the remote):

- `db`: `mysql:5.7`, mounts `drupal/var/lib/mysql` → `/var/lib/mysql`, healthcheck on port 3306
- `web`: `php:7.4-apache`, mounts `drupal/var/www/html` → `/var/www/html`, port 8080:80, first-run installs apt deps + PHP extensions (`gd mysqli pdo pdo_mysql opcache zip intl`) + Drush 8.4.12 + `pymysql`, then runs `apache2-foreground`
- shared `futl_futl` bridge network for runner containers (wget, scrub, pagefind) to reach `web` by its service name

`drupal/var/` was rsynced to `~/futl-flatten/drupal/var/` on docker-host (~840 MB, one-time). MySQL data dir was chowned to uid 999 to match `mysql:5.7`'s container user.

Drupal docroot was missing `.htaccess` (lost when the archive was created); a minimal Drupal-7-style `runtime/drupal.htaccess` was written into the docroot to make Drupal's clean-URL routing work under Apache.

---

## Phase 0 — Boot Drupal stack on docker-host

Container `futl-web-1` first run installs deps + drush + pymysql, then `apache2-foreground`.

Two Drupal contrib modules had PHP 7.4 incompatibilities that made `drush` unable to bootstrap:

1. `webform/components/select.inc` line 765 — closure parameter shadowed its captured variable. Patched in place to rename the captured variable to `$input_value`.
2. `rules/ui/ui.plugins.inc` lines 20+87 — both `RulesRuleUI::form()` and `RulesReactionRuleUI::form()` had signatures incompatible with the parent class. Added the missing `$iterator = NULL` parameter to both.

Patches in `scripts/patch_php74.py`. Idempotent.

Smoke check: `curl -sI http://10.112.113.211:8080/` → `200 OK`, `<title>Home | For Us the Living</title>`.

## Phase 1 — Spam triage

Comprehensive heuristic-driven triage. Source: `scripts/triage_spam.py` (pymysql, runs in the `web` container against the `db` service on the compose net).

**Discovery:** site had **16,426 webform submissions** (one form had 7,444 submissions, 7,421 of which were anonymous post-2018 — clearly spam).

**Triage method:**

- **Webforms:** scored each row on URL count, non-Latin script presence (Cyrillic/CJK), spam-keyword density (kraken/onion, casino, contraband-style spam), anonymous-after-course-window flag. Result:
  - HIGH (auto-delete): 11,854
  - MEDIUM (review): 1
  - LOW (keep): 4,571
- **Users:** scored on email TLD, name-digit-tail patterns, registration-burst clustering (within 90s of ≥3 other accounts), zero-content + never-logged-in. Then `scripts/triage_users_breakdown.py` re-bucketed against legitimate webform submissions:
  - `blocked_already`: 26 (status=0, all `*.emvps.xyz` bot emails)
  - `spam_tld`: 3 (active `.xyz`/`.cdn5.emvps.xyz` accounts)
  - `post_course_inactive`: 80 (post-2019, no nodes, no real submissions, throwaway domains)
  - `class_roster`: 130 — legitimate students, **kept**
  - `kept_active`: 59 — logged-in users with content, **kept**
- **Comments:** 0 found in DB
- **Nodes:** 489 nodes, none flagged as spam (the 7 with `uid=0` were 2016/2017 class entries, not spam)

**Sample HIGH webform spam confirmed:**
```
sid=4732  uid=0  "In areas the place the inhabitants accommodates extraordinarily low numbers of l..."
sid=10028 uid=0  "<a href=http://pint77.com/all-for-kids.html> KUZEMA personalised baby gifts..."
sid=13358 uid=0  "LoveShop  снова работает!!!  Подробнее  https://telegra.ph/Shop1-biz-ras..."
```

**User-approved deletions** (executed by `scripts/triage_delete.py`):
- 11,854 webform submissions (direct SQL, batched 1,000 at a time, ~2s)
- 109 users (drush `user_delete()` for safe cascade across 5+ tables, ~5s)

**Verification:** `webform_submissions` 16,426 → 4,572. `users` 300 → 189. `webform_submitted_data` orphan check: 0.

UTF-8 decode bug discovered during triage (mixed encoding in spam payloads); pymysql connection switched to `use_unicode=False` with safe-decode wrapper.

## Phase 2 — Pre-mirror hygiene

Disabled 9 interactive contrib modules (`ajax_comments`, `webform_ajax`, `login_destination`, `user_registrationpassword`, `og*`). Closed all comment forms to read-only (mode=1). Hid `block.module='user'|'search'`.

CSS/JS aggregation **disabled** (`drush vset preprocess_css 0; preprocess_js 0; cache 0`). Without this, Drupal serves CSS via aggregator URLs that get saved as broken empty-path stylesheets.

Three more redirect modules disabled (`globalredirect`, `redirect`, `subpathauto`) to fix internal redirect loops on taxonomy aliases like `/year/2018-19`.

Initially also closed all webforms (`UPDATE webform SET status=0`), but **reopened** them after discovering this hid all the lesson plan instructional markup. Forms were closed via the scrub instead — webform `<form>` elements get converted to display-only `<div>` containers preserving instructional text + question prompts but stripping inputs/buttons.

`drush vset error_level 1` — silence PHP notices on rendered pages.

`scripts/gen_seed_urls.php` — drush php-script that walks `{url_alias}` ∪ `{node WHERE status=1}` ∪ taxonomy aliases, filters out `/user/*`, `/admin/*`, `/comment/*`, `/node/add/*`, `/filter/tips`, `/search/*`, `?destination=`, `?q=`. Output: 718 seed URLs.

## Phase 3 — Static mirror via wget

Detached `alpine:3.20` runner on `futl_futl` network, `wget` invoked from `runtime/crawl.sh`:

```sh
wget --recursive --level=inf --page-requisites --convert-links \
     --no-host-directories --no-parent \
     --execute robots=off --tries=2 --timeout=30 --waitretry=2 \
     --reject-regex '(^|/)(user|admin|comment|node/add|filter/tips|search)(/|$)|\?(destination|q)=' \
     --domains=web --input-file=/artifacts/seed-urls.txt http://web/
```

Flag rationale:
- `-e robots=off` — Drupal's default robots.txt disallows `/themes/`, `/misc/`, `/sites/all/themes/...`. Honoring it would strip the theme.
- No `--adjust-extension` — would append `.html` to clean URLs like `/about`.
- No `--restrict-file-names=windows` — mangles `:` and other safe URL chars.
- `--no-host-directories` — output is `static/about/index.html`, not `static/web/about/index.html`.

Build artifacts (`seed-urls.txt`, `wget.log`) are written to a sibling `/artifacts` mount, not the `/out` (static) mount, so they never end up served.

**Raw mirror result:** 515 HTML pages saved at clean URL paths (no extension) + assets, ~3 minutes wall time.

A pre-conversion snapshot was preserved at `wget/` (288 MB, 641 files) before post-processing, so the unmodified mirror remains available.

**Coverage gap analysis** (`runtime/error_sample.sh`, `runtime/coverage.sh`):
- 1497 HTTP 404s — 156 were missing media files referenced from node bodies (pre-existing data loss in the archive itself; pages still link to them but show broken `<img>`/`<video>` like the live site does); rest were author typos in `<a href>`.
- 289 HTTP 403s — `users/*` profile pages, correctly bounced.
- 211 missing seeds out of 718 — 190 were `users/*` (login-only by design); 19 were `content/*` aliases pointing at unpublished nodes (`status=0` — should never have been seeded; the seed-URL query was joined too loosely); 1 home redirect; 1 dashboard redirect. Zero real content losses.

## Phase 4 — Scrub

`scripts/scrub_static.py` — single Python script that runs in a `python:3.12-slim` container, mounts `static/` and `scripts/` into the container, installs `beautifulsoup4` + `lxml` once, processes every HTML file in the tree.

**Filter:** identifies HTML by content-sniffing (`<!doctype html` or `<html>` in first 512 bytes) since wget saves clean URLs without extensions. Skips `sites/`, `modules/`, `misc/`, `pagefind/` directories so theme/module documentation HTML doesn't accidentally get indexed.

**Restructure:** every extensionless HTML file at `<path>` is moved to `<path>/index.html`, with relative URLs in attributes (`href`, `src`, `action`, `poster`, `data`, `srcset`, `style="...url(...)"`) and inside `<style>@import url(...)` blocks bumped one level deeper to compensate. This way the static host serves clean URLs without needing custom routing rules.

**Text-level preprocessing** (before HTML parsing):
- `http://web/` → `/` (host-rewrite)
- IE conditional `<html>` stanzas (`<!--[if ...]>...<html>...<![endif]-->`) replaced with single `<html lang="en" dir="ltr" class="no-js">` — needed because Pagefind couldn't detect language otherwise (no `lang` attribute in any non-conditional `<html>` tag)
- Cache-buster query strings (`?te68ox`, `?v=1.10.2`) stripped from CSS/JS/font/image URLs

**DOM-level scrub steps** (each idempotent, only writes file if content changed):

1. **Auth surface removal:**
   - Decompose `<form>` elements with `id`/`class` matching `user-login`, `user-register`, `user-pass`, `comment-form`, `webform-client-form`, `search-block-form`, or `action="/"` login forms.
   - Convert `<form class="webform-client-form">` to `<div class="webform-archived-content">` — preserves instructional `webform-component-markup`, headings, paragraphs, and field labels with descriptions; strips inputs/textarea/select/buttons/`form-actions`/`form-textarea-wrapper`/`form-required`. This recovers ~103 webform-page bodies that would otherwise be empty.
   - Drop `<a>` elements whose `href` matches `LOGIN_HREF_RE` (`/user`, `/user/login|register|password`, `/comment/reply/`). Walks up through empty wrappers (`linkholder` → `textholder`) and decomposes those too.
   - Drop `loginform`/`logininfo` themed dressing.
   - Drop `class="create"` "Teacher Registration" / "Create new account" anchors.

2. **Drop runtime-only JS includes** — replaced or harmful:
   - `lightbox2/js/lightbox.js` — no `rel="lightbox"` anchors anywhere; the script crashes on `Drupal.settings.lightbox2.overlay_opacity` since the Drupal.settings config is stripped.
   - `matomo/matomo.js` — analytics, no value without config.
   - `arlingtonUtility/parsley.min.js` — form validation, no forms.
   - `themes/arlington/js/arlington.behaviors.js` — its responsibilities (modal toggling, accordion clicks, glass clicks, `.toright` wrapAll, node-605 nextpart hide) are all replaced by the scrub's build-time markup or CSS overrides. Letting it run actively breaks pages: it re-applies `.toright` wrapAll on top of the already-wrapped DOM, nesting `.rightme > .rightme` and constraining the inner panes to half-width.
   - `themes/arlington/js/jquery.matchHeight.js` — only invoked by behaviors.js; redundant once that's gone.
   - `arlingtonUtility/arlingtonUtility.js` — custom AHAH callbacks; none of the surviving content uses them.

   After this scrub step, the only JS the archive ships is `drupal.js` + jQuery (used by Drupal core widgets that survived) + our injected `<script id="futl-archive-behaviors">` (15-line modal handler).

3. **Drop Drupal runtime status panes:** `<div class="pane-pane-messages">`, `messages--error`, `messages--warning`, `messages--status` — runtime PHP-notice / status-message containers don't belong in an archive.

4. **Drop `Drupal.settings` inline `<script>` JSON.**

5. **Drop RSS/Atom alternate-link tags:** `<link rel="alternate" type="application/rss+xml">` and `application/atom+xml` (38 pages affected). Underlying `taxonomy/term/*/feed` files also removed from disk.

6. **Drop Drupal shortlink discovery tags** (`<link rel="shortlink" href="/taxonomy/term/N">`) — the targets were deleted with the feeds.

7. **Drop broken stylesheet `<link>` tags** pointing to `index.html` or `http://web/` (artifacts of Drupal's CSS aggregator before we disabled it; wget had already saved a few).

8. **Look-closer page transformations:**
   - For pages with body class `node-type-look-closer`, find every `.buttonholder .button.disable`, strip the `disable` class, and inline `style="background-color:#007A8F"` (mirrors `arlington.behaviors.js:154-157` which un-disabled the button after all magnifying glasses were clicked — JS path never runs in archive).
   - Decompose entire `.views-field-field-transcription .accordion` whose body is just a `<div class="hidden">` placeholder ("there's nothing here"). Mirrors `arlington.behaviors.js:185-187` which adds `.hideme` to those.

9. **Resource-page transformations:**
   - Decompose `.pane-resource-image .views-field-field-source-1` outright (the source-thumbnail carousel selector — JS-only nav, parent stripped of its glasses; eliminates 404s on missing `styles/resource_circles/*` derivatives).
   - Detect multi-source pages: when `.pane-resource-image` contains 2+ `.accordion` elements (multi-page transcriptions), append class `multi-source` to the pane and **extract** all `.views-field-field-transcription` wrappers into a new sibling `<div class="multi-source-transcriptions">` inserted after `.rightme`. The pane keeps its 48% top-left column with image+citation, `.rightme` keeps its 48% top-right column with the petition card, and the transcriptions flow full-width across the page below both columns. 7 pages affected (resource-2-fighting-side-side, resource-3-fighting-side-side, resource-4-service-country, resource-1/3/4/5-sad-and-terrible-disaster). Single-source resource pages keep the original 48/48 two-column layout untouched. Idempotent — re-runs detect the existing wrapper and skip.

10. **Dashboard rewrite:** any `<a href>` whose path component is `dashboard` or starts with `dashboard/` rewritten to `/`. Then `static/dashboard/` directory deleted.

11. **Header restructure** — two parts:
    - `<div class="teachwrap">` "Teach" link gets moved into the sibling `<div class="rightside">` (which used to host the login form). Empty `.teachwrap` is decomposed.
    - `<div class="searchwrap">` is **inserted** as a sibling immediately before `.rightside`, containing `<a class="searchlink" href="/search/">Search</a>`. Anchored on `.rightside` (not `.leftside`) because content pages don't have `.leftside` while every page has `.rightside`. CSS positions `.searchwrap` absolutely so the parent doesn't matter visually.

12. **Resource-page two-column layout:** `.toright` siblings get wrapped in `<div class="rightme">`. Mirrors `arlington.behaviors.js:172-173`'s `wrapAll`. The existing CSS `.node-type-resource .pane-page-content .rightme { width: 48%; display: inline-block }` then takes over. (Originally we let the JS do the wrap at runtime, but that nested with our build-time wrap on every page reload — see step 2 above for why the JS now gets dropped entirely.)

13. **Pagefind body-tag injection:** `data-pagefind-body=""` added to the page's main content container (`.l-content` with `role="main"`, preferring non-anchor containers with text). Removes the attribute from misplaced elements (e.g. the empty "skip to main content" anchor that sometimes had it).

14. **Inject single-source-of-truth `<style id="futl-archive-overrides">`** containing all archive-specific CSS overrides. Idempotent — content-compare on re-run, replace only if changed. Currently includes:
    - Force-expand JS-driven collapsibles (`.accordion .acont`, `.panel-pane.webform.hidden`, `.node-type-{hypothesis,resource,rethink} .hidden`)
    - Resource page: always show `.views-field-field-citation- .field-content p` (no JS to add `.myself`); hide `.pane-resource-image .views-field-field-source-1` (thumbnail carousel); for `.multi-source-transcriptions` (the extracted full-width transcription container), full width with `clear: both` and accordion spacing
    - Look-closer page: stack all `.cluewrap` blocks vertically; hide `.glass` magnifying-glass overlays
    - Mirror `arlington.behaviors.js:167-169` — hide `.nextpart` on `node-type-look-closer.page-node-605` (live site hides the misplaced "Confederate Mound" text via JS)
    - `/content/teach`: center the lone `.holdleft` video in `.infoblock` since the right column was emptied
    - Header pills: style `.l-header .rightside .teachlink` and `.l-header .l-branding .searchwrap` (teal `#3395a5` background, white uppercase text, drop shadow, rounded bottom corners — identical look to the original `.teachwrap` pill)

15. **Inject `<script id="futl-archive-behaviors">`** — ~15 lines of vanilla JS for the home-page module modal:
    - Click `.boxwrap` → set sibling `.popupme.style.display = 'block'`
    - Click on `.popupme` backdrop (outside `.innerwarp`) → close
    - Clicks inside `.innerwarp` (white card) propagate normally so "Preview Module" anchor still navigates

## Phase 5 — Asset copy

`runtime/copy_assets.sh` — rsync-based copy of static assets from the Drupal docroot into the static tree at the same paths Drupal serves them from (so existing `<img src="/sites/default/files/...">` references resolve unchanged).

**Copy with `--exclude` for build-source files:**
- `misc/` (Drupal core JS/CSS bundle) — drops `typo3/` (PHP phar-stream-wrapper), `brumann/` (PHP polyfill), `farbtastic/` (color picker, unused), all `*.php`, all 15 unused top-level `*.js` (jquery.js, jquery.cookie.js, autocomplete.js, batch.js, collapse.js, etc.). Then post-copy reduces `misc/ui/` from 59 files to the 2 actually loaded (`jquery.effects.core.min.js`, `jquery.ui.datepicker-1.13.0-backport.js`), and removes 36 unused PNG/GIF icons. Final size: 168 KB (was 1.1 MB).
- `sites/all/themes/{omega,arlington}/` — drops `*.php`, `*.inc`, `*.module`, `*.tpl.php`, `template.php`, `node_modules/`, `sass/`, `*.scss`, `*.map`, `.sass-cache/`, `arlington/libraries/` (IE6/7 polyfills), `arlington/preprocess/`, `arlington/process/`, `omega/ohm/` (unused sub-theme), `LICENSE.txt`, `Gemfile`, `Gemfile.lock`, `Gruntfile.js`, `Guardfile`, `bower.json`, `.bowerrc`, `.jshintrc`, `package.json`, `.ruby-*`, `config.rb`, `*.info`, `*.make`, `screenshot.png`, `logo.png`. Post-copy removes 12 unused demo/template images from `arlington/images/`. Final size: 12 MB (was 19 MB).
- `sites/all/modules/*` — entire tree minus PHP backend code, tests, `*.info`, `*.make`, README/CHANGELOG/INSTALL/UPGRADE/TODO/LICENSE/API.txt
- `modules/*` — Drupal core modules' static files. Pruned post-copy to 8 actually-referenced modules (book, comment, field, file, node, search, system, user). 28 fully-unused modules removed (aggregator, block, blog, contact, dashboard, dblog, field_ui, filter, help, image, locale, menu, overlay, path, php, poll, profile, rdf, shortcut, simpletest, statistics, syslog, taxonomy, toolbar, tracker, translation, trigger, update). 4 modules referenced only from unloaded Omega CSS (color, contextual, forum, openid) also removed along with their unused Omega CSS subdirs. Final size: 204 KB (was 1004 KB).
- `sites/default/files/{webform,pictures}/` — 22 user-uploaded files

`runtime/cleanup_themes.sh` — standalone idempotent script that re-applies the same theme/misc cleanup if the static tree gets out of sync with the build pipeline. Run after `copy_assets.sh`.

## Phase 6 — Empty-content cleanup

`runtime/cleanup_taxonomy_pages.sh` — removed the empty teacher-classroom subgraph that had no real content:

- **28 empty `content/{class-*, briannas-class, class-gretas-test, class, deville-test, engle-period-1, jennifers-testing-class, js-new-classs}` pages** — auto-generated taxonomy metadata only (Period, Subject, Semester, Year fields), no body
- **7 `year/` pages** — empty taxonomy listings ("Class | Read more about Class | Book navigation goes here") + a stray `2017-18?page=1` file
- **9 `period/` pages** — same shape
- **2 `semester/` pages** — same shape
- **2 `subject/` pages** — same shape
- **4 `topic/` pages** — completely empty
- **`taxonomy/` directory** — leftover empty dir

The class-pages ↔ taxonomy-listings link graph was self-contained — every inbound link to the deleted pages came from inside the deleted set, so no orphaned links resulted.

Total HTML pages: 510 → 459.

## Phase 7 — Pagefind

`runtime/run_pagefind.sh` — runs `npx -y pagefind@latest --site /site --output-subdir pagefind --force-language en --logfile /artifacts/pagefind.log --exclude-selectors 'header,footer,nav,...'` in a `node:20-alpine` container.

`--force-language en` was needed because the IE-conditional-comment `<html>` tags initially confused language detection (resolved by the IE-block rewrite in scrub preprocessing).

`--exclude-selectors` keeps repeated header/footer/nav text out of every page's index.

`--logfile` writes the build log to `/artifacts/`, not `/site/`, so it doesn't end up served.

Output: `static/pagefind/` (~2.4 MB) with `pagefind.js`, `pagefind-ui.js/.css`, language WASM bundles, and gzipped fragments for **333 indexed pages**.

`runtime/search_page.html` → `static/search/index.html` — themed search page (dedicated `/search/` URL preserved). Loads the same Arlington/Omega theme stylesheets as content pages, places the Pagefind UI inside a content-style shell, recolors UI variables to match the site:

- Search input has the same `box-shadow: 1px 8px 20px 0 #a6a6a6` as the home cards
- Result cards: white, rounded corners, drop shadow, `padding: 1.5em 2.5em` for breathing room
- Result titles: teal `#007A8F`, CenStd serif font (matching `.toptit` on home cards)
- Excerpt highlights: yellow `#ffd966` matching the look-closer "Think about it" highlight color
- "Clear" button matches the `.teachlink` pill — teal `#3395a5` background, white uppercase text, drop shadow

The search page header includes both the SEARCH and TEACH pills (matching all other pages).

## Phase 8 — Render verification

Headless Chromium via Playwright on docker-host (`runtime/render.sh`, `runtime/render.js`).

**Architecture:**

- Image: `mcr.microsoft.com/playwright:v1.49.0-noble` (browsers preinstalled at `/ms-playwright/`, but no `playwright` npm module).
- First-run: `npm install playwright@1.49.0` into `runtime/node_modules/` on docker-host with `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` so it uses the image's browsers.
- Three modes: `local` (spins a python http.server against `static/` on `futl-render-net`), `drupal` (joins `futl_futl` to hit the running Drupal at `http://web/`), `live` (no network, hits `https://forustheliving.org`).

**Outputs per render:** `<basename>.{png, html, console.log, failed.log, responses.log}`.

A second helper, `runtime/render_click.js`, performs click → screenshot for verifying interactive elements (used to verify the home-page module modal opens correctly).

**Validation passes during build:** rendered local + live for ~12 representative pages and visually compared. Each visual gap traced to a specific JS dependency, fixed by static markup transformation in scrub or CSS override. Final sweep: 0 console errors, 0 failed requests on home, content pages, node pages, look-closer pages, resource pages, teach page, search page.

---

## How to re-run any step

| Step | Command |
| --- | --- |
| Bring up Drupal | `ssh docker-host 'cd ~/futl-flatten && docker compose up -d'` |
| Apply PHP 7.4 patches | `ssh docker-host 'docker exec futl-web-1 python3 /work/patch_php74.py'` |
| Re-run spam triage report | `ssh docker-host 'docker exec futl-web-1 python3 /work/triage_spam.py --password "..." --out /work/triage'` |
| Apply approved deletions | `ssh docker-host 'docker exec futl-web-1 python3 /work/triage_delete.py --password "..."'` |
| Hygiene + seed URLs | `drush -r /var/www/html/web ...` (see Phase 2 commands) |
| Re-crawl | `ssh docker-host 'docker run -d --name futl-crawl --network futl_futl -v ~/futl-flatten/static:/out -v ~/futl-flatten/runtime:/runtime:ro -v ~/futl-flatten/artifacts:/artifacts alpine:3.20 /runtime/crawl.sh'` |
| Re-scrub | `ssh docker-host 'docker run --rm -v ~/futl-flatten/static:/site -v ~/futl-flatten/scripts:/scripts:ro python:3.12-slim bash -c "pip install -q beautifulsoup4 lxml && python3 /scripts/scrub_static.py /site"'` |
| Re-copy assets | `ssh docker-host 'sh ~/futl-flatten/runtime/copy_assets.sh'` |
| Re-clean themes/misc | `ssh docker-host 'sh ~/futl-flatten/runtime/cleanup_themes.sh'` |
| Re-clean empty taxonomy/class pages | `ssh docker-host 'sh ~/futl-flatten/runtime/cleanup_taxonomy_pages.sh'` |
| Rebuild Pagefind | `ssh docker-host 'sh ~/futl-flatten/runtime/run_pagefind.sh'` |
| Replace search page | `ssh docker-host 'cp ~/futl-flatten/runtime/search_page.html ~/futl-flatten/static/search/index.html'` |
| Sync remote → local | `rsync -aHAX --delete-after docker-host:futl-flatten/static/ /workspace/futl-flatten/static/` |
| Render any page | `ssh docker-host 'sh ~/futl-flatten/runtime/render.sh {local\|live\|drupal} <path>'` |
| Visual check locally | `python3 -m http.server -d /workspace/futl-flatten/static 8000` |

## Files in this repo

```
static/PLAN.md                        — this file (deployed alongside the site)
compose.yml                           — Drupal stack (mysql + php-apache)
seed-urls.txt                         — 718 URLs given to wget
static/                               — final output, 311 MB, 459 HTML pages
wget/                                 — pre-conversion raw mirror snapshot, 288 MB
drupal/                               — input Drupal docroot + InnoDB data
scripts/
  patch_php74.py                      — PHP 7.4 fixups for webform + rules
  triage_spam.py                      — heuristic spam scorer
  triage_inspect.py                   — bucket sampler/printer
  triage_users_breakdown.py           — re-bucket users by deletion confidence
  triage_delete.py                    — apply approved deletions (SQL + drush)
  gen_seed_urls.php                   — drush php-script for seed-urls.txt
  scrub_static.py                     — single-source HTML post-processor
runtime/
  crawl.sh                            — wget runner (writes logs to /artifacts)
  copy_assets.sh                      — copy theme/module/uploads into static/
  cleanup_themes.sh                   — prune theme/misc build artifacts
  cleanup_taxonomy_pages.sh           — drop empty class/taxonomy subgraph
  run_pagefind.sh                     — pagefind index builder
  search_page.html                    — themed search page template
  drupal.htaccess                     — restored stock Drupal .htaccess
  apache-docroot.conf                 — Apache vhost for the web container
  render.sh, render.js                — headless Chromium screenshot+DOM dump
  render_click.js                     — click-then-screenshot helper
  audit.sh, final_audit.sh            — auth-surface + structure audits
  pf_coverage.sh, pf_debug.sh         — Pagefind coverage diagnostics
  error_sample.sh, coverage.sh        — wget error analysis
  inventory.sh, probe_assets.sh       — asset reference audits
```

## Notable decisions

- **Mirror, not SSG rebuild.** Reusing Drupal's rendered output preserves theme + URL fidelity without reauthoring 78 contrib modules' templates. The cost is post-processing — the scrub script (~400 lines) handles that.
- **Idempotent scrub.** Every transform in `scrub_static.py` checks state before mutating, so re-running on already-processed output is safe and minimal. The `<style id="futl-archive-overrides">` and `<script id="futl-archive-behaviors">` blocks are content-compared and replaced in place when their definitions change.
- **CSS overrides instead of theme rebuild.** Each visual gap was traced to a specific JS-driven behavior in `arlington.behaviors.js`; the build replaces those with static markup transformations + CSS rules rather than touching the Arlington theme files. The theme stays as Drupal shipped it.
- **Vanilla JS only where needed.** The home-page card modal would have been awkward as pure CSS (`:target` requires URL fragments); a 15-line vanilla JS handler is simpler and degrades gracefully.
- **Faithful to the live site, not "what should be".** Where the live theme suppresses content via JS (e.g. node 605's misplaced "Confederate Mound" text), the archive mirrors the suppression in CSS instead of either showing or removing the content arbitrarily.
- **Build artifacts stay out of `static/`.** Logs (`wget.log`, `pagefind.log`) and seed lists land in a sibling `artifacts/` mount on docker-host, never inside the served tree.
- **Search reachable on every page, not just home.** The `.searchwrap` injection anchors on `.rightside` (which exists on every page), not `.leftside` (only on the home page).
- **Empty content removed.** 28 teacher-classroom pages and their orphaned taxonomy listings (year/period/semester/subject/topic) were deleted because they contained only auto-generated metadata with no body — their entire link subgraph was self-contained, so removal was clean.

## Operational state

After build completion the Drupal stack on docker-host (`futl-web-1`, `futl-db-1`) was **stopped + removed**, along with the `futl_futl` network. The `~/futl-flatten/` directory tree (compose.yml, drupal/, runtime/, scripts/, static/, artifacts/) remains intact on docker-host so any re-run is `cd ~/futl-flatten && docker compose up -d` away.

To re-run the stack:

```sh
ssh docker-host 'cd ~/futl-flatten && docker compose up -d'
```

After that, any of the runner scripts (`runtime/crawl.sh`, `runtime/run_pagefind.sh`, `runtime/render.sh local|drupal|live`) work as before. Stop again with `docker compose down`.

## Out of scope

- Long-term hosting / CDN / domain cutover.
- Replacing webforms with Formspree/Netlify Forms (user chose drop-entirely for an archive).
- Migrating to a new SSG (11ty/Hugo) with reauthored templates.
- Spam-prevention hardening of the live Drupal (it's going away).

[Pagefind]: https://pagefind.app/
