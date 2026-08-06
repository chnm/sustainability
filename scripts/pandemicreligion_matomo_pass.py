#!/usr/bin/env python3
"""In-place: re-add Matomo analytics to the committed archives -- a single
per-site block (one siteId per MATOMO_SITE_IDS; the live Omeka pages
double-tagged with the project-wide 74 roll-up) inserted just before </head>.
Logic lives in pandemicreligion_flatten.py (add_matomo). The site dir name is
the domain. Idempotent: pages already carrying a stats.rrchnm.org tracker are
skipped. Head-only insertion, so no Pagefind rebuild is needed.

Usage: pandemicreligion_matomo_pass.py [--dry-run] <site-dir> [<site-dir> ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandemicreligion_flatten as F   # noqa: E402


def main() -> None:
    args = sys.argv[1:]
    dry = "--dry-run" in args
    roots = [Path(a) for a in args if a != "--dry-run"]
    for root in roots:
        domain = root.resolve().name
        changed = total = 0
        for p in sorted(root.rglob("*.html")):
            if "pagefind" in p.parts:
                continue
            total += 1
            t = p.read_text(encoding="utf-8", errors="replace")
            n = F.add_matomo(t, domain)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
        print(f"[{domain}] siteId {F.MATOMO_SITE_IDS.get(domain, '?')}: "
              f"{'would tag' if dry else 'tagged'} {changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
