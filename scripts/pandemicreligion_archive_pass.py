#!/usr/bin/env python3
"""Archive pass over the already-flattened, committed Pandemic Religion sites.

Applies the archival transforms in place (no re-flatten): upgrade the archived
statement, redirect the project's own contact address to chnm@gmu.edu, and
neutralize the "contribute / share" calls-to-action. The transform logic lives
in pandemicreligion_flatten.py so a future re-crawl reproduces the same result;
this driver only re-applies it to the committed HTML and upgrades the older,
terser statement wording that predates the flatten-script change.

Usage: pandemicreligion_archive_pass.py [--dry-run] <site-dir> [<site-dir> ...]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandemicreligion_flatten as F   # noqa: E402

_NOTE_DIV = re.compile(r'<div class="archived-form-note"[^>]*>.*?</div>', re.DOTALL)


def upgrade_note(text: str) -> str:
    """Replace any existing archived-form-note (older wording) with the current
    statement, so committed pages match a fresh flatten."""
    return _NOTE_DIV.sub(lambda _: F._DEAD_FORM_NOTE, text)


def process(text: str) -> str:
    text = upgrade_note(text)
    text = F.ensure_archive_statement(text)
    text = F.archive_contact_email(text)
    text = F.strip_contribute_ctas(text)
    return text


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    roots = [Path(a) for a in args if a != "--dry-run"]
    changed = total = 0
    for root in roots:
        for p in sorted(root.rglob("*.html")):
            total += 1
            t = p.read_text(encoding="utf-8", errors="replace")
            n = process(t)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
    verb = "would change" if dry else "changed"
    print(f"{verb} {changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
