#!/usr/bin/env python3
"""Find images with missing or weak alt text in a site directory and generate
replacements with Claude.

Works on any site in this monorepo: flattened HTML crawls and Hugo sources
alike. Scans every *.html and *.md under SITE. Flags <img> tags and Markdown
images whose alt is empty, a placeholder, or a filename/URL. With --strict it
also flags alt that is short or duplicated (the crdh behaviour), and appends
one generated sentence of detail instead of replacing the human text.

Usage:
    python utils/alt-text/generate-alt-text.py plastercast --list       # scan only, no Claude calls
    python utils/alt-text/generate-alt-text.py plastercast              # dry-run: list + suggest
    python utils/alt-text/generate-alt-text.py plastercast --apply      # patch files in place
    python utils/alt-text/generate-alt-text.py plastercast --limit 10   # try a few first
    python utils/alt-text/generate-alt-text.py plastercast --model opus
    python utils/alt-text/generate-alt-text.py thanksroy --base-url https://thanksroy.org
        # sites whose media lives in a bucket: fetch images that are not on disk

Requires: claude CLI (Claude Code) installed and authenticated.
Self-check: python utils/alt-text/test_generate_alt_text.py
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
SRC_RE = re.compile(r'\bsrc="([^"]+)"', re.I)
ALT_RE = re.compile(r'\balt="([^"]*)"', re.I)
PLACEHOLDER_RE = re.compile(r"^(\s*|alt|alt[- ]text|image|todo)$", re.I)
# alt that is really a path: a URL, a slash path, or a bare filename with an image extension
FILENAME_RE = re.compile(r"^(https?://\S+|\S*/\S+|\S+\.(jpe?g|png|gif|svg|webp|tiff?))$", re.I)
SKIP_DIRS = {"node_modules", ".git"}
MIN_ALT_LEN = 40

PROMPT_TEMPLATE = (
    "Read the image at {image_path} and describe it in one or two concise "
    "sentences for use as alt text on a digital history and humanities website. "
    'Focus on what is visually depicted. Do not start with "This image shows" '
    'or "The image depicts". Just state what you see. '
    "Always finish your sentence — never cut off mid-word or mid-phrase. "
    "Aim for under 200 characters but completeness matters more than brevity. "
    "Output ONLY the alt text, nothing else — no labels, no quotes."
)

EXTEND_TEMPLATE = (
    "Read the image at {image_path}. A human already wrote this alt text for it: "
    '"{existing}". Write ONE additional sentence adding specific visual detail '
    "not already stated (labels, place names, values, colors, layout) so a "
    "screen reader user can tell this figure apart from similar ones. "
    'Do not repeat or rephrase the existing text. Do not start with "This image". '
    "Always finish the sentence. Output ONLY the new sentence, no quotes."
)


def weak_reason(alt: str, dupes: set[str], strict: bool = False) -> str | None:
    """Why this alt needs regenerating, or None if it looks fine."""
    alt = alt.strip()
    if PLACEHOLDER_RE.match(alt):
        return "missing"
    if FILENAME_RE.match(alt):
        return "filename"
    if strict and alt.lower() in dupes:
        return "duplicate"
    if strict and len(alt) < MIN_ALT_LEN:
        return "short"
    return None


def site_files(site: Path, pattern: str) -> list[Path]:
    return sorted(p for p in site.rglob(pattern) if not SKIP_DIRS & set(p.parts))


def find_weak(site: Path, strict: bool) -> list[dict]:
    """Return one entry per image whose alt needs work."""
    found = []
    images = []  # (file, text, match, alt, ref, kind)
    for md in site_files(site, "*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in MD_IMG_RE.finditer(text):
            ref = m.group(2).split('"')[0].split("'")[0].strip()
            images.append((md, text, m, m.group(1), ref, "markdown"))
    for html in site_files(site, "*.html"):
        text = html.read_text(encoding="utf-8", errors="replace")
        for m in HTML_IMG_RE.finditer(text):
            tag = m.group(0)
            alt = ALT_RE.search(tag)
            src = SRC_RE.search(tag)
            images.append((html, text, m, alt.group(1) if alt else "", src.group(1) if src else "", "html"))
    alts = [a.strip().lower() for *_, a, _, _ in images]
    dupes = {a for a in alts if a and alts.count(a) > 1} if strict else set()
    for file, text, m, alt, ref, kind in images:
        reason = weak_reason(alt, dupes, strict)
        if reason:
            found.append({
                "alt": alt.strip(), "file": file, "match": m.group(0), "img_ref": ref,
                "line": text[: m.start()].count("\n") + 1, "type": kind, "reason": reason,
            })
    return found


def resolve_image_path(site: Path, src_file: Path, img_ref: str, base_url: str = "") -> Path | str | None:
    """Map a reference to a file on disk (site-root absolute, file-relative, or Hugo
    /static). If it is not on disk and base_url is set, return the URL to fetch instead."""
    if not img_ref or "{{" in img_ref or "'+" in img_ref or img_ref.startswith(("http://", "https://", "data:")):
        return None
    ref = img_ref.split("?")[0].split("#")[0]
    if ref.startswith("/"):
        candidates = [site / ref.lstrip("/"), site / "static" / ref.lstrip("/")]
    else:
        candidates = [src_file.parent / ref]
    on_disk = next((Path(os.path.normpath(c)) for c in candidates if c.is_file()), None)
    if on_disk or not base_url:
        return on_disk
    site_rel = os.path.relpath(os.path.normpath(candidates[0]), site)
    return None if site_rel.startswith("..") else f"{base_url.rstrip('/')}/{site_rel}"


def fetch(url: str, cache_dir: Path) -> Path | None:
    """Download url into cache_dir (once) so claude can Read it."""
    dest = cache_dir / url.rsplit("/", 1)[-1]
    if dest.exists():
        return dest
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            dest.write_bytes(r.read())
    except Exception as exc:  # 404 from the bucket, network, etc.
        print(f"  ERROR: fetch failed for {url}: {exc}", file=sys.stderr)
        return None
    return dest


def generate_alt_text(image_path: Path, model: str, existing: str = "") -> str:
    """Call claude -p for fresh alt text, or one extra sentence if alt exists."""
    template = EXTEND_TEMPLATE if existing else PROMPT_TEMPLATE
    prompt = template.format(image_path=image_path, existing=existing)
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--allowedTools", "Read"],
            capture_output=True, text=True, timeout=120,
        )
    except FileNotFoundError:
        sys.exit("ERROR: 'claude' CLI not found. Install Claude Code first.")
    except subprocess.TimeoutExpired:
        print(f"  ERROR: claude timed out for {image_path}", file=sys.stderr)
        return ""
    if result.returncode != 0:
        print(f"  ERROR: claude failed for {image_path}: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return clean(result.stdout)


def clean(text: str) -> str:
    text = re.sub(r"^\*\*.*?\*\*:?\s*", "", text.strip())
    if len(text) > 1 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    text = " ".join(text.split())
    if text and text.rstrip("\"'")[-1:] not in (".", "!", "?"):
        text += "."
    return text


def new_alt(entry: dict, generated: str) -> str:
    """Append to human alt for short/duplicate; otherwise replace it."""
    if entry["reason"] in ("short", "duplicate"):
        return clean(entry["alt"]) + " " + generated
    return generated


def patched_tag(old: str, kind: str, img_ref: str, alt: str) -> str:
    if kind == "markdown":
        return f"![{alt}]({img_ref})"
    alt = alt.replace('"', "&quot;")
    if ALT_RE.search(old):
        return ALT_RE.sub(f'alt="{alt}"', old, count=1)
    body = old[:-1].rstrip()
    close = "/>" if body.endswith("/") else ">"
    return body.rstrip("/").rstrip() + f' alt="{alt}"' + close


def patch(entry: dict, alt: str) -> None:
    """Rewrite the matched image with alt text (first occurrence only)."""
    text = entry["file"].read_text(encoding="utf-8", errors="replace")
    new = patched_tag(entry["match"], entry["type"], entry["img_ref"], alt)
    entry["file"].write_text(text.replace(entry["match"], new, 1), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate alt text for images missing it.")
    parser.add_argument("site", type=Path, help="Site directory to scan, e.g. plastercast")
    parser.add_argument("--apply", action="store_true", help="Patch files in place (default: dry run)")
    parser.add_argument("--list", action="store_true", help="Only list flagged images; no Claude calls")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N generated alts (0 = no limit)")
    parser.add_argument("--strict", action="store_true", help="Also flag short or duplicated alt text")
    parser.add_argument("--model", default="claude-sonnet-5", help="Claude model (default: claude-sonnet-5)")
    parser.add_argument("--base-url", default="", help="Fetch images not on disk from this site URL, e.g. https://thanksroy.org")
    args = parser.parse_args()
    if not args.site.is_dir():
        sys.exit(f"ERROR: {args.site} is not a directory")

    entries = find_weak(args.site, args.strict)
    if not entries:
        print("No images with missing or weak alt text found.")
        return
    print(f"Found {len(entries)} image(s) with missing or weak alt text.\n")

    cache: dict[tuple[str, str], str] = {}  # same image on many pages: generate once
    fetch_dir = Path(tempfile.mkdtemp(prefix="alt-text-"))
    processed = skipped = 0
    for e in entries:
        rel = e["file"].relative_to(args.site)
        img = resolve_image_path(args.site, e["file"], e["img_ref"], args.base_url)
        if img is None:
            print(f"  SKIP [{e['type']}]: {rel}:{e['line']} — cannot resolve {e['img_ref'] or '(dynamic src)'}; add alt by hand")
            skipped += 1
            continue
        print(f"  [{e['type']}, {e['reason']}] {rel}:{e['line']} — {img if isinstance(img, str) else e['img_ref']}")
        if args.list:
            continue
        existing = e["alt"] if e["reason"] in ("short", "duplicate") else ""
        key = (str(img), existing)
        if key not in cache:
            if args.limit and len(cache) >= args.limit:
                print("    (limit reached)")
                break
            local = fetch(img, fetch_dir) if isinstance(img, str) else img
            cache[key] = generate_alt_text(local, args.model, existing) if local else ""
        if not cache[key]:
            skipped += 1
            continue
        alt = new_alt(e, cache[key])
        print(f"    → {alt}")
        if args.apply:
            patch(e, alt)
            print("    ✓ Patched")
        processed += 1

    if args.list:
        return
    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Claude calls: {len(cache)}")
    if not args.apply and processed:
        print("Run with --apply to write changes to files.")


if __name__ == "__main__":
    main()
