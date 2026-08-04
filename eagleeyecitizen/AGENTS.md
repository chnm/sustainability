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

> **Currently DISABLED (2026-08-04).** The banner markup is still baked
> into every page, but `assets/archive.css` hides it with
> `.ee-archive-banner { display: none !important; }`. To bring it back,
> delete that one rule — and restore `html { scroll-padding-top: 56px; }`
> at the same time so the sticky banner can't obscure focused elements
> (WCAG 2.4.11). The rest of this section describes the banner as authored.

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
- **`about.html` and its footer "About" link** — removed 2026-08-04 (per
  request). The footer `<li><a href="…about.html">About</a></li>` was
  swept out of all 1502 pages; the page file was deleted. No other links
  pointed at it.
- **`create-challenges.html` and every "Create" link** — removed 2026-08-04
  (creation is no longer supported). Deleted the page; blanked the homepage
  `.home-nav` middle ticket to `<div class="btn btn-center"></div>` (the
  `.home-nav` grid keeps Solve/Teach in place) and the interior header nav
  to `<li class="middle-nav"></li>` on 561 pages — leaving the middle slot
  blank rather than collapsing it. No `create-challenges.html` references
  remain.

## Footer partner logos

The footer carries the **RRCHNM** mark (`.logo-chnm`) and, since
2026-08-04, the **GMU Department of History & Art History** mark
(`.logo-histarthist`, links to `https://historyarthistory.gmu.edu/`)
sitting immediately to its right. Both are CSS `background-image` logos
(empty anchors with an `aria-label` for the name) — `assets/histarthist-logo.png`
is the horizontal full-colour GMU lockup (900×251). Paths resolve against
`assets/archive.css`, not per-page depth.

The two anchors are wrapped in `<div class="footer-logos">` and laid out
as a **nowrap flex row** (styled in `archive.css`): on desktop they show
full size (RRCHNM ~220×41, GMU ~230×64) side by side; on narrow viewports
they **shrink together and stay on one line instead of stacking**
(`aspect-ratio` + `background-size:contain` keep them proportional, and
`min-width:0` on the footer grid cells lets the row scale below its
content width). Earlier revisions used fixed-size `inline-block` logos,
which stacked on narrow/zoomed viewports once the GMU mark was enlarged —
hence the flex-row rewrite.

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

