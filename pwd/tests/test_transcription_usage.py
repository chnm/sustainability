import importlib.util
import json
import sys
from pathlib import Path

_TRANSCRIPTION_DIR = Path(__file__).resolve().parent.parent / "_transcription"
sys.path.insert(0, str(_TRANSCRIPTION_DIR))

# Load _transcription/transcribe.py under a distinct module name so it does not
# collide with scripts/transcribe.py (a superseded SDK script that
# test_transcribe_selection.py imports as `transcribe`).
_spec = importlib.util.spec_from_file_location(
    "transcribe_claude_p_usage", _TRANSCRIPTION_DIR / "transcribe.py"
)
transcribe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transcribe)


ZERO_USAGE = {
    "input_tokens": 0,
    "output_tokens": 0,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
}


# ---------------------------------------------------------------------------
# parse_claude_json
# ---------------------------------------------------------------------------

def test_parse_claude_json_success_payload():
    payload = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": "This is the transcribed text.",
        "total_cost_usd": 0.1234,
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_creation_input_tokens": 10,
            "cache_read_input_tokens": 5,
        },
    }
    stdout = json.dumps(payload)
    result = transcribe.parse_claude_json(stdout)
    assert result["text"] == "This is the transcribed text."
    assert result["is_error"] is False
    assert result["usage"] == {
        "input_tokens": 100,
        "output_tokens": 50,
        "cache_creation_input_tokens": 10,
        "cache_read_input_tokens": 5,
    }
    assert result["cost_usd"] == 0.1234


def test_parse_claude_json_success_payload_missing_usage_keys_default_zero():
    payload = {
        "is_error": False,
        "result": "text",
        "total_cost_usd": 0.01,
        "usage": {"input_tokens": 42},
    }
    result = transcribe.parse_claude_json(json.dumps(payload))
    assert result["usage"] == {
        "input_tokens": 42,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def test_parse_claude_json_error_payload():
    payload = {
        "is_error": True,
        "result": "",
        "total_cost_usd": 0.0,
        "usage": {},
    }
    result = transcribe.parse_claude_json(json.dumps(payload))
    assert result["is_error"] is True


def test_parse_claude_json_unparseable_string():
    result = transcribe.parse_claude_json("not json at all {{{")
    assert result == {
        "text": None,
        "is_error": True,
        "usage": ZERO_USAGE,
        "cost_usd": 0.0,
    }


def test_parse_claude_json_empty_string():
    result = transcribe.parse_claude_json("")
    assert result == {
        "text": None,
        "is_error": True,
        "usage": ZERO_USAGE,
        "cost_usd": 0.0,
    }


# ---------------------------------------------------------------------------
# is_rate_limit
# ---------------------------------------------------------------------------

def test_is_rate_limit_detects_rate_limit_phrase():
    assert transcribe.is_rate_limit("Error: rate limit exceeded", "", 1) is True


def test_is_rate_limit_detects_rate_limit_underscore():
    assert transcribe.is_rate_limit("", "rate_limit_error occurred", 1) is True


def test_is_rate_limit_detects_usage_limit_phrase():
    assert transcribe.is_rate_limit("You have hit your usage limit", "", 1) is True


def test_is_rate_limit_detects_usage_limit_reached():
    assert transcribe.is_rate_limit("", "Usage limit reached for this account", 1) is True


def test_is_rate_limit_detects_429():
    assert transcribe.is_rate_limit("HTTP 429 Too Many Requests", "", 1) is True


def test_is_rate_limit_detects_resets_at():
    assert transcribe.is_rate_limit("", "Limit resets at 5:00pm", 1) is True


def test_is_rate_limit_detects_limit_reached():
    assert transcribe.is_rate_limit("Limit reached, try again later", "", 1) is True


def test_is_rate_limit_case_insensitive():
    assert transcribe.is_rate_limit("RATE LIMIT EXCEEDED", "", 1) is True


def test_is_rate_limit_false_for_ordinary_error():
    assert transcribe.is_rate_limit(
        "", "Error: could not read image file, no such file", 1
    ) is False


def test_is_rate_limit_false_for_success_string():
    payload = json.dumps({"is_error": False, "result": "some transcribed text"})
    assert transcribe.is_rate_limit(payload, "", 0) is False


def test_is_rate_limit_false_for_empty_strings():
    assert transcribe.is_rate_limit("", "", 0) is False


def test_is_rate_limit_false_for_successful_transcription_mentioning_429():
    # Regression: a successful transcription of an 18th-century document can
    # legitimately contain text like "...forwarded 429 stand of arms..." or
    # "the limit reached the fort by dusk". A clean success (returncode 0,
    # is_error False) must never be treated as a rate limit, no matter what
    # the transcribed text says.
    payload = json.dumps({
        "is_error": False,
        "result": "...forwarded 429 stand of arms before the limit reached the fort...",
    })
    assert transcribe.is_rate_limit(payload, "", 0, is_error=False) is False


def test_is_rate_limit_true_for_failed_call_with_rate_limit_message():
    assert transcribe.is_rate_limit(
        "", "Error: usage limit reached for this account", 1, is_error=False
    ) is True


def test_is_rate_limit_true_for_is_error_true_payload_with_zero_returncode():
    # Some failures surface as a zero exit code but is_error true in the
    # parsed JSON payload; a rate-limit indicator there must still count.
    payload = json.dumps({
        "is_error": True,
        "result": "Usage limit reached, please try again later.",
    })
    assert transcribe.is_rate_limit(payload, "", 0, is_error=True) is True


def test_is_rate_limit_false_for_failed_call_with_generic_error():
    assert transcribe.is_rate_limit(
        "", "Error: could not read image file, no such file", 1, is_error=False
    ) is False


# ---------------------------------------------------------------------------
# accumulate_usage
# ---------------------------------------------------------------------------

def test_accumulate_usage_sums_categories_and_total():
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_tokens": 0,
    }
    usage1 = {
        "input_tokens": 100,
        "output_tokens": 50,
        "cache_creation_input_tokens": 10,
        "cache_read_input_tokens": 5,
    }
    usage2 = {
        "input_tokens": 20,
        "output_tokens": 30,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 15,
    }
    totals = transcribe.accumulate_usage(totals, usage1)
    totals = transcribe.accumulate_usage(totals, usage2)

    assert totals["input_tokens"] == 120
    assert totals["output_tokens"] == 80
    assert totals["cache_creation_input_tokens"] == 10
    assert totals["cache_read_input_tokens"] == 20
    assert totals["total_tokens"] == 120 + 80 + 10 + 20


