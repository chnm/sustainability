# Creating Local Linkages

**A flattened static copy of the WordPress site `locallinkages.org`.**

Creating Local Linkages is an open-access professional development curriculum,
built by RRCHNM with IMLS funding (grant RE-85-17-0029-17), that teaches public
librarians historical research methods and digital history skills to share
with patrons doing local history. It has a five-module online course, a local
history activity guide with printable worksheets, and a set of resources and
tool tutorials (Omeka, TimelineJS, Juxtapose, Map Warper, Zotero).

## Source

This copy comes from Mason Archival Repository Service (MARS), George Mason
University's digital repository: <http://hdl.handle.net/1920/11870>
(gmu.tind.io record 75664), file `locallinkages.org.zip`, captured in August 2020
with WordPress 5.3.4. The same record also holds a WARC of the site and the
project's final report to IMLS.

The page text matches the static copy served at locallinkages.org in
November 2026, a later crawl.

## Structure

- `index.html`, `about.html` (and `about/index.html`): home and about
- `course/`: the introduction and modules 1 to 5, one directory per section
- `local-history-activity-guide/`: the activity guide and its three parts
- `resources/`: glossary, tutorials and planning pages
- `wp-content/uploads/`: images, PDFs and Word worksheets
- `wp-content/`, `wp-includes/`: theme (FoundationPress) and plugin assets

Removed from the archive as crawler debris: `wp-json/` (the REST index and
108 oEmbed responses), `wp-login.php` and its lost-password page, and the
`wp-admin/` assets only those login pages used.
