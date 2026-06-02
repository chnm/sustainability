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

User-uploaded files (challenge thumbnails, source images) live in the
MinIO bucket at `obj.rrchnm.org/eagleeyecitizen.org/files/`. Only the
`files/` subdirectory is referenced; the bucket's `js/`, `css/`, and
`ctools/` directories are unused by the archive.

**Spaces in filenames must be `%20`, not `&#32;`.** The bucket only
serves the percent-encoded form. Decimal HTML entities (`&#32;`) don't
round-trip correctly when assigned via `setAttribute('src', …)` from
the challenges manifest.

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
