# chnm.gmu.edu/declaration

"Interpreting the Declaration of Independence by Translation", the companion site to the
*Journal of American History* round table (vol. 85, no. 4, March 1999). Hand-built in 1999 with
GoLive CyberStudio 3 and Claris Home Page 3.0; a frameset (`index.html`) loads `one.html` and the
essays in the top frame and `menu.html` in the bottom one.

## wget

Crawled on 2026-11-17 (chnm/sustainability#154).

**Seed:** `https://chnm.gmu.edu/declaration/`

**Command** (run in an empty directory):

```
wget --mirror --page-requisites --convert-links --adjust-extension --no-parent -e robots=off --wait=0.5 --random-wait --tries=3 https://chnm.gmu.edu/declaration/
```

**Run**

- started:   2026-11-17 13:22:30
- finished:  2026-11-17 13:24:08
- duration:  1m 38s (wget wall-clock)
- status:    exit 0
- downloaded: 176 files, 5.7M
- links converted: 83 files in 0.1s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 176 | 0 | 0 | 0 |

Files: 82 `.html`, 1 `.htm`, 84 `.gif`, 8 `.jpg`, 1 `.png`. No stylesheets, PDFs, image maps,
applets or scripts other than the Piwik tracker.

### Failures

None.

## Gaps checked

- Every local `href`/`src`/`lowsrc` in the tree resolves to a file in the copy.
- One absolute self-link (`menu.html` "Home", `http://chnm.gmu.edu/declaration`) was rewritten to
  `index.html` so the copy works from its own root. No root-relative `/declaration/...` links.
- The server returns 403 for directory listings, so unlinked files were looked for in the Wayback
  Machine CDX index (`chnm.gmu.edu/declaration/*`, status 200). URLs it knows that the crawl did not
  fetch, none of them linked from any page in the copy, and all now 302 to rrchnm.org on the live
  server:
  - `japanese/aruga.html` and about 100 `japanese/aruga-N.gif` character images: an earlier version
    of Aruga's essay, replaced by `japanese/aruga2.html`.
  - `about1.html`, `adams2` (no extension), `japanese/japan3/test`.
  - `Russian1/*.html`, `Russian2/*.html`: capitalized duplicates of `russian1/`, `russian2/`.
  - WordPress-style `...-of-independence-by-translation/` and `/feed/` paths.
- Links left pointing at the live web: chnm.gmu.edu (home, copyright, requests), Creative Commons,
  the *JAH* site at indiana.edu, rrchnm.org, and the dead chnmdev Piwik tracker.
