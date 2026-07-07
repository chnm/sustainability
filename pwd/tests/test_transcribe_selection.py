import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import estimate_transcription_cost as est
import transcribe

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


def test_parse_images_list_inline_nonempty(tmp_path):
    p = tmp_path / "y.md"
    p.write_text("---\nomeka_id: 2\nimages: [a.jpg, b.jpg]\n---\n\nBody.\n")
    omeka_id, images = est.parse_images_list(str(p))
    assert omeka_id == "2"
    assert images == ["a.jpg", "b.jpg"]


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
