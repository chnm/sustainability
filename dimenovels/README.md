# American Women's Dime Novel Project

Static copy of <https://chnm.gmu.edu/dimenovels/>, built from Felicia Carr's research on women's dime novels in nineteenth-century America (WordPress 4.9, 2013–2015).

Source: the flattened copy deposited in MARS, George Mason University's digital repository, by RRCHNM in 2020: `chnm.gmu.edu.zip` in <http://hdl.handle.net/1920/11710> (doi:10.13021/MARS/2666, gmu.tind.io record 75574; MD5 96cc942aae67b357399e767d0ca14dbd). The same record holds a WARC of the site.

The import (`scripts/dimenovels_import.py`) dropped crawler debris (feeds, wp-json, xmlrpc, the `?p=N` shortlink duplicates), took the 380 cover thumbnails the crawl saved as 404 pages from chnm.gmu.edu/dimenovels, and made the internal links relative so the site works served from its own root. Accessibility work for chnm/sustainability#155 is in the `scripts/dimenovels_*.py` passes that follow.
