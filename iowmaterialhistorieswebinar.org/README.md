# iowmaterialhistorieswebinar.org

*Material Histories of the Indian Ocean World, 1500–Present: Methods &
Challenges* — a five-part webinar the Roy Rosenzweig Center for History and New
Media and Mason's Department of History and Art History ran between 24 March
and 22 April 2021, on the study of artistic materials produced, circulated and
used in and through the Indian Ocean World after the arrival of European
mercantile powers. The site is the schedule, the five session pages, two
"continuing the conversation" write-ups with the recorded talks, and 30 items
of supporting material.

## Retrofit

This is the one **Omeka S** site in the set — the siblings are all Omeka
Classic — so the URL vocabulary is different (`/s/<site-slug>/item/4` rather
than `/items/show/4`) but the failure modes are the same. The crawled mirror
still behaved like a live install: the search box on all 46 captured pages
posted to a database endpoint, every image was hot-linked to the origin, the
theme fetched its typeface and its JavaScript from Google on each page view,
the navigation could not be opened from a keyboard below 800px, and the footer
credited Omeka.

It was also **incomplete**, which was the more urgent problem. The crawl
captured 46 pages; the origin serves 71. Nothing linked to the browse listings,
so wget never found them, and through them it never found 12 of the 30 items,
10 of the 28 media pages, the one item set, or one of the ten site pages. The
origin was still up when this work started, so all of it was fetched rather
than reconstructed.

This directory holds only what gets served. The transformations were made by a
set of one-off scripts that are **not kept here** — this repository is
deployment artifacts, and `context_root` is copied to the web root wholesale,
so anything else in this directory would be served publicly. What they did is
recorded below in enough detail to redo it. They were idempotent and took a
`--check` flag, so a second run left `git diff` empty; the archive as committed
is a fixed point.

Order mattered in three places. The origin data had to come first, because
everything downstream would otherwise emit dead links, and because the site is
gone the moment the DNS moves. The 72 pages were then rebuilt from the
*pristine* origin HTML rather than patched from the crawl, so that a single
template governs the head, the header, the navigation, the footer and the
Matomo block on every one of them and they cannot drift apart. And the Pagefind
index was built last, because it indexes the HTML as committed.

| what | where |
|---|---|
| Static search | `pagefind/` (committed — the deploy only copies files), `pagefind.yml`, `themes/default/asset/js/search.js`, `search.html` |
| Accessibility | `themes/default/asset/css/a11y.css`, `themes/default/asset/js/default.js`, plus the markup itself |
| Chrome | `assets/histarthist-logo.png` |
| Fonts | `themes/default/asset/css/fonts.css` + `fonts/*.woff2` — Open Sans; `application/asset/fonts/` — Font Awesome 5 |
| Vendored JS | `application/asset/js/vendor/jquery.min.js` |
| Media | referenced as `/files/…`; the objects themselves live in the bucket |
| URL repair | `redirects.caddy` |

### What the crawl missed

Omeka S serves `/s/<site>/item` and `/s/<site>/item-set`, but this site's
navigation is a flat list of eight pages and neither browse listing is on it,
so nothing in the crawl's link graph pointed at them. Everything reachable only
through those two pages was therefore invisible to wget.

The gap was closed from the origin's own REST API (`/api/items`, `/api/media`,
`/api/site_pages`, `/api/item_sets`), which is the authoritative list and which
also supplied the file inventory and the alt text below. Recovered:

- **12 item pages** — 1, 6, 18, 20, 22, 24, 32, 60, 62, 64, 66, 68. Five of
  them (60–68) are Pedro Pombo's photographs and the recording of his talk,
  added a fortnight after the ones the crawl did see.
- **10 media pages** — 3, 7, 19, 25, 33, 61, 63, 65, 67, 69.
- **The item set** — `Related Images`, and its 2 MB `/files/asset/` thumbnail,
  which sits in a derivative directory the crawl's exclude list never named
  because nothing wget reached linked to one. It is in `.gitignore` now.
- **`page/beyond-the-margins-blog`** — "Continuing the Conversation: Beyond the
  Margins", the write-up of the second talk, with the recording. It is not on
  the menu and the Blog page does not link to it; the only route in was through
  item 68, which the crawl had not found either.

