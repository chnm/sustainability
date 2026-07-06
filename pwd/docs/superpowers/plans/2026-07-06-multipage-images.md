# Multi-page Images Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the `images:` frontmatter list (and derive `num_pages`) for the ~23,000 PWD documents missing `num_pages`, so multi-page documents include all their pages, then re-transcribe only the documents whose image list grew.

**Architecture:** A new pure-logic script, `scripts/fix_multipage_images.py`, groups documents by their reel (`omeka_image_id`), classifies each reel by size, and computes each document's image slice locally from `data/media_map.json` + `page_start` — no network. It writes patched frontmatter, a change manifest, and a list of "grown" document ids. Part 2 wires that grown-ids list into the existing cost estimator and transcription pipeline via a new `--ids-file` flag.

**Tech Stack:** Python 3.13 (stdlib `re`, `json`, `os`, `argparse`, `pathlib`), `uv` for running, `pytest` for tests (new dev dependency). Hugo consumes the resulting frontmatter.

## Global Constraints

- Python `>=3.13` (from `pyproject.toml`); run everything with `uv run`.
- Frontmatter edits use **regex string surgery** (never `yaml.dump`) to keep diffs minimal — matches the existing pattern in `scripts/fetch_num_pages.py`. Do not reorder or requote existing keys.
- `SMALL_REEL_THRESHOLD = 5`: reels with `> 5` images are sliced; reels with `≤ 5` images (and single-doc reels) get the whole reel. Exposed as a CLI flag.
- Image slices are always computed against the actual `media_map` file list and clamped to `len(reel_files)` — a reel's declared page count can overstate the files that exist.
- Documents that already have `num_pages` (the 7,410 fixed by `fetch_num_pages.py`) are **never** modified.
- Transcriptions live in `data/transcriptions_ai.json`, keyed by `omeka_id` (string).
- Output files that must **not** be under `data/` (Hugo loads `data/` at build): write the manifest and grown-ids list to the project root (`multipage_fix_manifest.json`, `multipage_grown_ids.txt`).

---

## File Structure

- `scripts/fix_multipage_images.py` (create) — reel classification, image resolution, frontmatter patching, orchestration. Pure functions are importable for tests.
- `tests/test_fix_multipage_images.py` (create) — unit + integration tests for the fixer.
- `tests/test_transcribe_selection.py` (create) — tests for the transcription doc-selection logic.
- `scripts/transcribe.py` (modify) — add `select_documents()` + `--ids-file` (forced re-transcription of specific ids).
- `scripts/estimate_transcription_cost.py` (modify) — add `--ids-file` per-document estimate path.
- `pyproject.toml` (modify) — add `pytest` dev dependency.
- `justfile` (modify) — add `test` and `fix-images` recipes.

---

## Task 1: Project test scaffolding + reel classification

**Files:**
- Modify: `pyproject.toml`
- Create: `scripts/fix_multipage_images.py`
- Create: `tests/test_fix_multipage_images.py`

**Interfaces:**
- Produces: `classify_reel(num_docs: int, reel_size: int, threshold: int = 5) -> str` returning one of `"single"`, `"small"`, `"large"`. `SMALL_REEL_THRESHOLD: int = 5`.

- [ ] **Step 1: Add pytest as a dev dependency**

Run:
```bash
cd /Users/jheppler/work/chnm/sustainability/pwd
uv add --dev pytest
```
Expected: `pyproject.toml` gains a `[dependency-groups]` (or `[tool.uv]` dev) entry for `pytest`; `uv.lock` updates.

- [ ] **Step 2: Write the failing test**

Create `tests/test_fix_multipage_images.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fix_multipage_images as fix


def test_single_doc_reel_is_single():
    assert fix.classify_reel(num_docs=1, reel_size=3) == "single"
    assert fix.classify_reel(num_docs=1, reel_size=800) == "single"


def test_small_multi_doc_reel_is_small():
    # NOE06: 3 images, 7 docs -> whole reel
    assert fix.classify_reel(num_docs=7, reel_size=3) == "small"
    assert fix.classify_reel(num_docs=2, reel_size=5) == "small"


def test_large_reel_is_large():
    # YRS01: 534 images, 946 docs -> slice
    assert fix.classify_reel(num_docs=946, reel_size=534) == "large"
    assert fix.classify_reel(num_docs=2, reel_size=6) == "large"


def test_threshold_is_configurable():
    assert fix.classify_reel(num_docs=2, reel_size=8, threshold=10) == "small"
    assert fix.classify_reel(num_docs=2, reel_size=8, threshold=5) == "large"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_fix_multipage_images.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fix_multipage_images'`.

- [ ] **Step 4: Write minimal implementation**

