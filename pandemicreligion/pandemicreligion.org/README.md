# Pandemic Religion: A Digital Archive

**A flattened static archive of the Pandemic Religion Omeka S hub site
`pandemicreligion.org`.**

`pandemicreligion.org` is a multi-site Omeka S install: its own **contributions** site
(~580 items) plus the **american-jewish-life** and **preaching-goes-viral**
sites, which are also published on their own domains. This archive keeps only
the hub's own contributions content; links into the AJL and PGV slugs are
rewritten to their dedicated archives (`americanjewishlife.org`,
`preachinggoesviral.org`) rather than duplicated here. (The crawl provenance
below reflects the full multi-site crawl.)

Flattened with `scripts/pandemicreligion_flatten.py --keep-browse-controls
--external-slug american-jewish-life=americanjewishlife.org
--external-slug preaching-goes-viral=preachinggoesviral.org`.

## Media is external

To keep the archive lean, **no media is committed**. Item images, downloads, and
site assets are referenced root-relatively (`/files/...`); flattening dropped
everything under `files/`. In deployment, Caddy serves `/files/...` from the
shared Pandemic Religion object-storage bucket (the seven Omeka S sites shared a
single `files/` store, so every site fronts the same bucket). In a bare local
preview (`python3 -m http.server`) media requests 404; page text and chrome are
unaffected.

## Search & browse

**[Pagefind](https://pagefind.app/)** header search (committed `pagefind/`;
rebuild with `npx pagefind@1.5.2 --site .`). The contributions browse spans
multiple pages, so pagination controls + default-sorted paginated browse pages
are kept.

## Local preview

```sh
cd pandemicreligion.org
python3 -m http.server 8000   # open http://localhost:8000/index.html
```

## Known limitations

- The "Share Your Experience" contribute form is replaced with a note.
- Sort dropdown / advanced search inert in a static mirror. Analytics removed;
  maps use committed Leaflet markers.

---

## Crawl provenance

### wget

Crawled by `multi-wget.py` on 2026-07-09.

**Seed:** `https://pandemicreligion.org/`

**Run**

- started:   2026-07-09 18:37:55
- finished:  2026-07-10 00:05:42
- duration:  19673s (wrapper) · 5h 27m 47s (wget wall-clock)
- status:    `ok(ec=8)`  — wget exit 8 = at least one 4xx/5xx; the wrapper treats this as success.
- links converted: 16726 files in 6.6s

**Responses**

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 16895 | 24 | 41 | 0 |

#### Failures (41)

| status | url |
|--------|-----|
| 404 | https://pandemicreligion.org/s/contributions/item/19241 |
| 404 | https://pandemicreligion.org/themes/centerrow/asset/img/vimeo-play.png |
| 404 | https://pandemicreligion.org/themes/centerrow/asset/img/video-play.png |
| 404 | https://pandemicreligion.org/themes/centerrow/asset/img/youtube-play.png |
| 404 | https://pandemicreligion.org/themes/centerrow/asset/img/loading.gif |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/svara.org |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/tiny.cc/jewishmentalhealth |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/asktherav.com |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/CrownHeights.info |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/player.vimeo.com%5C/video%5C/406699569?app_id=122963%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/t.co%5C/q59Wq6l9zd%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/MarkDever%5C/status%5C/1238424118506262528?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/MarkDever%5C/status%5C/1238527208702050306?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/t.co%5C/bGLCT4XDEO%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/chbcdc%5C/status%5C/1318209134269956097?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/player.vimeo.com%5C/video%5C/429406222?app_id=122963%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/SVNewsAlerts%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/t.co%5C/r7hYwJZKVT%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/SVNewsAlerts%5C/status%5C/1313342883341258757?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/t.co%5C/rPRKMK4NvZ%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/SVNewsAlerts%5C/status%5C/1313343860626595842?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/NYGovCuomo?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/t.co%5C/UCQf3lZu7c%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/twitter.com%5C/SVNewsAlerts%5C/status%5C/1313675223728893953?ref_src=twsrc%5Etfw%5C%22 |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/kosherwine.com |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/kashrut.com |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/player.vimeo.com%5C/video%5C/490903195?app_id=122963%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/item/Original%20article |
| 404 | https://pandemicreligion.org/s/contributions/media/%5C%22https:%5C/%5C/player.vimeo.com%5C/video%5C/406632491?app_id=122963%5C%22 |
| 404 | https://pandemicreligion.org/s/preaching-goes-viral/item/%20http://www.jstor.org/stable/j.ctv1j13zb3.26 |
| 404 | https://pandemicreligion.org/s/preaching-goes-viral/item/%20http://www.jstor.org/stable/resrep26356.43 |
| 404 | https://pandemicreligion.org/s/contributions/item/tiny.cc/jewishmentalhealth |
| 404 | https://pandemicreligion.org/s/contributions/item/asktherav.com |
| 404 | https://pandemicreligion.org/s/contributions/item/CrownHeights.info |
| 404 | https://pandemicreligion.org/s/contributions/%5C%22https:%5C/%5C/www.facebook.com%5C/plugins%5C/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto.php%3Ffbid%3D10158076537734597%26set%3Da.290245499596%26type%3D3&width=500%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/item/kosherwine.com |
| 404 | https://pandemicreligion.org/s/contributions/item/kashrut.com |
| 404 | https://pandemicreligion.org/s/contributions/item/%3Ciframe%20src=%22https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto.php%3Ffbid%3D10158076537734597%26set%3Da.290245499596%26type%3D3&width=500%22%20width=%22500%22%20height=%22486%22%20style=%22border:none;overflow:hidden%22%20scrolling=%22no%22%20frameborder=%220%22%20allowTransparency=%22true%22%20allow=%22encrypted-media%22%3E%3C/iframe%3E |
| 404 | https://pandemicreligion.org/s/contributions/item/%5C%22https:%5C/%5C/www.facebook.com%5C/plugins%5C/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto.php%3Ffbid%3D10158076537734597%26set%3Da.290245499596%26type%3D3&width=500%5C%22 |
| 404 | https://pandemicreligion.org/s/contributions/item-set/%5C%22https:%5C/%5C/www.facebook.com%5C/plugins%5C/post.php?href=https%3A%2F%2Fwww.facebook.com%2Fphoto.php%3Ffbid%3D10158076537734597%26set%3Da.290245499596%26type%3D3&width=500%5C%22 |
| 404 | https://pandemicreligion.org/s/american-jewish-life/item/onetable.org |

#### Excluded (81362)

URLs wget declined to fetch (pre-fetch filtering via `--reject-regex`, `--exclude-directories`, `--domains`, etc).

**Dir-level excludes** (collapsed):

| reason | path | count |
|--------|------|------:|
| LIST | `/files/original` | 7138 |
| LIST | `/files/large` | 4476 |
| LIST | `/files/medium` | 9405 |
| LIST | `/files/square` | 3323 |

**URL-level excludes** (one row per URL in `.crawl/excluded.tsv`):

| reason | count |
|--------|------:|
| DOMAIN | 56607 |
| REGEX | 413 |

Full list in `.crawl/excluded.tsv` (gitignored — regenerated on each crawl).
