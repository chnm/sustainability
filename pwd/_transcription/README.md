# AI Transcription Pipeline (`_transcription/`)

Generates AI transcriptions of War Department document images using **`claude -p`**
(the Claude Code CLI in headless mode), which bills against your **Claude
subscription** rather than the pay-per-token API.

> There are **two** transcription implementations in this repo. This one
> (`_transcription/transcribe.py`, `claude -p`, subscription) is the **preferred**
> path. `scripts/transcribe.py` is an alternate that uses the Anthropic **SDK +
> API key** — same targeting flags, but real per-token cost. Use this one unless
> you specifically want API billing.

## Files

| File | Role |
|------|------|
| `build_image_list.py` | Builds `images.tsv` (one row: `omeka_id<TAB>img1.jpg,img2.jpg,…`) from each document's frontmatter `images:` list. |
| `transcribe.py` | Downloads each doc's images, runs `claude -p`, saves transcriptions, tracks usage. |
| `prompt.txt` | The paleographer/transcription system prompt. |
| `images.tsv` | Generated manifest (regenerable; gitignored but tracked). |
| `transcriptions.json` | Output: `{omeka_id: transcription_text}`. **Not** what Hugo reads — see Sync below. |
| `.transcribe_progress` | Resume cache: one completed `omeka_id` per line. |
| `usage_log.jsonl` | Per-document token/cost record (see Usage monitoring). |

## Prerequisites

- The `claude` CLI installed and **logged into the account** whose subscription
  should be billed (`claude` interactive once, or `claude setup-token`).
- Network access to `https://obj.rrchnm.org/wardepartmentpapers.org/files/original/`
  (images are downloaded per-doc to a temp dir, then deleted).
- `uv` (the script shebang is `uv run python3`), run from the `pwd/` directory.

## Running

```bash
cd pwd

# 1. Build the manifest from current frontmatter (do this after any change to
#    documents' images: lists — e.g. after scripts/fix_multipage_images.py).
python3 _transcription/build_image_list.py --content-dir content/document

# 2. Transcribe. Plain run transcribes every doc in the manifest not yet in the
#    resume cache:
python3 _transcription/transcribe.py --model claude-sonnet-4-6
```

Useful flags:

- `--ids-file PATH` — transcribe only the `omeka_id`s listed in `PATH` (one per
  line), **forcing** them even if already transcribed. Used to re-transcribe a
  targeted subset (see Resume).
- `--max-tokens N` — stop cleanly once cumulative tokens (input+output+cache)
  exceed `N`. Leave headroom against your weekly/session limit.
- `--max-pages N` — skip documents with more than `N` images (default `50`).
- `--limit N` — process at most `N` documents (smoke tests).
- `--no-resume` — ignore the progress cache and output (start fresh).
- `--model` — Claude model (default `claude-sonnet-4-6`).

## Resume (important)

Resume is tracked by `.transcribe_progress` (a set of completed `omeka_id`s).
Every successful doc is saved immediately, so an interrupted run loses only the
single in-flight document.

**Caveat with `--ids-file`:** it *forces* its targets and ignores the cache, so
re-running the same ids file re-transcribes already-done docs and wastes quota.
To resume a targeted run correctly, regenerate the "remaining" list first:

```python
# remaining = target ids − already-done
from pathlib import Path
d = Path("_transcription")
target = [l.strip() for l in open("multipage_grown_ids.txt") if l.strip()]
done = set((d/".transcribe_progress").read_text().split()) if (d/".transcribe_progress").exists() else set()
(d/"remaining_ids.txt").write_text("\n".join(x for x in target if x not in done) + "\n")
```
then `--ids-file _transcription/remaining_ids.txt`.

To pause: `pkill -f "transcribe.py --ids-file"` (only the in-flight doc is lost).

## Usage monitoring

Each `claude -p` call uses `--output-format json`, so the script tracks token
usage and a notional (API-equivalent) cost:

- A running tally prints after each doc.
- One line per doc is appended to `usage_log.jsonl` (`{omeka_id, …tokens…,
  total_tokens, cost_usd, cumulative_total_tokens, cumulative_cost_usd}`).
- `--max-tokens` stops the run when cumulative tokens cross the threshold.
- On a **subscription rate limit**, `claude -p` errors and the run **stops
  cleanly** (resume when your window resets).

`cost_usd` is notional — no real money is spent on a subscription run. There is
no CLI to read your remaining weekly/session allowance; check `/usage` in a
normal Claude Code session and set `--max-tokens` accordingly. The per-call
timeout scales with page count (`180 + 90×pages`, capped 30 min); a doc that
times out is skipped (not marked done, so a later pass retries it).

## Making results live on the site (manual sync)

Hugo reads **`data/transcriptions_ai.json`**, keyed by `omeka_id`. This pipeline
writes **`_transcription/transcriptions.json`**. After a run, merge the latter
into the former (the project's existing manual step) so the new transcriptions
appear on the site. Keep this in mind — a completed run does **not** update the
site by itself.

## Relationship to the multi-page image fix

Documents reference a shared microfilm reel; a document's `images:` list is a
slice of that reel (`page_start` + `num_pages`). `scripts/fix_multipage_images.py`
repairs documents that were missing pages. Always run `build_image_list.py`
**after** that fix so the manifest reflects the full page set, then
(re-)transcribe the affected docs. See
`docs/superpowers/specs/2026-07-06-multipage-images-design.md`.