Create `scripts/fix_multipage_images.py`:
```python
#!/usr/bin/env python3
"""
Rebuild images: lists (and derive num_pages) for documents missing num_pages.

Groups documents by their reel (omeka_image_id), classifies each reel by size,
and resolves each document's image slice locally from data/media_map.json and
page_start. No network access.

Usage:
    uv run python3 scripts/fix_multipage_images.py --dry-run
    uv run python3 scripts/fix_multipage_images.py
"""

SMALL_REEL_THRESHOLD = 5


def classify_reel(num_docs, reel_size, threshold=SMALL_REEL_THRESHOLD):
    """Return 'single', 'small', or 'large' for a reel.

    - single: reel referenced by exactly one document -> whole reel
    - small:  multiple docs, reel_size <= threshold   -> whole reel
    - large:  multiple docs, reel_size >  threshold   -> slice by page_start
    """
    if num_docs <= 1:
        return "single"
    if reel_size <= threshold:
        return "small"
    return "large"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_fix_multipage_images.py -v`
Expected: PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock scripts/fix_multipage_images.py tests/test_fix_multipage_images.py
git commit -m "feat: add reel classification for multi-page image fix"
```

---

## Task 2: Image resolution (whole-reel vs slice)

**Files:**
- Modify: `scripts/fix_multipage_images.py`
- Test: `tests/test_fix_multipage_images.py`

**Interfaces:**
- Consumes: `classify_reel` from Task 1.
- Produces: `resolve_images(bucket: str, page_start: int, all_page_starts: list[int], reel_files: list[str]) -> list[str]`. For `single`/`small` returns the whole reel; for `large` returns `reel_files[page_start-1 : next_distinct_start-1]`, clamped to at least one file and never past `len(reel_files)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_fix_multipage_images.py`:
```python
REEL3 = ["a.jpg", "b.jpg", "c.jpg"]
REEL_BIG = [f"{i:02d}.jpg" for i in range(10)]  # 10 files, indices 0..9


def test_single_and_small_get_whole_reel():
    assert fix.resolve_images("single", 1, [1], REEL3) == REEL3
    assert fix.resolve_images("small", 1, [1, 1, 2], REEL3) == REEL3
    # page_start is ignored for whole-reel buckets
    assert fix.resolve_images("small", 2, [1, 2], REEL3) == REEL3


def test_large_reel_slices_to_next_start():
    starts = [1, 4, 7]
    assert fix.resolve_images("large", 1, starts, REEL_BIG) == REEL_BIG[0:3]
    assert fix.resolve_images("large", 4, starts, REEL_BIG) == REEL_BIG[3:6]


def test_large_reel_last_doc_runs_to_end():
    starts = [1, 4, 7]
    assert fix.resolve_images("large", 7, starts, REEL_BIG) == REEL_BIG[6:10]


def test_large_reel_duplicate_starts_share_slice():
    starts = [1, 1, 2]
    # both page_start=1 docs get page 1 only (next distinct start is 2)
    assert fix.resolve_images("large", 1, starts, REEL_BIG) == REEL_BIG[0:1]


def test_slice_clamps_and_never_empty():
    # page_start beyond the reel clamps to the last available page
    assert fix.resolve_images("large", 99, [1, 99], REEL3) == ["c.jpg"]


def test_empty_reel_returns_empty():
    assert fix.resolve_images("single", 1, [1], []) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_fix_multipage_images.py -k resolve -v` and the new tests.
Expected: FAIL — `AttributeError: module 'fix_multipage_images' has no attribute 'resolve_images'`.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/fix_multipage_images.py`:
```python
def resolve_images(bucket, page_start, all_page_starts, reel_files):
    """Return the list of image filenames for one document."""
    n = len(reel_files)
    if n == 0:
        return []
    if bucket in ("single", "small"):
        return list(reel_files)
    # large: slice from page_start to the next distinct page_start on the reel
    distinct = sorted(set(all_page_starts))
    if page_start in distinct:
        i = distinct.index(page_start)
        nxt = distinct[i + 1] if i + 1 < len(distinct) else n + 1
    else:
        nxt = n + 1
    start = min(max(page_start - 1, 0), n - 1)
    end = min(nxt - 1, n)
    if end <= start:
        end = start + 1
    return list(reel_files[start:end])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_fix_multipage_images.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/fix_multipage_images.py tests/test_fix_multipage_images.py
git commit -m "feat: resolve document image slices from reel structure"
```

---

## Task 3: Frontmatter parsing and patching

**Files:**
- Modify: `scripts/fix_multipage_images.py`
- Test: `tests/test_fix_multipage_images.py`