def test_accumulate_usage_does_not_mutate_input_totals_by_reference_issue():
    totals = {
        "input_tokens": 5,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_tokens": 5,
    }
    usage = {
        "input_tokens": 1,
        "output_tokens": 1,
        "cache_creation_input_tokens": 1,
        "cache_read_input_tokens": 1,
    }
    new_totals = transcribe.accumulate_usage(totals, usage)
    assert new_totals["input_tokens"] == 6
    assert new_totals["total_tokens"] == 9


# ---------------------------------------------------------------------------
# tokens_exceeded
# ---------------------------------------------------------------------------

def test_tokens_exceeded_none_max_is_false():
    totals = {"total_tokens": 999999}
    assert transcribe.tokens_exceeded(totals, None) is False


def test_tokens_exceeded_below_threshold_is_false():
    totals = {"total_tokens": 100}
    assert transcribe.tokens_exceeded(totals, 200) is False


def test_tokens_exceeded_above_threshold_is_true():
    totals = {"total_tokens": 300}
    assert transcribe.tokens_exceeded(totals, 200) is True


def test_tokens_exceeded_equal_threshold_is_false():
    totals = {"total_tokens": 200}
    assert transcribe.tokens_exceeded(totals, 200) is False


# ---------------------------------------------------------------------------
# call_timeout
# ---------------------------------------------------------------------------

def test_call_timeout_scales_with_pages():
    assert transcribe.call_timeout(1) < transcribe.call_timeout(7)
    # a 7-page doc (the one that crashed at the old flat 300s) now gets far longer
    assert transcribe.call_timeout(7) == 180 + 90 * 7
    assert transcribe.call_timeout(7) > 300


def test_call_timeout_floor_and_cap():
    # zero/negative page counts still get at least the one-page allowance
    assert transcribe.call_timeout(0) == transcribe.call_timeout(1)
    # very large docs are clamped to the cap
    assert transcribe.call_timeout(10_000) == 1800


# ---------------------------------------------------------------------------
# is_image_error (triggers the /files/large fallback)
# ---------------------------------------------------------------------------

def test_is_image_error_detects_could_not_process():
    stdout = json.dumps({"is_error": True, "result":
        'API Error: 400 {"type":"error","error":{"type":"invalid_request_error",'
        '"message":"Could not process image"}}'})
    assert transcribe.is_image_error(stdout) is True


def test_is_image_error_false_on_success_and_empty():
    ok = json.dumps({"is_error": False, "result": "A clean transcription with no errors."})
    assert transcribe.is_image_error(ok) is False
    assert transcribe.is_image_error("") is False
    assert transcribe.is_image_error(None) is False


def test_is_content_blocked_detects_policy_block():
    stdout = json.dumps({"is_error": True, "result":
        'API Error: 400 {"type":"error","error":{"type":"invalid_request_error",'
        '"message":"Output blocked by content filtering policy"}}'})
    assert transcribe.is_content_blocked(stdout) is True


def test_is_content_blocked_false_on_success_and_empty():
    ok = json.dumps({"is_error": False, "result": "A clean transcription."})
    assert transcribe.is_content_blocked(ok) is False
    assert transcribe.is_content_blocked("") is False
    assert transcribe.is_content_blocked(None) is False