Re-audit **2026-08-04**, axe-core 4.10.2 injected via Playwright against
the dev deploy `https://eec.dev.chnm.gmu.edu/` (same 8-page sample).
**axe reported 0 violations on all 8 pages** — only `color-contrast`
`incomplete`; plus every page had `lang="en"`, exactly one `<h1>`, clean
heading-order, and no unlabeled *visible* inputs. The `incomplete` items
are all text-over-**image** (which axe can't resolve), so they were
measured by hand: draw the same-origin background image to a `<canvas>`,
sample only the tight text line-boxes (`Range.getClientRects()`), compute
WCAG contrast per pixel. That measurement pulled two **real** 1.4.3
failures out of the "incomplete" bucket (HERO-TAGLINE-CONTRAST,
NAV-IMG-CONTRAST) plus a real 2.4.11 finding. New rows below.

| ID | SC | Lvl | Where | Status | Notes |
|----|----|----|-------|--------|-------|
| BANNER-CONTRAST | 1.4.3 Contrast (Minimum) | AA | `assets/archive.css` `.ee-archive-banner` | ✅ verified | Text `#f9f5ef` on `#474747` ≈ 9.4:1 (AAA); underlined link same color (no color-only affordance). |
| BANNER-NAME | 4.1.2 Name, Role, Value | AA | banner markup | ✅ verified | `role="note"` on the wrapper; logo link has `aria-label="RRCHNM"`. |
| BANNER-ORDER | 1.3.2 Meaningful Sequence | A | every page | ✅ verified | Banner is statically rendered, encountered first by screen readers. |
| LOGO-LINK-NAME | 2.4.4 Link Purpose / 4.1.2 Name, Role, Value | A | every page — `<a class="logo">` (header) and `<a class="logo-chnm">` (footer) | ✅ fixed 2026-06-02 | Added `aria-label="Eagle Eye Citizen — home"` to all 1503 header logo anchors and `aria-label="Roy Rosenzweig Center for History and New Media"` to all 1503 footer marks. Verified clean on re-scan. |
| HP-TILE-IMG-ALT | 1.1.1 Non-text Content | A | `index.html` — `.challenge-tile img` (homepage tile thumbnails, 2 occurrences) | ✅ fixed 2026-06-02 | Added `alt=""` to both hardcoded fallback `<img>` tags and `img.setAttribute("alt", "")` inside `apply()` in the randomizer JS. Decorative is correct — tile title text already names each link. Verified clean on re-scan. |
| SKIP-LINK-TARGET | 2.4.1 Bypass Blocks | A | every page — `<main>` element | ✅ fixed 2026-06-02 | Added `id="main-content"` so the existing `<a href="…#main-content">Skip to main content</a>` link now lands somewhere. axe didn't flag this (accepts the landmark) but the link was nonfunctional. 1503 pages. |
| TEACH-RIBBON-CONTRAST | 1.4.3 Contrast (Minimum) | AA | `teach.html` — `.topic-title.ribbon.teach-tile--titlec span` (6 ribbon labels: Resources, Achievements, Differentiation, In a Pinch, Assessment, Lesson Planning) | ✅ fixed 2026-06-02 | Override added to `assets/archive.css`: `body .teach-link--well .ribbon { background-color: #015960; }`. White on `#015960` ≈ 7.6:1 (passes AAA). `body` prefix bumps specificity above Drupal's `.teach-link--well .ribbon` so the cached CSS bundle stays untouched. Verified clean on re-scan. |
| HERO-TAGLINE-CONTRAST | 1.4.3 Contrast (Minimum) | AA | `.front-header .b-1 .tagline` — hero pages (`index.html` + any page rendering the `home-header-background.png` hero) | ✅ **fixed 2026-08-04** | Was white `#fff` **17px bold** (needs 4.5:1) over `home-header-background.png` at worst **2.54:1** (avg ~2.6:1). Fix in `assets/archive.css`: `.front-header .b-1 .tagline` given `display:inline-block` + `background:rgba(0,0,0,0.6)` scrim + padding. Re-measured composited (scrim over the hero photo, tight line-boxes) = **10.19:1 worst** — passes AA/AAA. |
| NAV-IMG-CONTRAST | 1.4.3 Contrast (Minimum) | AA | interior header — `.container.cap-banner` nav links (`SOLVE/CREATE/TEACH/ABOUT`) over `CapitalwLightRays.png`; sitewide on all non-front pages | ✅ **fixed 2026-08-04** | Was white `#fff` 20.8px bold nav links directly over the rays photo, no scrim: **CREATE ≈ 1.05:1**, **TEACH ≈ 1.8:1** (SOLVE/ABOUT happened to land on dark rays and passed). Fix in `assets/archive.css`: `.cap-banner .hr_2 nav a` given `background:rgba(0,0,0,0.6)` scrim + padding + `text-shadow`. Re-measured composited over the brightest rays = **≥12:1** (≥5.7:1 even by worst-case hand-calc over a pure-white ray) — passes. Copper H1 over same image = 5.66:1 (already passing); teach section ribbons (`ribbonheader.png`) = 4.74:1 pass. |
| BANNER-FOCUS-OBSCURED | 2.4.11 Focus Not Obscured (Minimum) | AA (2.2) | `assets/archive.css` `.ee-archive-banner` — every page | ✅ **resolved 2026-08-04 (banner disabled)** | Banner was `position:sticky; top:0; height:48px; z-index:9999` with **no `scroll-padding-top`** — a focused link was shown fully inside the 0–48px band. The archive banner has since been **disabled** (`.ee-archive-banner{display:none!important}`), so there is no sticky header left to obscure focus. If the banner is ever re-enabled, add `html{scroll-padding-top:56px}` at the same time (noted in `archive.css`). |
| DRAG-NO-ALT | 2.5.7 Dragging Movements / 2.1.1 Keyboard | AA (2.2) / A | `solve/sio/*` (Sort It Out), and the drag mechanics of BP/TAT | ⚠️ **noted 2026-08-04** | `.card.sortable.draggable` (jQuery-UI draggable, `hasUI:true`) — 6 cards, no move/up-down buttons, and cards are **not keyboard-focusable** (`.focus()` no-op). Drag is the only ordering path → fails 2.5.7 + 2.1.1 in principle. **Muted** because the challenge is non-functional in the archive (submit → `#archived`). Cleanest resolution: make the card UI inert (it can't be completed anyway) or document that in-archive solving is unsupported. |

### Todos

- [x] **LOGO-LINK-NAME** — done 2026-06-02.
- [x] **HP-TILE-IMG-ALT** — done 2026-06-02.
- [x] **TEACH-RIBBON-CONTRAST** — done 2026-06-02 (`#015960`, ≈ 7.6:1, AAA).
- [x] **SKIP-LINK-TARGET** — done 2026-06-02.
- [x] **AUDIT-INCOMPLETE-CONTRAST** — closed 2026-08-04. The `incomplete` was always text-over-image. Measured by hand: **passes** — homepage tile titles (white, 3.74:1), tile labels/types (`#474747`, ~5:1), teach section ribbons (4.74:1), copper H1 (5.66:1); **fails** pulled out into their own rows — HERO-TAGLINE-CONTRAST and NAV-IMG-CONTRAST.
- [x] **AUDIT-SUSPECTS** — worked 2026-08-04. Resolved: lang (`en` on all 8 sample pages incl. challenge-detail); headings (clean H1→H2, no skips); dead form inputs (TAT `src_1..5` are `required`+unlabeled but rendered **0×0 → non-focusable/inert**, so no exposure — recommend deleting the dead markup anyway); copper-on-cream (copper H1 over header image 5.66:1 pass). Still open as real findings: NAV-IMG-CONTRAST, HERO-TAGLINE-CONTRAST, BANNER-FOCUS-OBSCURED, DRAG-NO-ALT (rows above).
- [x] **NAV-IMG-CONTRAST** — fixed 2026-08-04 (`rgba(0,0,0,0.6)` scrim + text-shadow on `.cap-banner .hr_2 nav a`; composited ≥12:1).
- [x] **HERO-TAGLINE-CONTRAST** — fixed 2026-08-04 (`rgba(0,0,0,0.6)` scrim chip on `.front-header .b-1 .tagline`; composited 10.19:1).
- [x] **BANNER-FOCUS-OBSCURED** — resolved 2026-08-04 by disabling the archive banner (no sticky header). Restore `html{scroll-padding-top:56px}` if the banner ever comes back.
- [ ] **DRAG-NO-ALT** — decide archive policy for the non-functional drag challenges (make inert or document as unsupported).
- [ ] **DEPLOY** — the contrast fixes, banner disable, About-page removal and footer HistArtHist logo are in the working tree only; the dev deploy `eec.dev.chnm.gmu.edu` still serves the old build. Deploy + re-scan to confirm live.

### Known suspects (unverified — needs an audit pass)

- ✅ **Forms** — checked 2026-08-04. The `#archived` challenge forms keep
  `required`/label markup, but the answer inputs (e.g. TAT `src_1..5`)
  render **0×0** and are therefore non-focusable/inert — not exposed to
  AT, so no label/required failure. They're dead weight; delete when
  convenient. SIO/BP drag cards are a separate issue → DRAG-NO-ALT.
- **Decorative SVG/PNG iconography** (`themes/eagleeye/img/*`) is loaded
  via CSS `background-image`, which is correct for purely decorative
  content but means any informational icon needs an accompanying text
  label in the DOM. (Not re-swept in detail 2026-08-04 — axe `image-alt`
  and `background-image` heuristics were clean on the 8-page sample.)
- ✅ **Color contrast on theme accents** — measured 2026-08-04. Copper
  `#bd7332` H1 over the header image = 5.66:1 (pass). The failures are
  **white** text over photos, not copper: see NAV-IMG-CONTRAST and
  HERO-TAGLINE-CONTRAST.
- ✅ **Headings** — clean on all 8 sample pages (one `<h1>`, `<h2>`
  children, no skipped levels; axe `heading-order` passed).
- ✅ **Lang attribute** — `<html lang="en">` confirmed on all 8 sample
  pages including the three challenge-detail layouts (bp/sio/tat).
- ✅ **Skip link** — `#main-content` target confirmed present (the
  SKIP-LINK-TARGET fix is live on the dev deploy).
- ⚠️ **2.4.11 Focus Not Obscured (Minimum)** — confirmed a real risk, see
  BANNER-FOCUS-OBSCURED row (sticky 48px banner, no `scroll-padding-top`).
- ✅ **2.5.8 Target Size (Minimum)** (2.2 AA) — checked 2026-08-04. Nav
  links (~21px tall), footer links (~14–16px) and the logo (20px) are
  under 24px but every one clears the **spacing exception** (nearest
  interactive neighbour ≥ 44px center-to-center). Pass.
- ✅ **3.3.7 Redundant Entry / 3.3.8 Accessible Authentication** (2.2 AA)
  — N/A: no functional multi-step forms; auth is stripped.
- **Minor (non-blocking):** homepage `<title>` renders as
  `| Eagle Eye Citizen` (empty leading segment — front page has no title
  prefix). 2.4.2 is technically met (site name present) but it should read
  e.g. `Eagle Eye Citizen — Home`. Interior pages are fine
  (`About | Eagle Eye Citizen`, etc.).