Two browse listings are rebuilt as static pages —
`s/Material-Histories/item.html` (all 30 items on one page, in the origin's
default created-descending order) and `s/Material-Histories/item-set.html`.
Their server-side pagination, sort form and advanced-search form are dropped
rather than left as controls that do nothing. `search.html` links to both, so
the pages the origin orphaned are now reachable by browsing as well as by
searching.

### Static search

Omeka S ran search at `/s/Material-Histories/index/search`, a database query.
The theme put a search box in the header of every page, so **all 46 captured
pages carried a form posting to an endpoint a static host does not have** —
and `wget --convert-links` had rewritten its `action` to the absolute origin
URL, so after the DNS moves it would not even have failed locally.

It is re-implemented client-side with [Pagefind](https://pagefind.app):

- **`search.html`** — reads `?fulltext_search=`, the parameter name Omeka S
  itself used, so links and bookmarks of the old shape still land on a real
  result set (`?q=` and `?query=` are accepted too).
- **The header form on every other page** now targets it, in the slot the theme
  already had.
- `pagefind/` — the prebuilt index, committed, so the site stays a pure static
  deploy with no build step.

Built on Pagefind's **core API** rather than its Default UI, which renders its
own input: that would be a second search box on a page whose header already has
one, and the sibling archives work around it by hiding Pagefind's input and
driving it from the header, leaving an invisible control in the DOM.

**Index scope.** 69 pages — the home page, the nine site pages, the 30 items,
the 28 media and the item set. The three that carry `data-pagefind-ignore`
instead are the ones that would return themselves as answers: `search.html` and
the two browse listings, whose every word is a title indexed on the page it
links to. No facets: with two properties in use across the whole site
(`dcterms:title` and, on one item, `dcterms:rights`) there is nothing to facet
on.

**Search recall is bounded by the data.** Only 1,315 words are indexed across
69 pages. Most items are one photograph with a title and nothing else.

### Accessibility (WCAG 2.2 AA)

The archive was a raw crawl with no remediation. Verified with **axe-core**
(`wcag2a`/`2aa`/`21a`/`21aa`/`22aa`) → **0 violations across all 72 pages**
— 73 URLs, counting the search page both empty and with a query —
at 1280px, 375px and 320px, plus a keyboard pass and a horizontal-overflow
check at each width, all driven through real headless Chromium. jsdom would not
do: it cannot compute colour contrast or target size, and it cannot run
Pagefind's WebAssembly index, so the page that matters most here would audit as
an empty shell.

- **Keyboard (2.1.1), Name Role Value (4.1.2)**: below 800px the theme
  collapses the navigation and draws a hamburger as `header nav:before` — a CSS
  pseudo-element — with `default.js` listening for a click on the `<nav>`
  itself. There was nothing to focus and nothing to press, so **a keyboard user
  on a narrow viewport could not reach the navigation at all**, and assistive
  technology was never told a menu existed. There is a real `<button>` with
  `aria-expanded` now, Escape closes it, and the pseudo-element is suppressed so
  there is only one hamburger.
- **Landmarks (1.3.1)**: `<div id="content" role="main">` is a `<main>`, the
  navigation is named, and the header search form is a `search` landmark.
- **Headings (1.3.1)**: the theme made the site title the `<h1>` of all 72
  pages, so no page's `<h1>` said anything about that page, and content started
  at `<h2>`. Beneath that the page-block editor skipped levels freely —
  `h1 → h3 → h5` on the home page, `h2 → h4` on seven others, `h2 → h3 → h4` on
  every item and media page. The site title is a `<p>` on the 70 pages that have
  a heading of their own, and the content headings are renumbered so no level is
  skipped. **The rendering is unchanged**: each renumbered heading carries a
  `heading-N` class naming the level it used to be, and `a11y.css` restates what
  that level rendered as, including the browser's default margins, which are
  relative to the heading's own font-size and so have to move with it. Two pages
  (the home page and Contact Us) open below heading level and have no heading of
  their own; on those the site title stays the `<h1>`.
- **Empty heading (4.1.2)**: the Blog page had an `<h4>&nbsp;</h4>` doing the
  job of a spacer.
- **Use of colour (1.4.1)**: links are `#920b0b` with `text-decoration: none`,
  which is 2.27:1 against the black body text around them — below the 3:1 that
  colour alone needs. Underlines are restored throughout the content region and
  taken back off where a link sits among nothing but other links or wraps an
  image. (Restoring them only in `<p>` and `<li>` was not enough: this site puts
  prose straight into styled `<div>`s, and the funding credit inside a heading.)
- **Link name (2.4.4, 4.1.2)**: browse listings render each resource twice — a
  thumbnail link and a title link to the same page — and the thumbnail link's
  accessible name was an empty `alt`. Those are hidden from assistive technology
  and from the tab order.
- **Frame title (4.1.2)**: the four YouTube embeds were `<iframe>`s with no
  `title`.
- **Focus visible (2.4.7)**: the theme defines no focus styling anywhere, so
  the indicator was whatever the browser drew over a link with no underline —
  in several places against a grey button of nearly the same colour.
- **Reflow (1.4.10)**: no page scrolls horizontally at 320px.
- WCAG 2.2's other AA additions are satisfied without change and were confirmed:
  2.4.11 Focus Not Obscured (nothing is `position: fixed`/`sticky` except the
  skip link itself), 2.5.7 Dragging Movements and 3.3.8 Accessible
  Authentication (neither exists here), 3.2.6 Consistent Help and 3.3.7
  Redundant Entry (no help mechanism, no multi-step flows).

**Alt text.** Every `<img>` in the crawl had `alt=""`, including the ones that
were the only content of a link. The sibling archives record descriptive alt
text as a deferred curatorial pass; here it was not needed, because all 28 media
records carry a `dcterms:title` and the archive's images are all media
derivatives. Alt text is taken from the title of the media object the image
depicts, keyed on the file hash in the URL. Four of the 28 are non-descriptive
at source — `Pombo_Image 1` through `4` — and remain a curatorial follow-up.

**`[Untitled]`.** 28 of the 30 items carry no `dcterms:title`, so Omeka renders
the placeholder `[Untitled]` — which meant 28 pages with the same `<title>` and
the same `<h1>`, and, in any listing, 28 links with the same accessible name
going to different places (2.4.2, 2.4.4). Each of those items is a single media
object that *is* titled, so the placeholder is replaced by that title, in the
`<title>`, in the page heading and in every link that pointed at it. Two items
(20 and 22) have no media at all and read "Item 20" / "Item 22".

### Chrome

The **"Powered by Omeka S" footer credit** on all 72 pages is replaced by the
**GMU Department of History and Art History** logo, linked to
`historyarthistory.gmu.edu`, following commit `83180e5d9b` and the
`20.rrchnm.org` and `virginiaslostat` archives. The JSON-LD block Omeka wrote
into each resource page, and any mention of Omeka inside archived content, are
untouched.

### Robustness

Nothing outside the archive is fetched any more except Matomo and — on four
pages — the YouTube player. Verified in real headless Chromium with every other
host blocked at the network layer: across all 72 pages the only outbound
requests are `stats.rrchnm.org` (72) and `www.youtube-nocookie.com` (4).

- **Open Sans is self-hosted.** Every page's `<head>` loaded it from
  `fonts.googleapis.com`; with Google unreachable the whole site fell back to
  the browser's default sans. The `@font-face` blocks in `fonts.css` are
  Google's own, taken from the stylesheet it returns for exactly the request the
  theme made. Two reductions, both checked: of the ten unicode subsets per face
  only `latin` and `latin-ext` are kept, which covers every character in the
  archive; and Open Sans v44 is a *variable* font, so the three weights the
  theme asked for resolve to one identical file per (style, subset) — 12
  downloads, four distinct files by sha256 — which is why the six pinned
  `font-weight` declarations collapse into the `400 700` range the file
  actually carries.
- **jQuery 3.5.1 is vendored** (sha256 `f7f6a589…`, matching the published
  SRI). Every page loaded it from `ajax.googleapis.com` with no fallback, and
  `default.js` is entirely inside `(function($) {…})(jQuery)` — so a blocked
  CDN took the navigation and the iframe sizing with it.
- **Font Awesome 5 is self-hosted already**, but the crawl had saved the
  `.eot` twice, once under the literal filename `fa-solid-900.eot?` — a name no
  web server can serve, because the `?` starts a query string. The `@font-face`
  is trimmed to `woff2` + `woff`; the `.eot`, `.ttf` and `.svg` sources only
  ever served IE8 and Android 4.
- The crawl's asset filenames carried their cache-busting query strings into
  the *filenames* (`style.css?v=1.6.0.css`, `global.js?v=3.1.1`). They are
  named plainly now.
- Every `href`, `src` and `action` is relative, except `/files/…`, which is
  root-absolute so it reaches the bucket.

### Media

The 111 objects under `files/{original,large,medium,square,asset}` (50 MB) were
excluded at crawl time and are **not in this repo** (`.gitignore` blocks all
five). They were fetched from the origin into a staging tree outside this
repository, with a `manifest.tsv` recording each object's URL, path, size and
sha256, for loading into the object bucket. The list came from the API
(`o:original_url` and `o:thumbnail_urls` on each of the 28 media records, plus
the item-set thumbnail), not from a crawl, so it is complete by construction:
26 originals — two media are YouTube embeds and have no original — and 28 each
of `large`, `medium` and `square`.

Until the bucket and the web server's `/files/` handler are live on the deployed
host, every image 404s; they previously rendered only by hot-linking the origin.
Check with:

```sh
curl -sIL https://iowmaterial.dev.chnm.gmu.edu/files/square/cfceec5151cd6befa3fa9490f042c7941309a3fb.jpg
```

### Maps

There is **no interactive map in this archive**, and there never was one on the
origin: no Omeka S Mapping module, no Geolocation, no Leaflet on any of the 71
content URLs the origin serves. Three of the items *are* maps, and all three are static
images that now come from the bucket with real alt text — the Fra Mauro map of
c. 1460 (item 1), the Smithsonian's monsoon trading routes (item 4, the
homepage's lead image, previously hot-linked to the origin) and Brad Skopyk's
Spilhaus-projection map (item 57).

The one interactive map the site *points at* belongs to somebody else. The
"Continuing the Conversation: Four Objects" page links to the map that went with
Nancy Um and Meha Priyadarshini's talk, an R `leaflet` htmlwidget hosted on
`indianoceanexchanges.com` and drawing `CartoDB.Positron` tiles — the same
licensed CARTO basemap the sibling archives replaced with self-hosted Protomaps,
but on a domain this project does not control, so there is nothing to convert.
What was fixed is the hop in front of it: the link went through
`http://bit.ly/4Objects`, so the archive depended on a URL shortener continuing
to exist *and* on plain HTTP. It points at the resolved `https://` URL now.

### Video

Four pages embed one of two YouTube recordings of the talks. The embeds are
switched to **`youtube-nocookie.com`**, which serves the identical player
without setting a tracking cookie until the visitor presses play, and are
`loading="lazy"` with a `title`. They are the archive's one remaining
third-party dependency, and a deliberate one: the recordings are not in the
archive, so a click-to-play facade would buy a page load without removing the
dependency. If the videos are ever deposited somewhere the project controls,
this is the thing to revisit.

### Analytics

Matomo, site id **97**, at `https://stats.rrchnm.org/`. All 46 crawled pages
already carried it; the block is normalised to one identical copy across all 72,
and the three generated pages inherit it with the rest of the chrome.

### Redirects

`redirects.caddy` repairs the extensionless URLs the export renamed
(`/s/Material-Histories/item/4` → `…/4.html`), sends the site root and
`/s/Material-Histories/page/home` to `/` — the crawl held three byte-identical
copies of the home page and the archive keeps one — carries the old
`fulltext_search` query on to `search.html`, collapses the server-side browse
pagination onto the one-page listing, points the dead `four-objects-video` slug
at the page that has the recording, and answers `410` for `/api`, `/admin` and
`/login`, which no static host can stand in for. Every rule was checked with
`caddy validate` and exercised against a running Caddy 2.10.2.

### Deployment note

The archive must be served **at a domain root**: `/files/…` and the Pagefind
result links are root-absolute, as they are on the sibling archives. It is at
`iowmaterial.dev.chnm.gmu.edu` today, for both dev and prod
(`.github/workflows/iowmaterialhistorieswebinar.org--deploy.yml`). Flipping
`website-prod-fqdn` to `iowmaterialhistorieswebinar.org` is the cutover and is
deliberately **not** part of this work — the origin is still live and still
serving the real site.

That flip is what makes one loose end resolve: the `@id` permalinks Omeka wrote
into the JSON-LD block on all 59 resource pages still read
`https://iowmaterialhistorieswebinar.org/api/items/4`, which is what an
identifier minted before the migration should keep saying. Nothing in the
archive *fetches* from that host — those are text, and every `href`, `src` and
`action` is relative or root-absolute.

### Known gaps

- **Four alt texts** are non-descriptive at source (`Pombo_Image 1`–`4`) — see
  above.
- **Four outbound links have rotted** since 2021, all of them speaker profile
  pages on third-party sites that reorganised: Edinburgh (Meha Priyadarshini),
  NYU (Urmila Mohan), Hope College (Marsely Kehoe), and the Seattle Art Museum
  object page, whose URL carries a stale `jsessionid`. They were live when
  published and are left as the authors wrote them; repairing them is a
  curatorial call, not a migration one. The three WorldCat links and the Met
  link answer 403/429 to a script but resolve in a browser.
- One archived link had a Google Books URL pasted after a bare `http://` and a
  non-breaking space, so it resolved to nothing. That one *is* repaired: it is a
  typo, not a moved page.
- The Blog page's "Video Recordings of Talks" section lists only the first
  talk's recording; the second is on `beyond-the-margins-blog`, which nothing
  but item 68 links to. That is how the origin was published, and adding a link
  would be writing new content rather than preserving it. Search and the item
  browse both reach it.

## wget

Crawled by `multi-wget.py` on 2026-05-27.

**Seed:** `https://iowmaterialhistorieswebinar.org/`

**Run**

- started:   2026-05-27 16:13:12
- finished:  2026-05-27 16:13:49
- duration:  37s (wrapper) · 37s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- downloaded: 57 files, 1.2M (42.5 MB/s)
- links converted: 49 files in 0.03s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 57 | 3 | 1 | 0 |

**Startup warnings** (from `.crawl/crawl.log`)

- Both --no-clobber and --convert-links were specified, only --convert-links will be used.

### Failures (1)

| status | url |
|--------|-----|
| 404 | https://iowmaterialhistorieswebinar.org/s/Material-Histories/page/four-objects-video |

That 404 is real, and it is the origin's, not the crawler's: two pages link to a
video page that was never published. Both links now point at
`page/four-objects-blog`, which is where that recording actually is.

## Surviving absolute URLs to dead origin

In-tree HTML scan. `--convert-links` only rewrites refs to files wget actually
downloaded — anything filtered stayed as the absolute origin URL and would 404
once the live site is gone.

Measured across the 46 crawled pages, and again across the 72 rebuilt ones.

| attr      | at crawl | after retrofit |
| --------- | -------: | -------------: |
| `src=`    |       54 | 0 |
| `action=` |       46 | 0 |
| `href=`   |       19 | 0 |

**Where those 119 pointed, at crawl time**

| count | prefix |
| ----: | ------ |
|    48 | `s/Material-Histories/…` — 46 search-form actions, and the two dead `four-objects-video` links |
|    26 | `files/large/` |
|    26 | `files/square/` |
|    17 | `files/original/` |
|     2 | `files/medium/` |

No `href`, `src` or `action` anywhere in the archive resolves to
`iowmaterialhistorieswebinar.org` now. What remains is 548 plain-text mentions
across the 59 resource pages: the JSON-LD block Omeka wrote into each one, whose
`@id` and `thumbnail_display_urls` are identifiers rather than links, and are
not fetched.

## Rebuilding

The origin was live while this was done, and the API is what everything was
built from. To redo the harvest while it still answers:

```sh
for n in items media site_pages item_sets sites; do
  curl -s "https://iowmaterialhistorieswebinar.org/api/$n?per_page=100" -o "api-$n.json"
done
```

Every page URL in the archive is derivable from those four files, and every
media object from `o:original_url` and `o:thumbnail_urls` in `api-media.json`.
The media staging tree and its `manifest.tsv` are at
`~/media-staging/iowmaterialhistorieswebinar.org/` on the machine this was run
on; all 111 objects verify against the manifest's sha256 sums.
