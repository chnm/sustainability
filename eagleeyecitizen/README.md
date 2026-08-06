# Eagle Eye Citizen — static archive

Static archive of the former Drupal site at `eagleeyecitizen.org`.

See `AGENTS.md` for deployment, banner, and accessibility notes.

## Media file rewrites

The static export references user-uploaded media by their original
in-repo path. Those bytes are **not** checked in — they live in the
MinIO bucket at `obj.rrchnm.org`. The production web server must rewrite
the in-repo paths to the bucket URLs:

| Request path (as it appears in the HTML)  | Target URL                                                |
|-------------------------------------------|-----------------------------------------------------------|
| `/sites/default/files/<name>`             | `https://obj.rrchnm.org/eagleeyecitizen.org/files/<name>` |

`<name>` passes through unchanged, including any subdirectories and the
query string. Spaces must reach the bucket as `%20` (the bucket 404s on
any other encoding) — browsers already do this when fetching, so no
extra transform is needed on the server side.
