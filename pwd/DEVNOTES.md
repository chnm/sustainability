# DEVNOTES.md

Development notes and deployment TODOs for the PWD Hugo site.

---

## Deployment: URL Redirects

The original Omeka S site used URLs like `/s/home/item/{id}`. These are no longer generated as Hugo aliases. Instead, handle redirects at the web server level.

Example nginx config:

```nginx
# Redirect old Omeka item URLs to Hugo content pages.
# Documents are the vast majority of items (IDs roughly 36000-79999),
# but collections and repositories share the same ID space.
# A catch-all that tries document first covers most cases.

location ~ ^/s/home/item/(\d+)$ {
    return 301 /document/$1/;
}

location ~ ^/item/(\d+)$ {
    return 301 /document/$1/;
}
```

If finer-grained routing is needed (e.g., redirecting collection/repository IDs to their correct content type), a map block or try_files approach could check each path. In practice, most old bookmarked URLs are documents.

---

## Deployment: Media Files / CDN

Currently media files (document images) are not included in the Hugo build (`static-media` removed from `staticDir`). Long-term plan:

- Host media files on object storage (MinIO, S3, or similar CDN)
- Set a site param in `hugo.toml` like `[params] mediaBaseURL = "https://cdn.example.com/pwd-media"`
- Templates reference images as `{{ site.Params.mediaBaseURL }}/files/large/{{ $filename }}`
- No media files need to be part of the Hugo build at all

For local development, media can be served separately or symlinked as needed.

---

## Taxonomy Decisions

### Active taxonomies (4)
- `authors` — document author(s)
- `recipients` — document recipient(s)
- `collections` — archival collection name(s)
- `doc_types` — document type (e.g., "Autograph Letter Signed")

### Not taxonomies (kept as plain front matter)
- `notable_persons` — free-text, 41,930 unique terms, 70% used once
- `notable_locations` — free-text, 9,166 unique terms, 69% used once
- `notable_items` — free-text, 49,837 unique terms, 82% used once

These are uncontrolled vocabulary annotations. They display on document pages but don't generate browsable index/term pages. Pagefind search will cover discovery across these fields.

---

## Build Performance Notes

- Dropping 3 notable_* taxonomies eliminated ~100k+ taxonomy term pages
- Removing aliases eliminated ~88k redirect HTML files
- Removing `static-media` from `staticDir` avoids copying ~26k media files during build
- Remaining build: ~44k content pages + ~4 taxonomy indexes + taxonomy term pages + paginator pages
