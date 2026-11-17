#!/usr/bin/env python3
"""Import a wget mirror of gulaghistory.org into gulaghistory/.

    python3 scripts/gulaghistory_import.py <crawl>/gulaghistory.org

- Omeka served item images and PDFs from extensionless routes
  (files/download/N/fullsize, files/display/N/square_thumbnail), so wget saved
  them as .html. They are renamed to their real type (.jpg, .pdf, ...) and
  every reference is rewritten, otherwise a static server sends them as HTML.
- WordPress feed and xmlrpc debris from the podcast section is dropped.
- Bulk media (archive/files/ video and audio, files/download/ full-size images
  and PDFs, the podcast MP3) stays out of git via gulaghistory/.gitignore and is
  listed with size and MD5 in gulaghistory/MEDIA.tsv for upload to storage.

Re-running over an existing import is safe: the copy is replaced wholesale.
"""
import hashlib
import re
import shutil
import sys
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "gulaghistory"

# Paths (relative to the site root) kept out of git and served from storage.
IGNORED = ["archive/files/", "files/download/", "podcast/podpress_trac/"]

DROP_RE = re.compile(r"(^|/)feed/index\.html$|xmlrpc\.php\?rsd\.html$")
OMEKA_ROUTE_RE = re.compile(r"(files/(?:display|download)/\d+/[a-z_]+)\.html")

MAGIC = [(b"%PDF", "pdf"), (b"\xff\xd8\xff", "jpg"), (b"\x89PNG", "png"), (b"GIF8", "gif")]


def sniff(path: Path) -> str | None:
    head = path.read_bytes()[:8]
    return next((ext for sig, ext in MAGIC if head.startswith(sig)), None)


def ignored(rel: str) -> bool:
    return any(rel.startswith(p) for p in IGNORED)


def main(src: Path) -> None:
    if not (src / "index.html").is_file():
        sys.exit(f"{src} does not look like the site root (no index.html)")
    if DEST.exists():
        shutil.rmtree(DEST)
    renamed: dict[str, str] = {}
    dropped = 0
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src).as_posix()
        if DROP_RE.search(rel):
            dropped += 1
            continue
        out = rel
        m = OMEKA_ROUTE_RE.fullmatch(rel)
        if m and (ext := sniff(path)):
            out = f"{m.group(1)}.{ext}"
            renamed[m.group(1)] = ext
        target = DEST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

    def fix(m: re.Match) -> str:
        ext = renamed.get(m.group(1))
        return f"{m.group(1)}.{ext}" if ext else m.group(0)

    rewritten = 0
    for page in DEST.rglob("*"):
        if page.suffix not in (".html", ".css") or not page.is_file():
            continue
        with open(page, encoding="utf-8", errors="surrogateescape", newline="") as f:
            text = f.read()
        new = OMEKA_ROUTE_RE.sub(fix, text)
        if new != text:
            with open(page, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
                f.write(new)
            rewritten += 1

    (DEST / ".gitignore").write_text(
        "# Bulk media, served from object storage; see MEDIA.tsv.\n"
        + "".join(f"/{p}\n" for p in IGNORED)
    )
    rows = ["path\tbytes\tmd5"]
    for path in sorted(DEST.rglob("*")):
        rel = path.relative_to(DEST).as_posix()
        if path.is_file() and ignored(rel):
            rows.append(f"{rel}\t{path.stat().st_size}\t{hashlib.md5(path.read_bytes()).hexdigest()}")
    (DEST / "MEDIA.tsv").write_text("\n".join(rows) + "\n")
    print(f"renamed {len(renamed)} Omeka files, rewrote {rewritten} pages, "
          f"dropped {dropped} feed files, {len(rows) - 1} media files listed in MEDIA.tsv")


def selfcheck() -> None:
    assert OMEKA_ROUTE_RE.fullmatch("files/download/12/fullsize.html").group(1) == "files/download/12/fullsize"
    assert OMEKA_ROUTE_RE.sub(lambda m: m.group(1) + ".jpg", 'src="../files/display/3/square_thumbnail.html"') == \
        'src="../files/display/3/square_thumbnail.jpg"'
    assert DROP_RE.search("podcast/archive/x/feed/index.html") and DROP_RE.search("podcast/xmlrpc.php?rsd.html")
    assert not DROP_RE.search("podcast/archive/x/index.html")
    assert ignored("archive/files/a.mp4") and not ignored("archive/index.html")


if __name__ == "__main__":
    selfcheck()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
