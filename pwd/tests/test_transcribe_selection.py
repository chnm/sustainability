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
