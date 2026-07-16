#!/usr/bin/env python3
"""In-place footer/About logo normalization over the committed sites.

Applies the same transforms now baked into pandemicreligion_flatten.py:
replace each footer's logo area with a self-contained RRCHNM + GMU side-by-side
pair (committed assets, no live-host dependency), and add a labeled institutional
credit at the end of every About page. The asset-path prefix is derived from each
file's depth below its site root. Idempotent.

Usage: pandemicreligion_logos_pass.py [--dry-run] <site-dir> [<site-dir> ...]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandemicreligion_flatten as F   # noqa: E402

ABOUT_RE = re.compile(r"/page/about\.html$", re.IGNORECASE)


def process(text: str, prefix: str, is_about: bool) -> str:
    text = F.replace_footer(text, prefix)
    if is_about:
        text = F.add_about_logos(text, prefix)
    return text


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
            is_about = bool(ABOUT_RE.search("/" + rel.as_posix()))
            t = p.read_text(encoding="utf-8", errors="replace")
            n = process(t, prefix, is_about)
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
    print(f"{'would change' if dry else 'changed'} {changed}/{total} html file(s)")


if __name__ == "__main__":
    main()
