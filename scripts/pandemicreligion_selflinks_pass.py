#!/usr/bin/env python3
"""In-place: rewrite each site's absolute links to its OWN pages as document-
relative paths (media /files/ and malformed/embedded URLs stay absolute). Logic
lives in pandemicreligion_flatten.py; the site's own domain is its directory
name, and target existence is checked against the site tree. Idempotent.

Usage: pandemicreligion_selflinks_pass.py [--dry-run] <site-dir> [<site-dir> ...]
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
        own_domain = root.name          # e.g. collectingthesetimes.org
        for p in sorted(root.rglob("*.html")):
            total += 1
            rel = p.relative_to(root).as_posix()
            t = p.read_text(encoding="utf-8", errors="replace")
            n = F.relativize_self_links(t, own_domain, rel, root)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
    print(f"{'would change' if dry else 'changed'} {changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
