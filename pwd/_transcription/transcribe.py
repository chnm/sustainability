#!/usr/bin/env -S uv run python3
"""
Transcribe War Department document images using `claude -p`.

Downloads each document's images from object storage, passes them to
`claude -p` with the transcription prompt, saves the result, then
deletes the local image copies. Tracks progress in a cache file so
runs can be interrupted and resumed.

Usage:
    # First, build the image manifest (from project root):
    python3 _transcription/build_image_list.py --content-dir content/document

    # Transcribe all documents (resumes automatically):
    python3 _transcription/transcribe.py

    # Limit to N documents:
    python3 _transcription/transcribe.py --limit 10

    # Start fresh (ignore cache):
    python3 _transcription/transcribe.py --no-resume

    # Use a different model:
    python3 _transcription/transcribe.py --model claude-sonnet-4-6
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request


SCRIPT_DIR = Path(__file__).parent
MANIFEST = SCRIPT_DIR / "images.tsv"
PROMPT_FILE = SCRIPT_DIR / "prompt.txt"
CACHE_FILE = SCRIPT_DIR / ".transcribe_progress"
SKIP_FILE = SCRIPT_DIR / "skip_ids.txt"  # docs that permanently fail (content-blocked, etc.)
OUTPUT_FILE = SCRIPT_DIR / "transcriptions.json"
USAGE_LOG = SCRIPT_DIR / "usage_log.jsonl"
FAILURE_LOG = SCRIPT_DIR / "failures.csv"  # structured record of every non-success

FAILURE_HEADER = ["timestamp", "omeka_id", "num_pages", "category", "permanent", "detail"]
DETAIL_MAX = 200

MEDIA_BASE_ORIGINAL = "https://obj.rrchnm.org/wardepartmentpapers.org/files/original"
MEDIA_BASE_LARGE = "https://obj.rrchnm.org/wardepartmentpapers.org/files/large"

RATE_LIMIT_INDICATORS = (
    "rate limit",
    "rate_limit",
    "usage limit",
    "usage_limit",
    "429",
    "resets at",
    "limit reached",
    "usage limit reached",
)


def load_cache():
    """Load set of already-transcribed omeka_ids."""
    if CACHE_FILE.exists():
        return set(CACHE_FILE.read_text().strip().splitlines())
    return set()


def append_cache(omeka_id):
    """Mark a document as done in the cache."""
    with open(CACHE_FILE, "a") as f:
        f.write(f"{omeka_id}\n")


def load_skip():
    """Load set of omeka_ids that permanently fail (skip on future runs)."""
    if SKIP_FILE.exists():
        return set(SKIP_FILE.read_text().strip().splitlines())
    return set()


def append_skip(omeka_id):
    """Record a permanently-failing document so we stop re-attempting it."""
    with open(SKIP_FILE, "a") as f:
        f.write(f"{omeka_id}\n")


def log_failure(csv_path, omeka_id, num_pages, category, permanent, detail,
                timestamp=None):
    """Append one row to the failure CSV, writing the header if the file is new.

    Records every document that did NOT produce a transcription so we know what
    to come back to. `permanent` marks the ids also added to skip_ids.txt
    (never retried); transient failures log here but are still retried next run.

    `detail` is newline-collapsed and truncated to DETAIL_MAX chars; csv.writer
    handles quoting of commas/quotes. `timestamp` defaults to the current UTC
    time in ISO-8601 (injectable for tests).
    """
    csv_path = Path(csv_path)
    is_new = not csv_path.exists()
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    detail = " ".join((detail or "").split())[:DETAIL_MAX]
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(FAILURE_HEADER)
        writer.writerow([
            timestamp, omeka_id, num_pages, category,
            "true" if permanent else "false", detail,
        ])


def load_output():
    """Load existing transcriptions JSON."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {}