**Interfaces:**
- Produces:
  - `parse_document(text: str) -> dict | None` with keys `omeka_id` (str), `image_id` (str|None), `page_start` (int, default 1), `has_num_pages` (bool), `image_count` (int).
  - `build_patched_text(text: str, new_images: list[str]) -> tuple[str, bool]` returning `(new_text, changed)`. Rewrites the `images:` block and inserts `num_pages: '<N>'` after `page_start` when absent.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_fix_multipage_images.py`:
```python
DOC_BLOCK = """---
authors:
- Benjamin Lincoln
omeka_image_id: 12415
images:
- a.jpg
omeka_id: 36398
page_start: '1'
title: Clothing
---

Body text here.
"""

DOC_EMPTY = """---
omeka_image_id: 999
images: []
omeka_id: 40000
page_start: '2'
---

Body.
"""

DOC_HAS_NP = """---
omeka_image_id: 12415
images:
- a.jpg
- b.jpg
num_pages: '2'
omeka_id: 50000
page_start: '1'
---

Body.
"""


def test_parse_document_block_form():
    rec = fix.parse_document(DOC_BLOCK)
    assert rec["omeka_id"] == "36398"
    assert rec["image_id"] == "12415"
    assert rec["page_start"] == 1
    assert rec["has_num_pages"] is False
    assert rec["image_count"] == 1


def test_parse_document_empty_images_and_num_pages():
    rec = fix.parse_document(DOC_EMPTY)
    assert rec["image_count"] == 0
    assert rec["page_start"] == 2
    rec2 = fix.parse_document(DOC_HAS_NP)
    assert rec2["has_num_pages"] is True
    assert rec2["image_count"] == 2


def test_build_patched_text_block_form():
    new_text, changed = fix.build_patched_text(DOC_BLOCK, ["a.jpg", "b.jpg", "c.jpg"])
    assert changed is True
    assert "images:\n- a.jpg\n- b.jpg\n- c.jpg\n" in new_text
    assert "num_pages: '3'" in new_text
    # untouched keys survive
    assert "title: Clothing" in new_text
    assert "Body text here." in new_text


def test_build_patched_text_empty_list_form():
    new_text, changed = fix.build_patched_text(DOC_EMPTY, ["x.jpg", "y.jpg"])
    assert changed is True
    assert "images:\n- x.jpg\n- y.jpg\n" in new_text
    assert "images: []" not in new_text
    assert "num_pages: '2'" in new_text


def test_build_patched_text_is_idempotent_after_num_pages():
    once, _ = fix.build_patched_text(DOC_BLOCK, ["a.jpg", "b.jpg"])
    # once num_pages exists, parse marks it done; patching again does not duplicate it
    twice, _ = fix.build_patched_text(once, ["a.jpg", "b.jpg"])
    assert twice.count("num_pages:") == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_fix_multipage_images.py -k "parse or patched" -v`
Expected: FAIL — `resolve`/`classify` pass but `parse_document` / `build_patched_text` are undefined.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/fix_multipage_images.py` (add `import re` at the top of the file):
```python
import re


def _images_block(frontmatter):
    """Return the raw 'images:' block text (the images: line plus any - items)."""
    m = re.search(r"^images:[^\n]*\n(?:- [^\n]*\n)*", frontmatter, re.M)
    return m.group(0) if m else ""


def parse_document(text):
    """Parse a document file's text into a record dict, or None if no frontmatter."""
    if not text.startswith("---"):
        return None
    end = text.index("---", 3)
    fm = text[3:end]

    def field(name):
        m = re.search(rf"^{name}:\s*[\"']?([^\"'\n]+)", fm, re.M)
        return m.group(1).strip() if m else None

    page_start_raw = field("page_start")
    block = _images_block(fm)
    return {
        "omeka_id": field("omeka_id"),
        "image_id": field("omeka_image_id"),
        "page_start": int(page_start_raw) if page_start_raw and page_start_raw.isdigit() else 1,
        "has_num_pages": re.search(r"^num_pages:", fm, re.M) is not None,
        "image_count": len(re.findall(r"^- \S+", block, re.M)),
    }


def build_patched_text(text, new_images):
    """Rewrite the images: block and insert num_pages if absent.

    Returns (new_text, changed).
    """
    if not text.startswith("---"):
        return text, False
    end = text.index("---", 3)
    fm = text[3:end]
    body = text[end + 3:]

    new_block = "images:\n" + "".join(f"- {fn}\n" for fn in new_images)
    new_fm, n = re.subn(
        r"^images:[^\n]*\n(?:- [^\n]*\n)*", new_block, fm, count=1, flags=re.M
    )
    if n == 0:
        new_fm = fm  # no images key; leave untouched (not expected for our docs)

    if not re.search(r"^num_pages:", new_fm, re.M):
        new_fm = re.sub(
            r"^(page_start:[^\n]*)$",
            lambda m: m.group(1) + f"\nnum_pages: '{len(new_images)}'",
            new_fm,
            count=1,
            flags=re.M,
        )

    new_text = "---" + new_fm + "---" + body
    return new_text, new_text != text
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_fix_multipage_images.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/fix_multipage_images.py tests/test_fix_multipage_images.py
git commit -m "feat: parse and patch document frontmatter for image fix"
```

