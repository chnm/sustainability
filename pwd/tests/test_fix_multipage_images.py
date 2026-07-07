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
