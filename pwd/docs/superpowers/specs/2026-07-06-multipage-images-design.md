# Design: Fix missing multi-page images in PWD documents

*Date: 2026-07-06 · Branch: `fix/pwd-multipage-images`*

## Problem

Documents in the PWD Hugo site reference their scanned pages through a microfilm
**reel** model:

- Each document has `omeka_image_id` pointing to an Omeka **Image resource** (a reel).
- Each reel has an ordered list of page-image files in `data/media_map.json`.
- Each document has `page_start` (where on the reel it begins) and, ideally,
  `num_pages` (how many pages it spans).
- The document's `images:` frontmatter list is a slice of the reel:
  `reel_files[page_start-1 : page_start-1+num_pages]`.

When `num_pages` is missing, the migration scripts default it to `1`, so
multi-page documents get only their first image. The AI transcription pipeline
then transcribes just that one image and misses the rest of the document.

A prior fix ([`scripts/fetch_num_pages.py`](../../../scripts/fetch_num_pages.py),
commit `da98f3e5f`) patched the **7,410** documents where Omeka's API supplies
`bibo:numPages`. The remaining **~23,000** documents have no per-document
`numPages` value anywhere in Omeka, so no API or database fetch can recover it.

### What we learned about the source data

Investigation against the live Omeka instance
(`https://omeka.wardepartmentpapers.org`, VPN-only) established:

- The per-document `bibo:numPages` is genuinely **null** for the affected docs
  (verified on item 36398 and its six reel-siblings).
- The Image **reel** resource *does* carry a reliable `bibo:numPages` that equals
  its media-file count (e.g. reel 12415 "NOE06" → 3).
- The original site's **"[view document]"** link is a **reel viewer**: it always
  shows the *entire reel*, never a per-document subset. Verified on document
  67949, whose reel (YRS01, 534 images, shared by 946 documents) renders all 534
  pages. The `(N pages)` label on an item page is the reel's size, not the
  document's.

**Conclusion:** there is no authoritative per-document image list anywhere in
Omeka or on the original site. The correct `images:` list must be *derived* from
reel structure + `page_start`. This is a local computation — no API, VPN, or DB
dump required.

### `media_map.json` accuracy (verified)

The whole approach depends on `media_map.json` listing each reel's files in
correct **page order** with complete **coverage**. `media_map.json` is built by
[`build_media_map.py`](../../../scripts/build_media_map.py), which groups the
global media catalog by `item_id`, preserving catalog order. Verified against
live Omeka:

- **Order** matches each reel's canonical `o:media` order (which is ascending
  media id). Confirmed exactly on reel 12415 (3 files) and reel 24470 (534
  files; positions 0 / 267 / 533 aligned, media ids contiguous 138281–138814).
- **Coverage** matches the reel's actual attached media count in 50/50 sampled
  reels spread across the id range.
- A reel's declared `bibo:numPages` can **overstate** the files that actually
  exist (e.g. reel 16966 declares 11 pages but has only 7 media files — Omeka is
  missing 4 scans). `media_map` correctly lists the 7 that exist.

**Implication:** always slice against the actual `media_map` file list and clamp
to `len(reel_files)`. Never derive an index from a declared page count that could
exceed the available files.

## Goal

1. Rebuild the `images:` list (and derive `num_pages`) for the ~23,000 affected
   documents so multi-page documents include all their pages, without dumping
   unrelated pages onto documents that share a large reel.
2. Re-run the AI transcription pipeline on documents whose image list grew, so
   AI transcriptions cover the full document — behind a cost-estimate gate.

### Non-goals

- Re-fetching or re-deriving anything for the 7,410 documents that already have
  authoritative `bibo:numPages`. They are left untouched.
- Changing the document template's image display or the transcription pipeline
  itself.
- Recovering a "true" per-document page count where the source data cannot
  express one (pile-up reels); we apply a defined policy instead.

## Approach: size-and-structure-aware slicing

Group all documents by `omeka_image_id`. For each reel, read the `page_start` of
every document on it and the reel's file list from `media_map.json`. Classify the
reel, then assign each affected document its images. **Skip any document that
already has `num_pages`** (authoritative from the prior fix).

Three buckets (measured counts over the current content tree):

| Bucket | Definition | Count | Rule | Loses pages? |
|---|---|---|---|---|
| **Single-doc reel** | Reel referenced by exactly one document | 10,286 | Attach the whole reel | No |
| **Dense multi-doc reel** | `page_start`s span the reel (`max(page_start) > 0.5 × reel_size`) | 12,760 | Slice `page_start → next distinct page_start`; last group → end of reel | No |
| **Pile-up reel** | Multiple docs, `page_start`s clustered (do not span the reel; e.g. NOE06: 7 docs mostly `page_start=1` on 3 images) | 311 | Attach the whole reel | No |

