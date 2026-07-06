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
