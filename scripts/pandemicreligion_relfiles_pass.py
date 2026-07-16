#!/usr/bin/env python3
"""In-place: relativize own-domain media URLs (https://<domain>/files/... and
Omeka's entity-escaped form) to root-relative /files/..., now that /files/ is
served from the shared object-storage bucket via each site's Caddy. Logic lives
in pandemicreligion_flatten.py (relativize_media). The site dir name is the
domain. Idempotent. After running this, rebuild Pagefind for the affected sites
so the result-thumbnail image URLs in the index go root-relative too.

Usage: pandemicreligion_relfiles_pass.py [--dry-run] <site-dir> [<site-dir> ...]
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
            n = F.relativize_media(t, domain)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
        print(f"[{domain}] {'would change' if dry else 'changed'} "
              f"{changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
