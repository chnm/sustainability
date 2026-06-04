# Eagle Eye Citizen — archived static copy

A static archive of the former Drupal site at eagleeyecitizen.org. Every
page is pre-rendered HTML; nothing here runs server-side. ~1,500 HTML
pages plus the original theme assets (`sites/`, `themes/`, `core/`,
`vendor/`).

## Deployment

Production lives on **moby** (`10.112.113.211`) at `~/eec-static`,
served by an `nginx:1.27-alpine` container on **port 8082**.

```sh
# from this checkout
tar czf /tmp/eec.tgz -C .. eagleeyecitizen
scp -i ~/.ssh/id_ed25519_claude /tmp/eec.tgz moby@10.112.113.211:/tmp/
ssh -i ~/.ssh/id_ed25519_claude moby@10.112.113.211 \
  'cd ~/eec-static && tar xzf /tmp/eec.tgz --strip-components=1 && rm /tmp/eec.tgz'
```

**Never `rm -rf ~/eec-static`** to clear it — that swaps the directory
inode and the container's bind-mount goes stale (empty `ls` inside the
container). If you must wipe, follow it with `docker restart eec-static`.

Live preview folder: `~/static-sites/eec-preview/` on moby served at
`http://10.112.113.211:8088/eec-preview/` via the `static-sites` caddy.

## Archive banner

The "This is an archived copy…" banner is **statically baked into every
HTML page** for accessibility (works without JS, correct reading order,
no CLS). Sources of truth:

- `assets/archive.css` — visual styling (EEC palette: bg `#474747`,
  text `#f9f5ef`, copper accent `#bd7332`)
- `assets/archive-banner.html` — reference markup; **not** fetched at
  runtime, only useful for humans diffing pages
- `assets/rrchnm_logo.png` — loaded by CSS `background-image` so the
  per-page relative path to the logo doesn't matter

To change the banner text/markup, sweep all HTML files with a literal
replacement, then redeploy.

## Asset hosting

User-uploaded files (challenge thumbnails, source images) are referenced
in-repo as `sites/default/files/<name>`. The actual bytes live in the
MinIO bucket at `obj.rrchnm.org/eagleeyecitizen.org/files/`; the
production web server rewrites `/sites/default/files/...` requests to
that bucket. The static export therefore carries no `obj.rrchnm.org`
URLs — the redirect is the single source of truth for where files live.

## Homepage tile manifest

`assets/challenges.json` is fetched by inline JS in `index.html` to
randomize the Featured and Popular tiles on every page load. 546 entries,
each with `href`, `title`, `type_label`, `thumb`. The script dedupes
visually identical picks (same title or thumb). On `file://` origins the
fetch fails and the hardcoded fallback tiles are kept.

## What's been stripped from the original

- Login form, "Create Account", "Forgot Password" UI, mobile login bar,
  and the standalone `user.html` / `registration.html` /
  `user/password.html` pages — auth is permanently disabled
- "Terms of Use" footer link and its target `content/privacy-policy.html`
  — that page 404'd on the original live site
- The Drupal CSRF/build-id machinery in remaining forms is dead — every
  `<form>` posts to `action="#archived"`

## Pitfalls hit before

- Removing a multi-line block requires matching the **outer** closing
  `</div>`. A previous cleanup used `s.find('</div>', j)` where `j`
  pointed at `<div id="…">Login</div>` and ended up matching the inner
  `</div>`, leaving a stray closer that prematurely closed `.page-front`
  and collapsed the homepage grid (all tile styles are scoped under
  `.page-front`). Walk depth or search past the marker's own close.
- `position: sticky` on the banner needs to be preserved — History
  Matters uses `position: relative` but EEC's banner is sticky by
  intent.

## Accessibility — WCAG triage

**Target:** WCAG 2.1 Level AA is required. WCAG 2.2 additions are
nice-to-have; prefer to fix anything in 2.2 that's cheap, but a 2.2-only
failure doesn't block.

**How to audit a page.** Two MCPs are available at user scope:

- `mcp__a11y__test_accessibility` — pass a URL, runs axe-core, returns
  rule violations grouped by impact. Use this as the default scan.
- `mcp__a11y__check_color_contrast` and `check_aria_attributes` —
  targeted checks when triaging one finding.
- For interactive flow checks, drive the page with the `playwright` MCP
  and pair it with `mcp__a11y__test_html_string` on the post-interaction
  DOM.

Live URL to scan: `http://10.112.113.211:8082/<path>`. For a sweep,
script the MCP over a representative sample (one of each layout —
homepage, `solve-challenges.html`, a `solve/bp/`, `solve/sio/`,
`solve/tat/` page, `about.html`, `teach.html`).

### Status

Last full audit: **2026-06-02**, axe-core 4.11.4 via `mcp__a11y`. Sample
of 7 pages: `index.html`, `about.html`, `teach.html`,
`solve-challenges.html`, `create-challenges.html`, `solve/bp/2705.html`,
`solve/sio/27403.html`, `solve/tat/6140.html`. Treat the table below as
a living triage list — when you find or fix an issue, add or update a
row instead of leaving it in commit messages.

