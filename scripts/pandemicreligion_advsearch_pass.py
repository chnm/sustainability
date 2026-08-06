#!/usr/bin/env python3
"""In-place: repoint the browse controls' dead 'Advanced search' link at the
committed Pagefind search page, over the browse-controls-kept sites. Logic lives
in pandemicreligion_flatten.py (reproducible); the asset-path prefix is derived
from each file's depth below its site root. Idempotent.

Usage: pandemicreligion_advsearch_pass.py [--dry-run] <site-dir> [<site-dir> ...]
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
            rel = p.relative_to(root)
            prefix = "../" * (len(rel.parts) - 1)
            t = p.read_text(encoding="utf-8", errors="replace")
            n = F.replace_advanced_search(t, prefix)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
    print(f"{'would change' if dry else 'changed'} {changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
