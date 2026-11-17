# gulaghistory.org

*Gulag: Many Days, Many Lives* and the National Park Service exhibit *GULAG: Soviet Forced Labor Camps and the Struggle for Freedom* (`nps/`).

## Source

The live gulaghistory.org was already a static crawl of the original Omeka site (links end in `.html`; Omeka's routes return 403), so this copy is a fresh wget mirror of it, taken by `scripts/gulaghistory_import.py` after:

```
wget --mirror --page-requisites --convert-links --adjust-extension --no-parent -e robots=off \
     --wait=0.3 --random-wait --tries=3 --domains=gulaghistory.org \
     https://gulaghistory.org/ https://gulaghistory.org/nps/
```

- started 2026-11-17T19:22:46Z, finished 2026-11-17T19:39:50Z, wget exit 8 (at least one 4xx/5xx)
- 1,977 files, 1.6 GB

| 2xx | 3xx | 4xx | 5xx |
|-----|-----|-----|-----|
| 1978 | 35 | 2 | 18 |

Failures:

| url |
|-----|
| https://gulaghistory.org/about/ |
| https://gulaghistory.org/archive/files/arrest_db590df2c4.mov |
| https://gulaghistory.org/archive/files/conflict_8eb977529f.mov |
| https://gulaghistory.org/archive/files/conflictclip_part2_9ae0bfa571.mov |
| https://gulaghistory.org/archive/files/fate_2680d992b8.mov |
| https://gulaghistory.org/archive/files/guards_0164dc3f0d.mov |
| https://gulaghistory.org/archive/files/intro_7f39e361eb.mov |
| https://gulaghistory.org/archive/files/labor_0865929231.mov |
| https://gulaghistory.org/archive/files/propaganda_60b86cf6ae.mov |
| https://gulaghistory.org/archive/files/solidarity_e2cf62fe3e.mov |
| https://gulaghistory.org/archive/files/suffering_336f713643.mov |
| https://gulaghistory.org/archive/files/survival_a9578794e0.mov |
| https://gulaghistory.org/exhibits/browse |
| https://gulaghistory.org/items/browse/ |
| https://gulaghistory.org/nps/about/contact.php |
| https://gulaghistory.org/nps/travelingexhibit/index.php |
| https://gulaghistory.org/resources/ |
| https://gulaghistory.org/resources/bibliography |
| https://gulaghistory.org/resources/teacher-resources |

The eleven `.mov` files are the original QuickTime versions of the exhibit clips; the pages play the MP4 and Ogg copies, which were fetched.

MARS (hdl 1920/11992, gmu.tind.io record 75712) also holds this project:

- `gulaghistory_nps.zip`, a 2026 crawl of the NPS exhibit; it matches `nps/` here.
- `GulagHistory_nehSite.zip`, the proof-of-concept site built for the NEH grant proposal. It was never public (`/neh/` on the live host returns 500) and is not in this copy.
- `gulag.warc.gz` (1.75 GB), a WARC of the site.

## What the import changes

- Omeka served item images and PDFs from extensionless routes (`files/download/N/fullsize`, `files/display/N/square_thumbnail`), so wget saved 581 of them as `.html`. They are renamed to `.jpg` / `.pdf` and every reference is rewritten.
- Five WordPress feed and xmlrpc files from `podcast/` are dropped.

## Media, not in git

`.gitignore` keeps the bulk media out of the repo: `archive/files/` (exhibit video and audio, including a 363 MB WAV), `files/download/` (full-size item images and PDFs) and `podcast/podpress_trac/` (the podcast MP3). That is 423 files, about 1.56 GB. `MEDIA.tsv` lists each with its size and MD5. They need to be served from object storage at the same paths before the old host goes away.