### Why this satisfies "never lose pages"

Slicing a dense reel by neighbor `page_start`s is a **partition**: each document
gets `[page_start, next_document_page_start)`, the last document runs to the end
of the reel, and every reel page is assigned to at least one document. No page is
dropped. Documents sharing a `page_start` (duplicates within a dense reel) each
receive the same slice — acceptable, and still lossless.

Whole-reel assignment is reserved for reels where slicing is meaningless (one
document owns the reel, or `page_start`s pile up and cannot partition it). These
reels are small in practice, so whole-reel adds at most a few pages.

### Why not literal whole-reel everywhere

Measured blast radius for AI transcription (image-pages to transcribe):

| Strategy | Image-pages |
|---|---|
| Literal whole-reel for every non-single-doc reel | 5,023,980 |
| Size-aware slicing (this design) | 78,123 |

Literal whole-reel would attach a 534-page reel to each of its 946 documents.
Size-aware slicing is ~64× smaller and assigns each document its actual pages.

## Components

### Part 1 — `scripts/fix_multipage_images.py` (new)

Pure-local script; no network.

Inputs: `content/document/*.md`, `data/media_map.json`.

Steps:
1. Scan all documents; parse `omeka_image_id`, `page_start`, presence of
   `num_pages`, and current `images:` list.
2. Group documents by reel; look up each reel's file list.
3. Classify each reel (single / dense / pile-up) using the definitions above.
4. For each document **without** `num_pages`, compute its image slice per its
   bucket's rule.
5. Write back the `images:` block and a derived `num_pages` into frontmatter,
   reusing the frontmatter-patching approach already in
   [`fetch_num_pages.py`](../../../scripts/fetch_num_pages.py).
6. `--dry-run` mode prints the plan without writing.
7. Report: documents changed, images added, and a per-bucket breakdown; write a
   machine-readable change manifest (list of `{omeka_id, old_count, new_count}`)
   to a JSON file for Part 2 to consume.

Edge cases:
- Reel `omeka_image_id` absent from `media_map.json` → skip, count as
  "no media on reel".
- `page_start` missing on a document → treat as `1`.
- Slice indices are always computed against the actual `media_map` file list and
  clamped to `len(reel_files)`. A reel's declared `bibo:numPages` may overstate
  the files that exist, so we never index past the real list (see
  "`media_map.json` accuracy" above).
- Idempotent: re-running produces no further changes.

### Part 2 — Re-transcription of grown documents

1. From Part 1's change manifest, select documents whose `images:` list grew
   (`new_count > old_count`).
2. Run [`scripts/estimate_transcription_cost.py`](../../../scripts/estimate_transcription_cost.py)
   over that set and present the estimate. **Stop here for explicit approval of
   the spend.**
3. On approval, run the transcription pipeline
   ([`scripts/transcribe.py`](../../../scripts/transcribe.py) /
   [`_transcription/`](../../../_transcription)) on only those documents,
   appending page transcriptions to `data/transcriptions_ai.json` keyed by
   `omeka_id`.

## Validation

- **Bucket spot-checks** against live Omeka reels (VPN):
  - Single-doc / pile-up: item 36398 → all 3 images of reel 12415.
  - Dense: a document mid-reel on 24470 (YRS01) → its correct slice, not all 534.
- **Regression check:** for a sample of the 7,410 already-fixed docs, confirm our
  slicing logic *would* reproduce their existing `images:` lists (sanity that the
  rule agrees with authoritative `numPages` where both exist).
- **Idempotence:** a second `--dry-run` after applying reports zero changes.
- **Build check:** `make build` succeeds and sampled document pages render the
  expanded galleries.

## Rollout

1. Run `fix_multipage_images.py --dry-run`; review the per-bucket report.
2. Apply; commit the frontmatter changes (large diff, ~23k files).
3. Run the cost estimate for re-transcription; get spend approval.
4. Run re-transcription on grown docs; commit `data/transcriptions_ai.json`.
5. Build and spot-check; open PR from `fix/pwd-multipage-images`.

## Open questions

- Is the `max(page_start) > 0.5 × reel_size` threshold for "dense vs pile-up"
  robust across the corpus, or do we need to inspect the borderline reels? The
  dry-run per-bucket report will surface counts to sanity-check before applying.
