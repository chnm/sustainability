# Design: usage monitoring + guards for the claude -p transcription run

*Date: 2026-07-07 · Branch: `fix/pwd-multipage-images`*

## Problem

Running `_transcription/transcribe.py` over ~10k documents via `claude -p` consumes the operator's Claude **subscription** usage (rolling session + weekly windows). There is currently no visibility into how much a run consumes, and no guard to stop before exhausting the allowance. The subscription's remaining quota is **not** queryable from the CLI (v2.1.79 has no usage/limits subcommand), so we cannot read it directly — we can only measure this run's consumption and react to the server-side rate-limit signal.

## Approach

`claude -p --output-format json` returns per-call metadata: `result` (the text), `usage` (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`), `total_cost_usd`, and `is_error`/`subtype`/`result`. We switch the transcription call to JSON, accumulate usage across the run, log it, and add guards.

Note: on a subscription, `total_cost_usd` is a **notional** API-equivalent figure (no real money moves). We track it for information only; the enforced guard is token-based.

## Behavior

Per document (in `transcribe_images` / the run loop):
1. Invoke `claude -p <prompt> --model <model> --allowedTools Read --output-format json`.
2. Parse the JSON result into `{text, is_error, rate_limited, usage{...}, cost_usd}`.
3. If the call is a **rate-limit** error → **stop the whole run cleanly** (progress already saved per-doc; resumable). Print a clear message.
4. If the call is a **non-rate-limit** error (or unparseable output) → skip that document and continue (current resilience preserved).
5. On success → save the transcription (unchanged output format), accumulate usage, append one line to the usage log, print a running tally.

Guards / config (new CLI flags):
- `--max-tokens N` — stop the run cleanly once cumulative counted tokens exceed `N`. Counted tokens = `input + output + cache_creation + cache_read` (conservative — stops earlier rather than later). Default: unlimited.

Rate-limit handling: **always stop** on the first detected rate-limit (no wait/retry). The run is resumable, so the operator restarts when their window resets.

Outputs:
- `_transcription/usage_log.jsonl` — one JSON line per transcribed doc: `{omeka_id, input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens, total_tokens, cost_usd, cumulative_total_tokens, cumulative_cost_usd}`. Append-mode, survives across resumed runs.
- A running tally line printed after each doc: cumulative tokens + notional cost + doc count.
- `transcriptions.json` output format is **unchanged** (usage lives only in the log), so the operator's manual sync to `data/transcriptions_ai.json` is unaffected.

## Testable units (pure functions)

- `parse_claude_json(stdout: str) -> dict` — returns `{text, is_error, rate_limited, usage, cost_usd}`. Handles: success payload; error payload; rate-limit payload; unparseable/empty stdout (→ `is_error=True`, `text=None`, zero usage).
- `is_rate_limit(stdout: str, stderr: str, returncode: int) -> bool` — best-effort, case-insensitive detection of rate/usage-limit indicators (e.g. "rate limit", "usage limit", "429", "resets at", "limit reached"). Conservative: only true on clear indicators, so ordinary per-doc errors are NOT treated as rate limits.
- `accumulate_usage(totals: dict, usage: dict) -> dict` — add one call's usage into running totals (per-category + `total_tokens`).
- `tokens_exceeded(totals: dict, max_tokens: int | None) -> bool` — `False` when `max_tokens` is `None`; else `total_tokens > max_tokens`.

The subprocess/network/`claude -p` invocation itself is not unit-tested (as with the existing script); only the pure parsing/accounting logic is.

## Non-goals

- Reading the subscription's remaining session/weekly allowance (not exposed by the CLI).
- Wait-and-retry on rate limit (explicitly chosen: always stop).
- Dollar or doc-count caps (only `--max-tokens`).
- Changing the `transcriptions.json` schema or the `--ids-file` targeting behavior.
