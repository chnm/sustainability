# PWD Multi-Page Images + AI Transcription — Handoff / Roadmap

*Last updated: 2026-07-15. Branch: `fix/pwd-multipage-images` (PR [#65](https://github.com/chnm/sustainability/pull/65), open). This supersedes `HANDOFF-num-pages-bug.md` (safe to delete).*

## TL;DR status

- **Part 1 — multi-page image fix: DONE & committed.** 23,357 documents had their `images:` / `num_pages` frontmatter rebuilt (10,163 gained pages).
- **Part 2 — AI re-transcription: IN PROGRESS.** ~**3,287 / 10,163 (32.3%)** of the grown docs transcribed via `claude -p`. Resumable; everything is saved after each doc.
- All tooling committed to PR #65 (27 commits, 63 passing tests).

---

## Part 1 — multi-page image fix (complete)

Documents reference a shared microfilm **reel** via `omeka_image_id`; `data/media_map.json` maps a reel to its ordered files. A document's `images:` list is a slice `reel_files[page_start-1 : page_start-1+num_pages]`. Missing `num_pages` truncated multi-page docs to one image.

`scripts/fix_multipage_images.py` fixes this **locally** (no API): single-doc / small reels (≤5 imgs) get the whole reel; large shared reels are sliced by neighbor `page_start`. Already applied. Design: `docs/superpowers/specs/2026-07-06-multipage-images-design.md`. The list of docs that grew is `multipage_grown_ids.txt` (10,163 ids).

---

## Part 2 — AI transcription (in progress)

Uses the **`claude -p`** pipeline in `_transcription/` (billed to the Claude **subscription**, not API). Full runbook: `_transcription/README.md`.

### Resume the run (do this to continue)

```bash
cd pwd

# 1. Rebuild the manifest from current frontmatter (safe to re-run):
python3 _transcription/build_image_list.py --content-dir content/document

# 2. Regenerate the "remaining" list = grown − done − skip-listed:
python3 - <<'PY'
from pathlib import Path
d=Path("_transcription")
grown=[l.strip() for l in open("multipage_grown_ids.txt") if l.strip()]
done=set((d/".transcribe_progress").read_text().split()) if (d/".transcribe_progress").exists() else set()
skip=set((d/"skip_ids.txt").read_text().split()) if (d/"skip_ids.txt").exists() else set()
rem=[g for g in grown if g not in done and g not in skip]
(d/"remaining_ids.txt").write_text("\n".join(rem)+"\n")
print("remaining:", len(rem))
PY

# 3. Launch (tracked bg job wrapped in caffeinate: system awake, screen can sleep):
caffeinate -i -m -s python3 "$PWD/_transcription/transcribe.py" \
  --ids-file "$PWD/_transcription/remaining_ids.txt" --model claude-sonnet-4-6
```

- **Monitor** via the per-doc files (console output is buffered): `.transcribe_progress` (count), `usage_log.jsonl` (tokens/cost), `transcriptions.json` (output).
- **Pause**: `pkill -f "transcribe.py --ids-file"` — only the in-flight doc is lost.
- Launch as a **tracked background job** (not detached `os.setsid`, which was flaky here).

### Making results live on the site (MANUAL — required)

Hugo reads `data/transcriptions_ai.json`. The pipeline writes `_transcription/transcriptions.json`. After a run, **merge the latter into the former** (the project's existing manual sync step — ask the site owner where it is). A completed run does NOT update the site by itself.

---

## Failure modes — all handled (learned the hard way)

| Symptom | Cause | Handling |
|---|---|---|
| Every call exits 1, "no stdin data received" | Newer `claude` CLI waits on stdin | `stdin=subprocess.DEVNULL` (fixed) |
| `400 "Could not process image"` | Some `/files/original` scans have an encoding the API rejects (not size) | Per-doc fallback to smaller `/files/large` (fixed) |
| `400 "Output blocked by content filtering policy"` | Period War-Dept content trips the output filter | Recorded in `skip_ids.txt`, excluded from future runs |
| Doc times out / fails around ~34+ pages | Read-turn / output-token limits on huge docs | `--max-pages 50` skips the 51 docs >50 pages; largest single doc is 137pp |
| "Hit rate limit" but `/usage` shows headroom | **Short-term burst throttle (429)**, not exhausted quota | **Backs off (`--rate-backoff` 60s) and retries (`--max-rate-retries` 3)**, paces docs (`--delay`), logs the real message; only stops if still limited after retries |

**Subscription limits:** two windows — a **~5-hour rolling session limit** AND the **weekly limit** — plus short-term **burst (429)** throttling. `/usage` shows the session + weekly percentages and reset times. Bursty transcription can trip the 429 even with both windows far from full; that's what the backoff-retry now rides through.

---

## Open items / roadmap

1. **Finish the ~6,800 remaining docs** — just keep resuming (above). With backoff-retry it should push much further per run now.
2. **The 51 big docs (>50 pages, up to 137pp)** — currently skipped. Later, do a dedicated pass: test one with a raised `--max-pages` + long timeout to find where it breaks (turns/output), bump the cap to what works, and **chunk only the genuine stragglers** (~20-page batches, concatenate in order — they're single-doc reels so page-boundary chunking is clean).
3. **Quantify content-filtering** — how many docs land in `skip_ids.txt` when the run completes. If it's a large share, decide policy (accept gaps where human transcription already stands, or try a different tack). Currently only 2 confirmed.
4. **The manual `_transcription/transcriptions.json` → `data/transcriptions_ai.json` sync** — needs to run before the site shows new transcriptions. Locate/automate it.
5. **Merge PR #65** once transcription is far enough along (Part 1 is independently shippable now).

---

## Key files

- `scripts/fix_multipage_images.py` — the image fix (Part 1).
- `_transcription/transcribe.py` — the `claude -p` pipeline (Part 2); `README.md` next to it.
- `_transcription/build_image_list.py` — builds `images.tsv` manifest from frontmatter.
- `multipage_grown_ids.txt` — the 10,163 re-transcription targets.
- `_transcription/{.transcribe_progress, skip_ids.txt, usage_log.jsonl, remaining_ids.txt, failures.csv}` — run state (gitignored). `failures.csv` is the structured "what to come back to" log: one row per non-success (skip, timeout, empty/error, no-images, rate-stop), with a `permanent` flag and a `category`.
- Specs: `docs/superpowers/specs/2026-07-06-multipage-images-design.md`, `2026-07-07-transcription-usage-monitor-design.md`.

## Environment notes

- Python via `uv` (`uv run python3 …`); tests: `uv run pytest` (63 passing).
- Omeka API moved to `https://omeka.wardepartmentpapers.org/api/` (VPN-only); old `www.` host is dead. The transcription run does NOT need the API — only `obj.rrchnm.org` for images.
- Frontmatter edits use minimal-diff regex surgery, never `yaml.dump`.
