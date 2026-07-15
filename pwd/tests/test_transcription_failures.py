import csv
import importlib.util
import sys
from pathlib import Path

_TRANSCRIPTION_DIR = Path(__file__).resolve().parent.parent / "_transcription"
sys.path.insert(0, str(_TRANSCRIPTION_DIR))

# Load _transcription/transcribe.py under a distinct module name so it does not
# collide with scripts/transcribe.py (a superseded SDK script).
_spec = importlib.util.spec_from_file_location(
    "transcribe_claude_p_failures", _TRANSCRIPTION_DIR / "transcribe.py"
)
transcribe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transcribe)


def _rows(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.reader(f))


# ---------------------------------------------------------------------------
# log_failure — structured failure CSV
# ---------------------------------------------------------------------------

def test_log_failure_writes_header_on_first_write(tmp_path):
    csv_path = tmp_path / "failures.csv"
    transcribe.log_failure(
        csv_path, "12345", 3, "timeout", False, "claude timed out",
        timestamp="2026-07-15T12:00:00+00:00",
    )
    rows = _rows(csv_path)
    assert rows[0] == [
        "timestamp", "omeka_id", "num_pages", "category", "permanent", "detail",
    ]
    assert rows[1] == [
        "2026-07-15T12:00:00+00:00", "12345", "3", "timeout", "false",
        "claude timed out",
    ]


def test_log_failure_appends_without_repeating_header(tmp_path):
    csv_path = tmp_path / "failures.csv"
    transcribe.log_failure(
        csv_path, "1", 1, "no-images", False, "no images downloaded",
        timestamp="2026-07-15T12:00:00+00:00",
    )
    transcribe.log_failure(
        csv_path, "2", 5, "content-blocked", True, "Output blocked",
        timestamp="2026-07-15T12:01:00+00:00",
    )
    rows = _rows(csv_path)
    assert len(rows) == 3  # header + 2 data rows
    assert rows[0][0] == "timestamp"
    assert rows[1][1] == "1"
    assert rows[2][1] == "2"
    assert rows[2][4] == "true"  # permanent flag for content-blocked


def test_log_failure_escapes_commas_and_quotes_round_trip(tmp_path):
    csv_path = tmp_path / "failures.csv"
    nasty = 'API Error: 400 {"type":"error","message":"bad, image"}'
    transcribe.log_failure(
        csv_path, "999", 2, "image-unprocessable", True, nasty,
        timestamp="2026-07-15T12:02:00+00:00",
    )
    # csv.reader round-trips the escaped field back to the original string.
    rows = _rows(csv_path)
    assert rows[1][5] == nasty


def test_log_failure_collapses_newlines_and_truncates_detail(tmp_path):
    csv_path = tmp_path / "failures.csv"
    detail = "line one\nline two\n" + ("x" * 500)
    transcribe.log_failure(
        csv_path, "7", 1, "empty-or-error", False, detail,
        timestamp="2026-07-15T12:03:00+00:00",
    )
    logged = _rows(csv_path)[1][5]
    assert "\n" not in logged
    assert logged.startswith("line one line two")
    assert len(logged) <= 200


def test_log_failure_handles_none_detail(tmp_path):
    csv_path = tmp_path / "failures.csv"
    transcribe.log_failure(
        csv_path, "8", 4, "rate-limit-stop", False, None,
        timestamp="2026-07-15T12:04:00+00:00",
    )
    assert _rows(csv_path)[1][5] == ""


def test_log_failure_default_timestamp_is_iso_utc(tmp_path):
    csv_path = tmp_path / "failures.csv"
    transcribe.log_failure(csv_path, "9", 1, "timeout", False, "x")
    ts = _rows(csv_path)[1][0]
    # ISO-8601 with a UTC offset; parseable and timezone-aware.
    from datetime import datetime
    parsed = datetime.fromisoformat(ts)
    assert parsed.utcoffset() is not None


# ---------------------------------------------------------------------------
# transcribe_images surfaces a timed_out flag so the CSV can distinguish a
# timeout from a generic empty/error result.
# ---------------------------------------------------------------------------

def test_transcribe_images_timeout_sets_timed_out_flag(monkeypatch):
    import subprocess

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(transcribe.subprocess, "run", fake_run)
    outcome = transcribe.transcribe_images(["/tmp/a.jpg"])
    assert outcome["timed_out"] is True
    assert outcome["is_error"] is True


def test_transcribe_images_generic_failure_is_not_timed_out(monkeypatch):
    def fake_run(*args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(transcribe.subprocess, "run", fake_run)
    outcome = transcribe.transcribe_images(["/tmp/a.jpg"])
    assert outcome["timed_out"] is False
    assert outcome["is_error"] is True


# ---------------------------------------------------------------------------
# End-to-end: main() routes each failure to the CSV with the right category,
# num_pages, and permanent flag (claude call + downloads stubbed, no quota).
# ---------------------------------------------------------------------------

def _outcome(**over):
    base = {
        "text": None, "usage": {}, "cost_usd": 0.0, "is_error": False,
        "rate_limited": False, "image_error": False, "content_blocked": False,
        "timed_out": False,
    }
    base.update(over)
    return base


def test_main_writes_failure_rows_end_to_end(tmp_path, monkeypatch):
    # Tiny manifest: a 1-page doc that comes back empty, and a 2-page doc the
    # content filter blocks (permanent).
    manifest = tmp_path / "images.tsv"
    manifest.write_text("100\tfileA.jpg\n200\tfileB.jpg,fileC.jpg\n")

    failures = tmp_path / "failures.csv"
    monkeypatch.setattr(transcribe, "MANIFEST", manifest)
    monkeypatch.setattr(transcribe, "FAILURE_LOG", failures)
    monkeypatch.setattr(transcribe, "CACHE_FILE", tmp_path / ".progress")
    monkeypatch.setattr(transcribe, "OUTPUT_FILE", tmp_path / "out.json")
    monkeypatch.setattr(transcribe, "SKIP_FILE", tmp_path / "skip.txt")
    monkeypatch.setattr(transcribe, "USAGE_LOG", tmp_path / "usage.jsonl")

    # Downloads always "succeed"; claude call is forced per document.
    monkeypatch.setattr(transcribe, "download_all",
                        lambda files, d, base: list(files))
    outcomes = {
        ("fileA.jpg",): _outcome(is_error=True),                 # empty-or-error
        ("fileB.jpg", "fileC.jpg"): _outcome(content_blocked=True,
                                             text="Output blocked by policy"),
    }
    monkeypatch.setattr(transcribe, "transcribe_images",
                        lambda paths, model=None: outcomes[tuple(paths)])
    monkeypatch.setattr(transcribe.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["transcribe.py", "--delay", "0"])

    transcribe.main()

    rows = _rows(failures)
    assert rows[0] == transcribe.FAILURE_HEADER
    by_id = {r[1]: r for r in rows[1:]}
    assert by_id["100"][2:5] == ["1", "empty-or-error", "false"]
    assert by_id["200"][2:5] == ["2", "content-blocked", "true"]
    # Permanent failure is also recorded in skip_ids.txt; transient one is not.
    skip_ids = (tmp_path / "skip.txt").read_text().split()
    assert "200" in skip_ids and "100" not in skip_ids
