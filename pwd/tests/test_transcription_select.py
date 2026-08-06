import importlib.util
import sys
from pathlib import Path

_TRANSCRIPTION_DIR = Path(__file__).resolve().parent.parent / "_transcription"
sys.path.insert(0, str(_TRANSCRIPTION_DIR))

# Load _transcription/transcribe.py under a distinct module name so it does not
# collide with scripts/transcribe.py (a superseded SDK script that
# test_transcribe_selection.py imports as `transcribe`).
_spec = importlib.util.spec_from_file_location(
    "transcribe_claude_p", _TRANSCRIPTION_DIR / "transcribe.py"
)
transcribe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transcribe)


def test_resume_skips_done_and_respects_max_pages():
    manifest = [
        ("1", ["a.jpg"]),
        ("2", ["b.jpg"]),
        ("3", ["c.jpg", "d.jpg", "e.jpg"]),  # too big for max_pages=2
    ]
    done = {"1"}
    result = transcribe.select_todo(manifest, done, max_pages=2)
    # "1" is done -> skipped; "3" exceeds max_pages -> skipped
    assert result == [("2", ["b.jpg"])]


def test_skip_excludes_ids_in_both_modes():
    manifest = [("1", ["a.jpg"]), ("2", ["b.jpg"]), ("3", ["c.jpg"])]
    # resume mode: skip-listed "2" excluded even though not done
    assert transcribe.select_todo(manifest, done=set(), max_pages=50, skip={"2"}) == [
        ("1", ["a.jpg"]), ("3", ["c.jpg"])]
    # forced ids-file mode: skip-listed "2" excluded even though explicitly listed
    assert transcribe.select_todo(
        manifest, done=set(), max_pages=50, ids_filter={"1", "2", "3"}, skip={"2"}) == [
        ("1", ["a.jpg"]), ("3", ["c.jpg"])]


def test_ids_filter_forces_done_ids_and_excludes_unlisted():
    manifest = [
        ("1", ["a.jpg"]),
        ("2", ["b.jpg"]),
        ("3", ["c.jpg"]),
    ]
    done = {"1", "2", "3"}  # all already done
    result = transcribe.select_todo(manifest, done, max_pages=50, ids_filter={"1", "3"})
    # forced: 1 and 3 selected despite being done; 2 not listed -> excluded
    assert result == [("1", ["a.jpg"]), ("3", ["c.jpg"])]


def test_ids_filter_respects_max_pages():
    manifest = [
        ("1", ["a.jpg", "b.jpg", "c.jpg"]),  # exceeds max_pages=2
        ("2", ["d.jpg"]),
    ]
    done = {"1", "2"}
    result = transcribe.select_todo(manifest, done, max_pages=2, ids_filter={"1", "2"})
    # "1" listed but too big -> dropped; "2" listed and fits -> kept
    assert result == [("2", ["d.jpg"])]


def test_ids_filter_id_not_in_manifest_is_absent_no_crash():
    manifest = [("1", ["a.jpg"])]
    done = set()
    result = transcribe.select_todo(manifest, done, max_pages=50, ids_filter={"1", "999"})
    # "999" not in manifest -> simply absent, no error
    assert result == [("1", ["a.jpg"])]


def test_ids_filter_preserves_manifest_order():
    manifest = [
        ("5", ["e.jpg"]),
        ("3", ["c.jpg"]),
        ("9", ["i.jpg"]),
    ]
    done = {"5", "3", "9"}
    result = transcribe.select_todo(manifest, done, max_pages=50, ids_filter={"9", "5"})
    assert result == [("5", ["e.jpg"]), ("9", ["i.jpg"])]
