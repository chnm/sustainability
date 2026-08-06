#!/usr/bin/env python3
"""In-place: repair double-escaped Pagefind result titles (data-pf-title). Logic
lives in pandemicreligion_flatten.py. Idempotent. After running this, rebuild
Pagefind for the affected sites so the index carries the corrected titles.

Usage: pandemicreligion_pftitle_pass.py [--dry-run] <site-dir> [<site-dir> ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandemicreligion_flatten as F   # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    roots = [Path(a) for a in args if a != "--dry-run"]
    changed = total = 0
    for root in roots:
        for p in sorted(root.rglob("*.html")):
            total += 1
            t = p.read_text(encoding="utf-8", errors="replace")
            n = F.fix_pf_title_escaping(t)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
    print(f"{'would change' if dry else 'changed'} {changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
