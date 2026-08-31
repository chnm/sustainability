#!/bin/sh
# Auto-resume wrapper: regenerate the queue, run the transcriber, and on any
# stop (session/weekly limit, crash) sleep 30 min and try again. Exits when
# the queue is empty.
cd "$(dirname "$0")/.." || exit 1
while :; do
  python3 - <<'PY'
from pathlib import Path
d = Path("_transcription")
q = [l.strip() for l in open(d / "remaining_ids.txt") if l.strip()]
done = set((d / ".transcribe_progress").read_text().split())
skip = set((d / "skip_ids.txt").read_text().split())
rem = [i for i in q if i not in done and i not in skip]
(d / "remaining_ids.txt").write_text("\n".join(rem) + "\n" if rem else "")
print(f"queue: {len(rem)} remaining")
PY
  [ -s _transcription/remaining_ids.txt ] || { echo "queue empty, done"; break; }
  python3 -u _transcription/transcribe.py --ids-file _transcription/remaining_ids.txt --max-pages 150 --model claude-sonnet-4-6 2>&1 | tee _transcription/last_run.out
  grep -q "^To transcribe: 0$" _transcription/last_run.out && { echo "nothing left to transcribe (remaining docs exceed --max-pages), done"; break; }
  echo "transcriber exited $(date) — retrying in 30 min"
  sleep 1800
done