def save_output(transcriptions):
    """Save transcriptions JSON."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(transcriptions, f, indent=2, ensure_ascii=False)


def download_image(filename, dest_dir, base_url=MEDIA_BASE_ORIGINAL):
    """Download an image from object storage. Returns local path."""
    url = f"{base_url}/{filename}"
    local_path = os.path.join(dest_dir, filename)
    req = Request(url, headers={"User-Agent": "PWD-Transcribe/1.0"})
    try:
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path
    except Exception as e:
        print(f"    Error downloading {filename}: {e}")
        return None


def download_all(image_files, dest_dir, base_url):
    """Download every image for a document. Returns the list of local paths."""
    paths = []
    for filename in image_files:
        print(f"    Downloading {filename[:16]}...")
        path = download_image(filename, dest_dir, base_url)
        if path:
            paths.append(path)
    return paths


def is_image_error(stdout):
    """True if claude -p reported the API could not process an image (400)."""
    return "could not process image" in (stdout or "").lower()


def is_content_blocked(stdout):
    """True if the API blocked the transcription output via content filtering."""
    low = (stdout or "").lower()
    return "content filtering policy" in low or "output blocked" in low


def _zero_usage():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def parse_claude_json(stdout):
    """Parse `claude -p --output-format json` stdout into a structured result.

    Returns {text, is_error, usage, cost_usd}. On unparseable/empty stdout,
    returns is_error=True, text=None, zero usage, cost_usd=0.0.
    """
    if not stdout or not stdout.strip():
        return {
            "text": None,
            "is_error": True,
            "usage": _zero_usage(),
            "cost_usd": 0.0,
        }

    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return {
            "text": None,
            "is_error": True,
            "usage": _zero_usage(),
            "cost_usd": 0.0,
        }

    raw_usage = payload.get("usage") or {}
    usage = _zero_usage()
    for key in usage:
        usage[key] = raw_usage.get(key, 0)

    return {
        "text": payload.get("result"),
        "is_error": bool(payload.get("is_error", False)),
        "usage": usage,
        "cost_usd": float(payload.get("total_cost_usd", 0.0) or 0.0),
    }


def is_rate_limit(stdout, stderr, returncode, is_error=False):
    """Best-effort, conservative detection of a subscription rate/usage-limit error.

    Only returns True on clear indicators, so ordinary per-doc failures are not
    mistaken for rate limits. This is the single authoritative rate-limit check.

    A successful call (returncode 0 and is_error False) is never a rate limit,
    so a clean transcription's text is never scanned for these indicators.
    """
    # A successful call is never a rate limit — never scan a good transcription's text.
    if returncode == 0 and not is_error:
        return False
    haystack = f"{stdout or ''}\n{stderr or ''}".lower()
    return any(indicator in haystack for indicator in RATE_LIMIT_INDICATORS)


def accumulate_usage(totals, usage):
    """Add one call's usage into running totals. Returns an updated dict."""
    updated = {
        "input_tokens": totals.get("input_tokens", 0) + usage.get("input_tokens", 0),
        "output_tokens": totals.get("output_tokens", 0) + usage.get("output_tokens", 0),
        "cache_creation_input_tokens": (
            totals.get("cache_creation_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
        ),
        "cache_read_input_tokens": (
            totals.get("cache_read_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
        ),
    }
    updated["total_tokens"] = (
        updated["input_tokens"]
        + updated["output_tokens"]
        + updated["cache_creation_input_tokens"]
        + updated["cache_read_input_tokens"]
    )
    return updated


def tokens_exceeded(totals, max_tokens):
    """True if cumulative counted tokens exceed max_tokens. False when max_tokens is None."""
    if max_tokens is None:
        return False
    return totals["total_tokens"] > max_tokens


def call_timeout(num_pages, base=180, per_page=90, cap=1800):
    """Seconds to allow one `claude -p` call, scaled by page count (clamped to cap)."""
    return min(cap, base + per_page * max(1, num_pages))


def transcribe_images(image_paths, model="claude-sonnet-4-6"):
    """Run `claude -p` with the prompt and image files.

    Returns {text, usage, cost_usd, is_error, rate_limited}. A timeout or
    subprocess failure is treated as a per-document error (skip), never a crash.
    """
    prompt = PROMPT_FILE.read_text() + "\n\nPlease read and transcribe the following image files:\n"
    for path in image_paths:
        prompt += f"- {path}\n"

    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--allowedTools", "Read",
        "--output-format", "json",
    ]

    zero_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    timeout_s = call_timeout(len(image_paths))
    try:
        # Redirect stdin from /dev/null: newer `claude` CLI waits on stdin and
        # fails ("no stdin data received in 3s") when it inherits a pipe/tty.
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        print(f"    claude timed out after {timeout_s}s — skipping this document")
        return {"text": None, "usage": zero_usage, "cost_usd": 0.0,
                "is_error": True, "rate_limited": False,
                "image_error": False, "content_blocked": False,
                "timed_out": True}
    except Exception as e:
        print(f"    claude call failed: {e} — skipping this document")
        return {"text": None, "usage": zero_usage, "cost_usd": 0.0,
                "is_error": True, "rate_limited": False,
                "image_error": False, "content_blocked": False,
                "timed_out": False}

    if result.returncode != 0:
        print(f"    claude error (exit {result.returncode}): {result.stderr[:200]}")

    parsed = parse_claude_json(result.stdout)
    rate_limited = is_rate_limit(
        result.stdout, result.stderr, result.returncode, is_error=parsed["is_error"]
    )

    return {
        "text": parsed["text"],
        "usage": parsed["usage"],
        "cost_usd": parsed["cost_usd"],
        "is_error": parsed["is_error"],
        "rate_limited": rate_limited,
        "image_error": is_image_error(result.stdout),
        "content_blocked": is_content_blocked(result.stdout),
        "timed_out": False,
    }


def load_manifest():
    """Read the image manifest TSV. Returns list of (omeka_id, [filenames])."""
    if not MANIFEST.exists():
        print(f"Error: manifest not found at {MANIFEST}")
        print("Run build_image_list.py first.")
        sys.exit(1)

    entries = []
    with open(MANIFEST) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            omeka_id, images_str = line.split("\t", 1)
            images = images_str.split(",")
            entries.append((omeka_id, images))
    return entries


def load_ids_file(path):
    """Load a set of omeka_ids from a file (one per line, blanks ignored)."""
    text = Path(path).read_text()
    return {line.strip() for line in text.splitlines() if line.strip()}


def select_todo(manifest, done, max_pages, ids_filter=None, skip=None):
    """Select the (omeka_id, [images]) documents to transcribe.

    manifest: list of (omeka_id, [images]).

    When ids_filter is a set: select exactly those ids present in the manifest,
    forcing re-transcription (ignore `done`), still respecting max_pages. Ids in
    ids_filter but not in the manifest are simply absent from the result.

    When ids_filter is None: skip ids already in `done`, respect max_pages.

    `skip` is a set of omeka_ids known to permanently fail (content-blocked,
    etc.); they are always excluded, even in forced ids_filter mode.

    Manifest order is preserved.
    """
    skip = skip or set()
    todo = []
    for oid, imgs in manifest:
        if len(imgs) > max_pages:
            continue
        if oid in skip:
            continue
        if ids_filter is not None:
            if oid in ids_filter:
                todo.append((oid, imgs))
        elif oid not in done:
            todo.append((oid, imgs))
    return todo


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe War Department documents via claude -p"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max documents to transcribe",
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Start fresh, ignoring the progress cache",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6",
        help="Claude model (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=50,
        help="Max pages per document (default: 50)",
    )
    parser.add_argument(
        "--ids-file", default=None,
        help="Re-transcribe only these omeka_ids (one per line), forcing "
             "re-transcription even if already done.",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="Stop the run once cumulative tokens exceed N (counts input+output+cache).",
    )
    parser.add_argument(
        "--rate-backoff", type=int, default=60,
        help="Seconds to wait before retrying after a rate-limit hit (default 60).",
    )
    parser.add_argument(
        "--max-rate-retries", type=int, default=3,
        help="Rate-limit retries per doc before giving up and stopping (default 3).",
    )
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Seconds to pause between documents to avoid burst limits (default 2).",
    )
    args = parser.parse_args()

    manifest = load_manifest()

    ids_filter = load_ids_file(args.ids_file) if args.ids_file else None

    # In ids-file (forced) mode, always preserve existing transcriptions so
    # untargeted entries survive and only the targeted ids get overwritten.
    if ids_filter is not None:
        done = load_cache()
        transcriptions = load_output()
    else:
        done = set() if args.no_resume else load_cache()
        transcriptions = {} if args.no_resume else load_output()

    skip = load_skip()
    todo = select_todo(manifest, done, args.max_pages, ids_filter=ids_filter, skip=skip)
    if args.limit:
        todo = todo[:args.limit]

    skipped_big = len([oid for oid, imgs in manifest if len(imgs) > args.max_pages])
    print(f"Manifest: {len(manifest)} documents")
    if ids_filter is not None:
        manifest_ids = {oid for oid, _ in manifest}
        found = ids_filter & manifest_ids
        missing = ids_filter - manifest_ids
        print(f"Mode: targeted re-transcription via --ids-file ({args.ids_file})")
        print(f"IDs requested: {len(ids_filter)}")
        print(f"IDs found in manifest: {len(found)}")
        if missing:
            print(f"IDs listed but NOT in manifest: {len(missing)}")
        print(f"Skipped (>{args.max_pages} pages): "
              f"{len(found) - len(todo) if args.limit is None else 'n/a (limited)'}")
    else:
        skipped_done = len([oid for oid, _ in manifest if oid in done])
        print(f"Already done: {skipped_done}")
        print(f"Skipped (>{args.max_pages} pages): {skipped_big}")
    print(f"To transcribe: {len(todo)}")
    print(f"Model: {args.model}")
    print()

    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_tokens": 0,
    }
    cost_total = 0.0

    for i, (omeka_id, image_files) in enumerate(todo):
        image_files = image_files[:args.max_pages]
        print(f"[{i + 1}/{len(todo)}] Document {omeka_id} ({len(image_files)} page(s))")

        # Pace between documents to avoid tripping short-term burst limits.
        if i > 0 and args.delay:
            time.sleep(args.delay)

        # Download images to a temp directory
        with tempfile.TemporaryDirectory(prefix="pwd_transcribe_") as tmpdir:
            orig_dir = os.path.join(tmpdir, "original")
            os.makedirs(orig_dir, exist_ok=True)
            local_paths = download_all(image_files, orig_dir, MEDIA_BASE_ORIGINAL)

            if not local_paths:
                print(f"    No images downloaded, skipping")
                log_failure(FAILURE_LOG, omeka_id, len(image_files),
                            "no-images", False, "no images downloaded")
                continue

            # Transcribe, with a one-time /files/large image fallback and
            # rate-limit backoff-retry (rate limits are usually short-term
            # throttling, so we retry the doc rather than halt the whole run).
            large_paths = None
            rl_retries = 0
            while True:
                paths = large_paths if large_paths else local_paths
                print(f"    Transcribing with claude -p...")
                start = time.time()
                outcome = transcribe_images(paths, model=args.model)

                # Original scans the API can't process → retry once with /large.
                if outcome["image_error"] and large_paths is None:
                    print("    Original images rejected; retrying with /files/large...")
                    large_dir = os.path.join(tmpdir, "large")
                    os.makedirs(large_dir, exist_ok=True)
                    dl = download_all(image_files, large_dir, MEDIA_BASE_LARGE)
                    if dl:
                        large_paths = dl
                        continue
                    break  # nothing to fall back to

                # Rate limited → back off and retry the same document.
                if outcome["rate_limited"] and rl_retries < args.max_rate_retries:
                    rl_retries += 1
                    print(f"    Rate limited (retry {rl_retries}/{args.max_rate_retries}): "
                          f"{(outcome['text'] or '')[:200]}")
                    print(f"    Backing off {args.rate_backoff}s...")
                    time.sleep(args.rate_backoff)
                    continue

                break

            elapsed = time.time() - start
            text = outcome["text"]

            if outcome["rate_limited"]:
                print(f"    Still rate limited after {args.max_rate_retries} retries; "
                      f"stopping (resumable). Detail: {(outcome['text'] or '')[:200]}")
                log_failure(FAILURE_LOG, omeka_id, len(image_files),
                            "rate-limit-stop", False, outcome["text"])
                break

            # Permanent failures: content filtering, or images the API rejects
            # even at /files/large. Record so future runs don't re-attempt them.
            if outcome["content_blocked"] or outcome["image_error"]:
                reason = "content-blocked" if outcome["content_blocked"] else "image-unprocessable"
                print(f"    Permanent failure ({reason}); adding to skip-list")
                append_skip(omeka_id)
                log_failure(FAILURE_LOG, omeka_id, len(image_files),
                            reason, True, outcome["text"])
                continue

            if not text or outcome["is_error"]:
                print(f"    No transcription returned")
                category = "timeout" if outcome.get("timed_out") else "empty-or-error"
                log_failure(FAILURE_LOG, omeka_id, len(image_files),
                            category, False, outcome["text"])
                continue

            transcriptions[omeka_id] = text
            save_output(transcriptions)
            append_cache(omeka_id)
            print(f"    Done ({len(text)} chars, {elapsed:.1f}s)")

            totals = accumulate_usage(totals, outcome["usage"])
            cost_total += outcome["cost_usd"]
            with open(USAGE_LOG, "a") as f:
                f.write(json.dumps({
                    "omeka_id": omeka_id,
                    "input_tokens": outcome["usage"]["input_tokens"],
                    "output_tokens": outcome["usage"]["output_tokens"],
                    "cache_creation_input_tokens": outcome["usage"]["cache_creation_input_tokens"],
                    "cache_read_input_tokens": outcome["usage"]["cache_read_input_tokens"],
                    "total_tokens": (
                        outcome["usage"]["input_tokens"]
                        + outcome["usage"]["output_tokens"]
                        + outcome["usage"]["cache_creation_input_tokens"]
                        + outcome["usage"]["cache_read_input_tokens"]
                    ),
                    "cost_usd": outcome["cost_usd"],
                    "cumulative_total_tokens": totals["total_tokens"],
                    "cumulative_cost_usd": cost_total,
                }) + "\n")
            print(f"    Usage: {totals['total_tokens']} cumulative tokens, "
                  f"${cost_total:.4f} notional cost, {i + 1} doc(s) done")

            # tempdir cleanup is automatic — images are deleted here

            if tokens_exceeded(totals, args.max_tokens):
                print(f"    Cumulative tokens ({totals['total_tokens']}) exceeded "
                      f"--max-tokens ({args.max_tokens}); stopping. Run is resumable.")
                break

    print(f"\nFinished. {len(transcriptions)} transcriptions in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