| ID | SC | Lvl | Where | Status | Notes |
|----|----|----|-------|--------|-------|
| BANNER-CONTRAST | 1.4.3 Contrast (Minimum) | AA | `assets/archive.css` `.ee-archive-banner` | ✅ verified | Text `#f9f5ef` on `#474747` ≈ 9.4:1 (AAA); underlined link same color (no color-only affordance). |
| BANNER-NAME | 4.1.2 Name, Role, Value | AA | banner markup | ✅ verified | `role="note"` on the wrapper; logo link has `aria-label="RRCHNM"`. |
| BANNER-ORDER | 1.3.2 Meaningful Sequence | A | every page | ✅ verified | Banner is statically rendered, encountered first by screen readers. |
| LOGO-LINK-NAME | 2.4.4 Link Purpose / 4.1.2 Name, Role, Value | A | every page — `<a class="logo">` (header) and `<a class="logo-chnm">` (footer) | ✅ fixed 2026-06-02 | Added `aria-label="Eagle Eye Citizen — home"` to all 1503 header logo anchors and `aria-label="Roy Rosenzweig Center for History and New Media"` to all 1503 footer marks. Verified clean on re-scan. |
| HP-TILE-IMG-ALT | 1.1.1 Non-text Content | A | `index.html` — `.challenge-tile img` (homepage tile thumbnails, 2 occurrences) | ✅ fixed 2026-06-02 | Added `alt=""` to both hardcoded fallback `<img>` tags and `img.setAttribute("alt", "")` inside `apply()` in the randomizer JS. Decorative is correct — tile title text already names each link. Verified clean on re-scan. |
| SKIP-LINK-TARGET | 2.4.1 Bypass Blocks | A | every page — `<main>` element | ✅ fixed 2026-06-02 | Added `id="main-content"` so the existing `<a href="…#main-content">Skip to main content</a>` link now lands somewhere. axe didn't flag this (accepts the landmark) but the link was nonfunctional. 1503 pages. |
| TEACH-RIBBON-CONTRAST | 1.4.3 Contrast (Minimum) | AA | `teach.html` — `.topic-title.ribbon.teach-tile--titlec span` (6 ribbon labels: Resources, Achievements, Differentiation, In a Pinch, Assessment, Lesson Planning) | ✅ fixed 2026-06-02 | Override added to `assets/archive.css`: `body .teach-link--well .ribbon { background-color: #015960; }`. White on `#015960` ≈ 7.6:1 (passes AAA). `body` prefix bumps specificity above Drupal's `.teach-link--well .ribbon` so the cached CSS bundle stays untouched. Verified clean on re-scan. |

### Todos

- [x] **LOGO-LINK-NAME** — done 2026-06-02.
- [x] **HP-TILE-IMG-ALT** — done 2026-06-02.
- [x] **TEACH-RIBBON-CONTRAST** — done 2026-06-02 (`#015960`, ≈ 7.6:1, AAA).
- [x] **SKIP-LINK-TARGET** — done 2026-06-02.
- [ ] **AUDIT-INCOMPLETE-CONTRAST** — Every page returned `incomplete: 1` from axe, almost certainly a `color-contrast` check it couldn't resolve against a gradient/image background. Manually verify and close out.
- [ ] **AUDIT-SUSPECTS** — Work through the unverified items in the "Known suspects" subsection below (dead form labels, decorative iconography, copper-on-cream contrast, headings, lang on challenge-detail pages, 2.4.11 Focus Not Obscured for the sticky banner).

### Known suspects (unverified — needs an audit pass)

- **Forms** still present in the archive (challenge answer inputs, search
  inputs) are non-functional but keep their labels, required markers,
  and submit buttons. Confirm focus order is sane and that "Required"
  + `aria-required` don't lie when the form does nothing.
- **Decorative SVG/PNG iconography** (`themes/eagleeye/img/*`) is loaded
  via CSS `background-image`, which is correct for purely decorative
  content but means any informational icon needs an accompanying text
  label in the DOM.
- **Color contrast on theme accents** (`#bd7332` copper on `#f9f5ef`
  cream — used for tile labels, buttons) — has not been measured.
- **Headings** — Drupal often emits skipped heading levels. Run an axe
  pass and check `heading-order`.
- **Lang attribute** — `<html lang="en">` is present on the homepage;
  confirm every page has it (the original Drupal render should, but the
  challenge-detail pages are worth a spot check).
- **Skip link** — every page has `<a href="…#main-content" class="visually-hidden focusable">Skip to main content</a>`,
  but `#main-content` is not currently set on the `<main>` element on
  most pages. That's a 2.4.1 Bypass Blocks failure — should be fixed by
  adding `id="main-content"` to the `<main>` tag.
- **2.2-only worth keeping in mind:** 2.4.11 Focus Not Obscured (Minimum)
  — verify the sticky archive banner doesn't cover focused elements
  near the top of the page when tabbing.