---

## Task 4: Orchestration — scan, plan, manifest, dry-run

**Files:**
- Modify: `scripts/fix_multipage_images.py`
- Modify: `justfile`
- Test: `tests/test_fix_multipage_images.py`

**Interfaces:**
- Consumes: `classify_reel`, `resolve_images`, `parse_document`, `build_patched_text`.
- Produces:
  - `plan_changes(records: dict, media_map: dict, threshold: int) -> tuple[list, list, dict]` returning `(changes, grown_ids, stats)`, where `records` maps `omeka_id -> {"record": <parse_document dict>, "text": <str>}`, `changes` is a list of `{"omeka_id", "bucket", "old_count", "new_count", "new_text"}`, `grown_ids` is the list of ids whose `new_count > old_count`, and `stats` is a count-by-bucket dict.
  - `main()` — CLI entry with `--dry-run` and `--small-reel-threshold`.

- [ ] **Step 1: Write the failing integration test**

Append to `tests/test_fix_multipage_images.py`:
```python
def _rec(text):
    return {"record": fix.parse_document(text), "text": text}


def test_plan_changes_buckets_and_grown():
    # reel 12415: small (3 imgs, 2 docs) -> both whole reel
    # reel 24470: large (needs >5 imgs) -> slice
    media_map = {
        "12415": ["a.jpg", "b.jpg", "c.jpg"],
        "24470": [f"{i}.jpg" for i in range(10)],
    }
    small_doc = DOC_BLOCK  # image_id 12415, page_start 1, 1 image currently
    small_doc2 = DOC_BLOCK.replace("omeka_id: 36398", "omeka_id: 36399")
    large_doc = """---
omeka_image_id: 24470
images:
- 0.jpg
omeka_id: 67949
page_start: '1'
---

Body.
"""
    large_doc2 = large_doc.replace("omeka_id: 67949", "omeka_id: 67950").replace(
        "page_start: '1'", "page_start: '4'"
    )
    records = {
        "36398": _rec(small_doc),
        "36399": _rec(small_doc2),
        "67949": _rec(large_doc),
        "67950": _rec(large_doc2),
    }
    changes, grown, stats = fix.plan_changes(records, media_map, threshold=5)
    by_id = {c["omeka_id"]: c for c in changes}
    assert by_id["36398"]["bucket"] == "small"
    assert by_id["36398"]["new_count"] == 3
    assert by_id["67949"]["bucket"] == "large"
    assert by_id["67949"]["new_count"] == 3      # pages 1..3 (next start 4)
    assert set(grown) == {"36398", "36399", "67949", "67950"}
    assert stats["small"] == 2 and stats["large"] == 2


def test_plan_changes_skips_num_pages_and_missing_reel():
    media_map = {"12415": ["a.jpg", "b.jpg"]}
    records = {
        "50000": _rec(DOC_HAS_NP),          # already has num_pages -> skip
        "40000": _rec(DOC_EMPTY),           # reel 999 not in map -> skip
    }
    changes, grown, stats = fix.plan_changes(records, media_map, threshold=5)
    assert changes == []
    assert grown == []
    assert stats["skip_has_num_pages"] == 1
    assert stats["skip_no_media"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_fix_multipage_images.py -k plan -v`
Expected: FAIL — `plan_changes` undefined.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/fix_multipage_images.py` (add imports `import os`, `import json`, `import argparse`, `from collections import Counter`, `from pathlib import Path` at the top):
```python
import os
import json
import argparse
from collections import Counter
from pathlib import Path

HUGO_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = HUGO_DIR / "content" / "document"
MEDIA_MAP_PATH = HUGO_DIR / "data" / "media_map.json"
MANIFEST_PATH = HUGO_DIR / "multipage_fix_manifest.json"
GROWN_IDS_PATH = HUGO_DIR / "multipage_grown_ids.txt"


def plan_changes(records, media_map, threshold):
    """Compute the set of changes without touching disk.

    records: {omeka_id: {"record": <parse dict>, "text": <str>}}
    Returns (changes, grown_ids, stats).
    """
    # Group page_starts by reel across ALL documents (including already-fixed
    # ones), so slice boundaries and doc counts are correct.
    reel_starts = {}
    for info in records.values():
        rec = info["record"]
        if rec and rec["image_id"]:
            reel_starts.setdefault(rec["image_id"], []).append(rec["page_start"])

    changes = []
    grown = []
    stats = Counter()
    for omeka_id, info in records.items():
        rec = info["record"]
        if not rec or not rec["image_id"]:
            continue
        if rec["has_num_pages"]:
            stats["skip_has_num_pages"] += 1
            continue
        reel = media_map.get(rec["image_id"])
        if not reel:
            stats["skip_no_media"] += 1
            continue
        starts = reel_starts[rec["image_id"]]
        bucket = classify_reel(len(starts), len(reel), threshold)
        images = resolve_images(bucket, rec["page_start"], starts, reel)
        new_text, _ = build_patched_text(info["text"], images)
        old_count, new_count = rec["image_count"], len(images)
        stats[bucket] += 1
        changes.append({
            "omeka_id": omeka_id,
            "bucket": bucket,
            "old_count": old_count,
            "new_count": new_count,
            "new_text": new_text,
        })
        if new_count > old_count:
            grown.append(omeka_id)
    return changes, grown, stats


def collect_records(content_dir):
    """Read every document .md into {omeka_id: {'record':..., 'text':..., 'path':...}}."""
    records = {}
    for fname in os.listdir(content_dir):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        path = os.path.join(content_dir, fname)
        with open(path) as f:
            text = f.read()
        rec = parse_document(text)
        if not rec or not rec["omeka_id"]:
            continue
        records[rec["omeka_id"]] = {"record": rec, "text": text, "path": path}
    return records


def main():
    ap = argparse.ArgumentParser(description="Fix multi-page document images")
    ap.add_argument("--dry-run", action="store_true", help="Plan only; write no .md files")
    ap.add_argument("--small-reel-threshold", type=int, default=SMALL_REEL_THRESHOLD,
                    help=f"Reels with <= N images get the whole reel (default {SMALL_REEL_THRESHOLD})")
    args = ap.parse_args()

    with open(MEDIA_MAP_PATH) as f:
        media_map = json.load(f)

    print(f"Scanning {CONTENT_DIR}...")
    records = collect_records(CONTENT_DIR)
    print(f"Documents scanned: {len(records)}")

    changes, grown, stats = plan_changes(records, media_map, args.small_reel_threshold)

    would_patch = sum(
        1 for c in changes if c["new_text"] != records[c["omeka_id"]]["text"]
    )
    patched = 0
    for change in changes:
        info = records[change["omeka_id"]]
        if change["new_text"] != info["text"] and not args.dry_run:
            with open(info["path"], "w") as f:
                f.write(change["new_text"])
            patched += 1

    manifest = [{k: c[k] for k in ("omeka_id", "bucket", "old_count", "new_count")}
                for c in changes]
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    with open(GROWN_IDS_PATH, "w") as f:
        f.write("\n".join(sorted(grown, key=int)) + ("\n" if grown else ""))

    print(f"\n{'=' * 50}")
    print(f"Done{'  (DRY RUN — no files written)' if args.dry_run else ''}")
    print(f"  single (whole reel):   {stats.get('single', 0)}")
    print(f"  small  (whole reel):   {stats.get('small', 0)}")
    print(f"  large  (sliced):       {stats.get('large', 0)}")
    print(f"  skipped (has num_pages): {stats.get('skip_has_num_pages', 0)}")
    print(f"  skipped (no media):      {stats.get('skip_no_media', 0)}")
    print(f"  documents that grew:   {len(grown)}")
    print(f"  files {'to patch (dry run)' if args.dry_run else 'patched'}: "
          f"{would_patch if args.dry_run else patched}")
    print(f"  manifest:   {MANIFEST_PATH}")
    print(f"  grown ids:  {GROWN_IDS_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_fix_multipage_images.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Add justfile recipes**

Add to `justfile`:
```
# Run the Python test suite
test:
    uv run pytest -q

# Rebuild multi-page image lists (use --dry-run first)
fix-images *ARGS:
    uv run python3 scripts/fix_multipage_images.py {{ARGS}}
```

- [ ] **Step 6: Commit**

```bash
git add scripts/fix_multipage_images.py tests/test_fix_multipage_images.py justfile
git commit -m "feat: orchestrate multi-page image fix with manifest and dry-run"
```

---

## Task 5: Cost estimate for a specific set of documents

**Files:**
- Modify: `scripts/estimate_transcription_cost.py`
- Test: `tests/test_transcribe_selection.py`

**Note:** the estimator's existing default path parses `image_id:` from frontmatter, but current documents use `omeka_image_id:` — so the whole-corpus path under-counts. We are **not** fixing that here; we add a correct, self-contained per-document path used for our grown-docs estimate.

**Interfaces:**
- Produces: `parse_images_list(filepath) -> tuple[str|None, list[str]]` and `estimate_for_ids(ids_file: str, samples: int) -> None` (prints the estimate). New CLI flag `--ids-file`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_transcribe_selection.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import estimate_transcription_cost as est

DOC = """---
omeka_image_id: 12415
images:
- a.jpg
- b.jpg
omeka_id: 36398
page_start: '1'
---

Body.
"""


def test_parse_images_list(tmp_path):
    p = tmp_path / "36398.md"
    p.write_text(DOC)
    omeka_id, images = est.parse_images_list(str(p))
    assert omeka_id == "36398"
    assert images == ["a.jpg", "b.jpg"]


def test_parse_images_list_empty(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("---\nomeka_id: 1\nimages: []\n---\n\nBody.\n")
    omeka_id, images = est.parse_images_list(str(p))
    assert omeka_id == "1"
    assert images == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_transcribe_selection.py -k parse_images -v`
Expected: FAIL — `estimate_transcription_cost` has no `parse_images_list`.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/estimate_transcription_cost.py`:
```python
def parse_images_list(filepath):
    """Return (omeka_id, [image_filenames]) from a document's frontmatter."""
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return None, []
    fm = content[3:content.index("---", 3)]
    omeka_id = None
    images = []
    in_images = False
    for line in fm.split("\n"):
        if line.startswith("omeka_id:"):
            omeka_id = line.split(":", 1)[1].strip()
            in_images = False
        elif line.startswith("images:"):
            in_images = True
            if line.split(":", 1)[1].strip() == "[]":
                in_images = False
        elif in_images and line.startswith("- "):
            images.append(line[2:].strip())
        elif in_images and line.strip() and not line.startswith("- "):
            in_images = False
    return omeka_id, images


def estimate_for_ids(ids_file, samples):
    """Estimate cost of re-transcribing exactly the documents listed in ids_file.

    One request per document, using each document's full images: list. Mirrors
    the whole-run token assumptions (system 500 + user 30 per request,
    ~500 output tokens per page).
    """
    with open(ids_file) as f:
        ids = [line.strip() for line in f if line.strip()]

    all_images = []
    docs = 0
    for omeka_id in ids:
        path = CONTENT_DIR / f"{omeka_id}.md"
        if not path.exists():
            continue
        _, images = parse_images_list(str(path))
        if images:
            docs += 1
            all_images.extend(images)

    total_images = len(all_images)
    print(f"Documents to re-transcribe: {docs:,}")
    print(f"Total image-pages:          {total_images:,}")
    if total_images == 0:
        print("Nothing to estimate.")
        return

    print(f"\nSampling {min(samples, total_images)} images for size...")
    sample = all_images if total_images <= samples else random.sample(all_images, samples)
    for filename in sample:
        size = get_image_size_bytes(filename)
        if size:
            print(f"  {filename[:16]}... {size / 1024:.0f} KB")

    system_tokens, user_prompt_tokens = 500, 30
    tokens_per_image = estimate_image_tokens()
    output_tokens_per_page = 500

    total_input_tokens = docs * (system_tokens + user_prompt_tokens) + total_images * tokens_per_image
    total_output_tokens = total_images * output_tokens_per_page

    print(f"\n  Input tokens:  ~{total_input_tokens:,.0f}")
    print(f"  Output tokens: ~{total_output_tokens:,.0f}\n")
    print(f"  {'Model':<20} {'Input':>10} {'Output':>10} {'Total':>10}")
    print(f"  {'-' * 50}")
    for model_name, prices in MODELS.items():
        input_cost = (total_input_tokens / 1_000_000) * prices["input_per_m"]
        output_cost = (total_output_tokens / 1_000_000) * prices["output_per_m"]
        print(f"  {model_name:<20} ${input_cost:>8,.2f} ${output_cost:>8,.2f} ${input_cost + output_cost:>8,.2f}")
    print(f"\n  With Batch API (50% discount):")
    for model_name, prices in MODELS.items():
        input_cost = (total_input_tokens / 1_000_000) * prices["input_per_m"] * 0.5
        output_cost = (total_output_tokens / 1_000_000) * prices["output_per_m"] * 0.5
        print(f"  {model_name:<20} ${input_cost:>8,.2f} ${output_cost:>8,.2f} ${input_cost + output_cost:>8,.2f}")
```

Then in `main()`, add the argument and an early dispatch. After the existing `--samples` argument add:
```python
    parser.add_argument(
        "--ids-file", default=None,
        help="Estimate only the omeka_ids listed in this file (one per line), per-document"
    )
```
and immediately after `args = parser.parse_args()`:
```python
    if args.ids_file:
        estimate_for_ids(args.ids_file, args.samples)
        return
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_transcribe_selection.py -k parse_images -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/estimate_transcription_cost.py tests/test_transcribe_selection.py
git commit -m "feat: add per-document cost estimate via --ids-file"
```

---

## Task 6: Targeted re-transcription via `--ids-file`

**Files:**
- Modify: `scripts/transcribe.py`
- Test: `tests/test_transcribe_selection.py`

**Interfaces:**
- Produces: `select_documents(parsed_docs, transcriptions, resume=False, ids_filter=None) -> list[tuple[str, list[str]]]`. `parsed_docs` is an iterable of `(omeka_id, image_files)`. When `ids_filter` is a set, exactly those ids are selected **even if already transcribed** (forced re-transcription); `resume`/skip logic applies only when `ids_filter` is None. New CLI flag `--ids-file`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_transcribe_selection.py`:
```python
import transcribe


def test_select_documents_resume_skips_done():
    docs = [("1", ["a.jpg"]), ("2", ["b.jpg"]), ("3", [])]
    result = transcribe.select_documents(docs, {"1": "done"}, resume=True)
    # "1" already transcribed -> skipped; "3" has no images -> skipped
    assert result == [("2", ["b.jpg"])]


def test_select_documents_ids_filter_forces_retranscription():
    docs = [("1", ["a.jpg"]), ("2", ["b.jpg", "c.jpg"]), ("3", ["d.jpg"])]
    # 1 and 2 already transcribed, but ids_filter forces them anyway
    result = transcribe.select_documents(
        docs, {"1": "old", "2": "old"}, resume=True, ids_filter={"1", "2"}
    )
    assert result == [("1", ["a.jpg"]), ("2", ["b.jpg", "c.jpg"])]


def test_select_documents_ids_filter_ignores_unlisted():
    docs = [("1", ["a.jpg"]), ("2", ["b.jpg"])]
    result = transcribe.select_documents(docs, {}, ids_filter={"2"})
    assert result == [("2", ["b.jpg"])]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_transcribe_selection.py -k select_documents -v`
Expected: FAIL — `transcribe` has no `select_documents`.

- [ ] **Step 3: Write minimal implementation**

Add to `scripts/transcribe.py` (near `batch_transcribe`):
```python
def select_documents(parsed_docs, transcriptions, resume=False, ids_filter=None):
    """Choose which documents to transcribe.

    parsed_docs: iterable of (omeka_id, image_files).
    ids_filter: when a set, select exactly those ids (forced re-transcription),
                bypassing the resume-skip; when None, apply resume-skip.
    """
    selected = []
    for omeka_id, image_files in parsed_docs:
        if not omeka_id or not image_files:
            continue
        if ids_filter is not None:
            if omeka_id in ids_filter:
                selected.append((omeka_id, image_files))
            continue
        if resume and omeka_id in transcriptions:
            continue
        selected.append((omeka_id, image_files))
    return selected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_transcribe_selection.py -k select_documents -v`
Expected: PASS.

- [ ] **Step 5: Wire `select_documents` into `batch_transcribe` and add the CLI flag**

In `scripts/transcribe.py`, change `batch_transcribe`'s signature and its document-collection block. Replace:
```python
def batch_transcribe(model="claude-sonnet-4-6", limit=None,
                     resume=False, max_pages=50):
    """Transcribe all documents with images."""
    client = anthropic.Anthropic()

    # Load existing transcriptions if resuming
    transcriptions = load_existing_transcriptions() if resume else {}
    skipped = 0

    # Collect all documents with images
    doc_files = sorted(glob.glob(str(CONTENT_DIR / "*.md")))
    docs_to_process = []

    for doc_path in doc_files:
        omeka_id, image_files = parse_document_frontmatter(doc_path)
        if not omeka_id or not image_files:
            continue

        if resume and omeka_id in transcriptions:
            skipped += 1
            continue

        docs_to_process.append((omeka_id, image_files))

    if limit:
        docs_to_process = docs_to_process[:limit]
```
with:
```python
def batch_transcribe(model="claude-sonnet-4-6", limit=None,
                     resume=False, max_pages=50, ids_filter=None):
    """Transcribe all documents with images (or only ids_filter, forced)."""
    client = anthropic.Anthropic()

    # Preserve existing transcriptions when resuming or when re-transcribing a
    # targeted subset (so untargeted entries are not lost).
    transcriptions = (
        load_existing_transcriptions() if (resume or ids_filter is not None) else {}
    )

    doc_files = sorted(glob.glob(str(CONTENT_DIR / "*.md")))
    parsed_docs = (parse_document_frontmatter(p) for p in doc_files)
    docs_to_process = select_documents(
        parsed_docs, transcriptions, resume=resume, ids_filter=ids_filter
    )
    skipped = 0

    if limit:
        docs_to_process = docs_to_process[:limit]
```
Then in `main()`, add the argument after `--max-pages`:
```python
    parser.add_argument(
        "--ids-file", default=None,
        help="Re-transcribe only the omeka_ids in this file (one per line), overwriting them"
    )
```
and update the batch dispatch (the `elif args.batch:` block) to load the ids and pass them:
```python
    elif args.batch:
        ids_filter = None
        if args.ids_file:
            with open(args.ids_file) as f:
                ids_filter = {line.strip() for line in f if line.strip()}
        batch_transcribe(
            model=args.model,
            limit=args.limit,
            resume=args.resume,
            max_pages=args.max_pages,
            ids_filter=ids_filter,
        )
```

- [ ] **Step 6: Run the full suite to verify nothing regressed**

Run: `uv run pytest -q`
Expected: PASS (all tests across both test files).

- [ ] **Step 7: Commit**

```bash
git add scripts/transcribe.py tests/test_transcribe_selection.py
git commit -m "feat: support targeted re-transcription via --ids-file"
```

---

## Task 7: Execute, validate, and apply

This task runs the pipeline against real data. Each step has an explicit expected result to check before proceeding. **Do not run the transcription step (Step 6) without the cost gate in Step 5.**

- [ ] **Step 1: Dry-run the fixer and review the bucket report**

Run:
```bash
uv run python3 scripts/fix_multipage_images.py --dry-run
```
Expected: a report roughly matching — single ≈ 10,286; small ≈ 459; large ≈ 12,612; skipped (no media) ≈ 345; documents that grew in the thousands. `multipage_fix_manifest.json` and `multipage_grown_ids.txt` are written; no `.md` files change (`git status` shows only the two new root files).

- [ ] **Step 2: Spot-check the plan against known documents**

Run:
```bash
python3 -c "import json; m={d['omeka_id']:d for d in json.load(open('multipage_fix_manifest.json'))}; print('36398', m.get('36398')); print('67949', m.get('67949'))"
```
Expected: `36398` → bucket `small`, `new_count` 3. `67949` → bucket `large`, `new_count` equal to its slice (its page_start to the next document's page_start on reel 24470), not 534.

- [ ] **Step 3: Apply the fix**

Run:
```bash
uv run python3 scripts/fix_multipage_images.py
```
Expected: report shows `files patched` in the tens of thousands. `git status` shows many modified `content/document/*.md`.

- [ ] **Step 4: Verify idempotence and a sample diff**

Run:
```bash
git diff content/document/36398.md
uv run python3 scripts/fix_multipage_images.py --dry-run
```
Expected: the `36398.md` diff shows `images:` expanded to 3 files and a new `num_pages: '3'`. The second dry-run reports `small`/`large`/`single` all ≈ 0 and `documents that grew` = 0 (everything now has `num_pages`, so it is skipped) — confirming idempotence.

- [ ] **Step 5: Estimate re-transcription cost (GATE)**

Run:
```bash
uv run python3 scripts/estimate_transcription_cost.py --ids-file multipage_grown_ids.txt --samples 20
```
Expected: prints document count, total image-pages, and a per-model cost table. **Stop and get explicit approval of the spend before continuing.**

- [ ] **Step 6: Commit the frontmatter changes**

```bash
git add content/document/ multipage_fix_manifest.json multipage_grown_ids.txt
git commit -m "fix: expand images lists for multi-page documents

Derive images and num_pages for ~23k documents missing num_pages using
reel-size-aware slicing. See docs/superpowers/specs/2026-07-06-multipage-images-design.md"
```

- [ ] **Step 7: Re-transcribe grown documents (only after Step 5 approval)**

Run (start with a small `--limit` smoke test, then the full run):
```bash
uv run python3 scripts/transcribe.py --batch --ids-file multipage_grown_ids.txt --limit 3
uv run python3 scripts/transcribe.py --batch --ids-file multipage_grown_ids.txt
```
Expected: the smoke test transcribes 3 of the grown documents and overwrites their entries in `data/transcriptions_ai.json`; the full run processes the rest. Spot-check one entry to confirm it now covers multiple pages.

- [ ] **Step 8: Commit the transcriptions and build**

```bash
git add data/transcriptions_ai.json
git commit -m "data: re-transcribe documents whose image lists grew"
just build
```
Expected: `hugo --minify` completes; sampled document pages render the expanded galleries.

---

## Self-Review Notes

- **Spec coverage:** Part 1 (image lists) → Tasks 1–4, applied in Task 7 Steps 1–4,6. Part 2 (re-transcription behind cost gate) → Tasks 5–6, executed in Task 7 Steps 5,7. `media_map` accuracy / clamping → Task 2 (`resolve_images` clamp) and Global Constraints. Skip-already-fixed docs → Task 4 (`plan_changes` `skip_has_num_pages`). Reel-size threshold → Tasks 1–2, CLI flag in Task 4.
- **Threshold open question** (from the spec) is addressed operationally: the dry-run bucket report (Task 7 Step 1) lets us re-check counts, and `--small-reel-threshold` allows trying other values without code changes.
- **Type consistency:** `classify_reel` returns `"single"|"small"|"large"`, consumed verbatim by `resolve_images` (whole reel for `single`/`small`) and keyed in `stats`. `select_documents` / `estimate_for_ids` both read newline-delimited ids from the same `multipage_grown_ids.txt` produced by `main()`.
