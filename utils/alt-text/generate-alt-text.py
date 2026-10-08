#!/usr/bin/env python3
"""Find images with missing or weak alt text in a site directory and generate
replacements with a vision model: Claude via the claude CLI (default), Claude
via the Anthropic API, or any model behind an OpenAI-compatible chat endpoint
(Ollama, LM Studio, vLLM, hosted providers).

Works on any site in this monorepo: flattened HTML crawls and Hugo sources
alike. Scans every *.html, *.htm and *.md under SITE. Flags <img> tags and Markdown
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
    python utils/alt-text/generate-alt-text.py plastercast --backend openai \
        --api-url http://localhost:11434/v1 --model qwen2.5vl:7b
        # local open model via Ollama; OPENAI_API_KEY (or --api-key) for hosted endpoints
    python utils/alt-text/generate-alt-text.py plastercast --backend anthropic
        # Claude via the API instead of the CLI; reads ANTHROPIC_API_KEY

Requires: claude CLI (Claude Code) installed and authenticated for the default
backend; `uv run --with anthropic` for --backend anthropic; nothing beyond the
standard library for --backend openai.
Self-check: python utils/alt-text/test_generate_alt_text.py
"""

import argparse
import base64
import functools
import hashlib
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
SRC_RE = re.compile(r'(?<![\w-])src\s*=\s*(?:"([^"]+)"|([^\s>"\']+))', re.I)  # old crawls leave src unquoted
ALT_RE = re.compile(r'(?<![\w-])alt="([^"]*)"', re.I)
PLACEHOLDER_RE = re.compile(r"^(\s*|alt|alt[- ]text|image|todo)$", re.I)
# alt that is really a path: a URL, a slash path, or a bare filename with an image extension
FILENAME_RE = re.compile(r"^(https?://\S+|\S*/\S+|\S+\.(jpe?g|png|gif|svg|webp|tiff?))$", re.I)
SKIP_DIRS = {"node_modules", ".git"}
MIN_ALT_LEN = 40
# Omeka serves one upload as several derivatives under the same hash name
# (files/large/abc.jpg, files/square/abc.jpg, files/original/abc.png)
OMEKA_DERIVATIVE_RE = re.compile(r"/files/(?:original|fullsize|large|medium|thumbnails|square_thumbnails|square)/([^/]+?)\.\w+$")
# the model talking to us instead of describing ("I'm not able to view the image... re-upload")
NOT_A_DESCRIPTION_RE = re.compile(
    r"not able to (?:view|see|access|open)|(?:can't|cannot|unable to) (?:view|see|access|open)"
    r"|re-?upload|did ?n[o']?t come through|came through instead"
    r"|approv|(?:isn't|is not|not) actually an image|no actual image", re.I)
API_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}  # what vision APIs accept

PROMPT_TEMPLATE = (
    "{image} Describe it in one or two concise "
    "sentences for use as alt text on a digital history and humanities website. "
    'Focus on what is visually depicted. Do not start with "This image shows" '
    'or "The image depicts". Just state what you see. '
    "Always finish your sentence — never cut off mid-word or mid-phrase. "
    "Aim for under 200 characters but completeness matters more than brevity. "
    "Output ONLY the alt text, nothing else — no labels, no quotes."
)

EXTEND_TEMPLATE = (
    "{image} A human already wrote this alt text for it: "
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


def read_page(path: Path) -> tuple[str, str]:
    """Text and encoding. Old crawls mix UTF-8 with Latin-1 pages; latin-1 round-trips any bytes."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1"


def find_weak(site: Path, strict: bool, keep_empty: bool = False) -> list[dict]:
    """Return one entry per image whose alt needs work."""
    found = []
    images = []  # (file, text, match, alt, ref, kind)
    for md in site_files(site, "*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in MD_IMG_RE.finditer(text):
            ref = m.group(2).split('"')[0].split("'")[0].strip()
            images.append((md, text, m, m.group(1), ref, "markdown"))
    for page in site_files(site, "*.htm*"):
        text, _ = read_page(page)
        for m in HTML_IMG_RE.finditer(text):
            tag = m.group(0)
            alt = ALT_RE.search(tag)
            if keep_empty and alt and not alt.group(1).strip():
                continue  # alt="" marks the image decorative
            src = SRC_RE.search(tag)
            images.append((page, text, m, html.unescape(alt.group(1)) if alt else "",
                           html.unescape(src.group(1) or src.group(2)) if src else "", "html"))
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


class ImageFailed(Exception):
    """One image could not be described; the run logs it and moves on."""


def write_log(path: Path, **record) -> None:
    """Append one JSON line to the run log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def previous_alts(log: Path, site: str, model: str) -> dict[tuple[str, str], str]:
    """Descriptions earlier runs of this model made for this site, so a resumed or
    re-run pass reuses them instead of describing (and paying for) a photo again."""
    found = {}
    if not log.is_file():
        return found
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:  # a line cut short by Ctrl-C
            continue
        if (r.get("status") == "ok" and r.get("site") == site and r.get("model") == model
                and not NOT_A_DESCRIPTION_RE.search(r["alt"])):
            found[(image_key(r["image"]), r["existing"])] = r["alt"]  # later lines win
    return found


def image_key(img: Path | str) -> str:
    """Same key for every Omeka derivative of one upload, so it is described once."""
    return OMEKA_DERIVATIVE_RE.sub(r"/files/\1", str(img))


def largest_derivative(img: Path | str) -> str:
    """Omeka's square/medium thumbnails are too small to read a scanned page; use the large copy."""
    big = re.sub(r"/files/(?:medium|square)/", "/files/large/", str(img))                        # Omeka S
    return re.sub(r"/files/(?:thumbnails|square_thumbnails)/", "/files/fullsize/", big)          # Omeka Classic


def load(img: Path | str, cache_dir: Path) -> tuple[Path, str]:
    """Local file to describe for img, preferring its largest derivative; returns (file, what it came from)."""
    big = largest_derivative(img)
    if not isinstance(img, str):
        return (Path(big), big) if Path(big).is_file() else (img, str(img))
    if big != img:
        try:
            return fetch(big, cache_dir), big
        except ImageFailed:
            pass  # no large copy; describe what the page links
    return fetch(img, cache_dir), img


def fetch(url: str, cache_dir: Path) -> Path:
    """Download url into cache_dir (once) so the model can read it."""
    suffix = Path(urllib.parse.urlsplit(url).path).suffix
    dest = cache_dir / (hashlib.sha1(url.encode()).hexdigest()[:16] + suffix)
    if dest.exists():
        return dest
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            dest.write_bytes(r.read())
    except Exception as exc:  # 404 from the bucket, network, etc.
        raise ImageFailed(f"fetch failed for {url}: {exc}") from exc
    return dest


def build_prompt(image_phrase: str, existing: str) -> str:
    template = EXTEND_TEMPLATE if existing else PROMPT_TEMPLATE
    return template.format(image=image_phrase, existing=existing)


def generate_alt_text(image_path: Path, existing: str, args) -> str:
    """Fresh alt text, or one extra sentence if alt exists, from the chosen backend."""
    if is_html(image_path):  # crawls save error pages under image names (x.gif".html)
        raise ImageFailed(f"{image_path.name} is an HTML page, not an image; add alt by hand")
    if args.backend != "claude" and image_mime(image_path) not in API_IMAGE_TYPES:
        raise ImageFailed(f"{image_path.suffix} is not jpeg/png/gif/webp; use --backend claude or add alt by hand")
    if args.backend == "openai":
        prompt = build_prompt("Look at the attached image.", existing)
        text = call_openai(image_path, prompt, args.model, args.api_url, args.api_key)
    elif args.backend == "anthropic":
        text = call_anthropic(image_path, build_prompt("Look at the attached image.", existing), args.model)
    else:
        prompt = build_prompt(f"Read the image at {image_path}.", existing)
        text = call_claude(prompt, args.model)
    text = clean(text)
    if NOT_A_DESCRIPTION_RE.search(text):
        raise ImageFailed(f"model did not describe the image: {text[:100]}")
    return text


def call_claude(prompt: str, model: str) -> str:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--allowedTools", "Read"],
            capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        sys.exit("ERROR: 'claude' CLI not found. Install Claude Code first.")
    except subprocess.TimeoutExpired as exc:
        raise ImageFailed("claude timed out") from exc
    if result.returncode != 0:
        raise ImageFailed(f"claude failed: {(result.stdout + result.stderr).strip()}")  # auth errors land on stdout
    return result.stdout


def image_mime(path: Path) -> str:
    """Sniff the real type: URLs like default.png%3Fv=3.1.0 have no usable extension."""
    with path.open("rb") as f:
        head = f.read(12)
    for magic, mime in ((b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG", "image/png"), (b"GIF8", "image/gif")):
        if head.startswith(magic):
            return mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return mimetypes.guess_type(path.name)[0] or "image/jpeg"


def is_html(path: Path) -> bool:
    with path.open("rb") as f:
        head = f.read(512).lstrip().lower()
    return head.startswith((b"<!doctype html", b"<html", b"<head", b"<body"))


def b64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode()


def anthropic_content(image_path: Path, prompt: str) -> list[dict]:
    """User content for a Messages API call: the image, then the prompt."""
    return [
        {"type": "image", "source": {"type": "base64", "media_type": image_mime(image_path), "data": b64(image_path)}},
        {"type": "text", "text": prompt},
    ]


@functools.cache
def anthropic_client():
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: --backend anthropic needs the SDK; run with: uv run --with anthropic python ...")
    return anthropic.Anthropic()  # ANTHROPIC_API_KEY or an `ant auth login` profile


def call_anthropic(image_path: Path, prompt: str, model: str) -> str:
    client = anthropic_client()  # exits with an install hint if the SDK is missing
    import anthropic
    try:
        msg = client.messages.create(
            model=model, max_tokens=16000,
            messages=[{"role": "user", "content": anthropic_content(image_path, prompt)}],
        )
    except (anthropic.AuthenticationError, TypeError) as exc:  # TypeError: no credentials configured at all
        sys.exit(f"ERROR: Anthropic API auth failed; set ANTHROPIC_API_KEY. {exc}")
    except anthropic.APIError as exc:  # rate limit after SDK retries, oversized image, etc.
        raise ImageFailed(f"Anthropic API failed: {exc}") from exc
    if msg.stop_reason == "refusal":
        raise ImageFailed("Claude declined; add alt by hand")
    return "".join(b.text for b in msg.content if b.type == "text")


def openai_request(image_path: Path, prompt: str, model: str, api_url: str, api_key: str) -> urllib.request.Request:
    """POST body for an OpenAI-compatible /chat/completions call with the image inline."""
    data_url = f"data:{image_mime(image_path)};base64,{b64(image_path)}"
    body = {
        "model": model,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]}],
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return urllib.request.Request(f"{api_url.rstrip('/')}/chat/completions",
                                  data=json.dumps(body).encode(), headers=headers)


def call_openai(image_path: Path, prompt: str, model: str, api_url: str, api_key: str) -> str:
    try:
        with urllib.request.urlopen(openai_request(image_path, prompt, model, api_url, api_key), timeout=300) as r:
            return json.load(r)["choices"][0]["message"]["content"]
    except Exception as exc:  # connection refused, HTTP error, unexpected shape
        raise ImageFailed(f"{api_url} failed: {exc}") from exc


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


def patched_tag(old: str, kind: str, alt: str) -> str:
    if kind == "markdown":
        return MD_IMG_RE.sub(lambda m: f"![{alt}]({m.group(2)})", old, count=1)
    alt = html.escape(alt, quote=False).replace('"', "&quot;")  # a quoted sign like "Prayer > the virus"
    if ALT_RE.search(old):
        return ALT_RE.sub(f'alt="{alt}"', old, count=1)
    body = old[:-1].rstrip()
    close = "/>" if body.endswith("/") else ">"
    return body.rstrip("/").rstrip() + f' alt="{alt}"' + close


def patch(entry: dict, alt: str) -> None:
    """Rewrite the matched image with alt text (first occurrence only)."""
    text, encoding = read_page(entry["file"])
    new = patched_tag(entry["match"], entry["type"], alt)
    entry["file"].write_bytes(text.replace(entry["match"], new, 1).encode(encoding, "xmlcharrefreplace"))


def main():
    parser = argparse.ArgumentParser(description="Generate alt text for images missing it.")
    parser.add_argument("site", type=Path, help="Site directory to scan, e.g. plastercast")
    parser.add_argument("--apply", action="store_true", help="Patch files in place (default: dry run)")
    parser.add_argument("--list", action="store_true", help="Only list flagged images; no model calls")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N generated alts (0 = no limit)")
    parser.add_argument("--strict", action="store_true", help="Also flag short or duplicated alt text")
    parser.add_argument("--keep-empty", action="store_true",
                        help='Treat alt="" as deliberately decorative instead of missing')
    parser.add_argument("--backend", choices=["claude", "anthropic", "openai"], default="claude",
                        help="claude: the claude CLI (default); anthropic: the Anthropic API; "
                             "openai: any OpenAI-compatible chat endpoint")
    parser.add_argument("--model", default=None,
                        help="Model name (default: claude-sonnet-5 for claude/anthropic; required for openai)")
    parser.add_argument("--api-url", default="http://localhost:11434/v1",
                        help="Base URL for --backend openai (default: Ollama at http://localhost:11434/v1)")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""),
                        help="Bearer token for --backend openai (default: $OPENAI_API_KEY)")
    parser.add_argument("--base-url", default="", help="Fetch images not on disk from this site URL, e.g. https://thanksroy.org")
    parser.add_argument("--fresh", action="store_true",
                        help="Describe every image again instead of reusing this site's descriptions from --log")
    parser.add_argument("--log", type=Path, default=Path(__file__).parent / "logs" / "runs.jsonl",
                        help="Append one JSON line per model call and per unresolved image (default: utils/alt-text/logs/runs.jsonl)")
    args = parser.parse_args()
    if not args.site.is_dir():
        sys.exit(f"ERROR: {args.site} is not a directory")
    if args.backend == "openai" and not args.model:
        sys.exit("ERROR: --backend openai needs --model, e.g. --model qwen2.5vl:7b")
    args.model = args.model or "claude-sonnet-5"

    entries = find_weak(args.site, args.strict, args.keep_empty)
    if not entries:
        print("No images with missing or weak alt text found.")
        return
    print(f"Found {len(entries)} image(s) with missing or weak alt text.\n")

    # same image on many pages: generate once, and reuse what earlier runs of this model generated
    cache = {} if args.fresh or args.list else previous_alts(args.log, str(args.site), args.model)
    if cache:
        print(f"Reusing {len(cache)} description(s) from {args.log}; --fresh to describe again.\n")
    calls = 0
    fetch_dir = Path(tempfile.mkdtemp(prefix="alt-text-"))
    processed = skipped = 0
    run = datetime.now(timezone.utc).isoformat(timespec="seconds")
    def log(**record):
        if not args.list:
            write_log(args.log, run=run, time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      site=str(args.site), backend=args.backend, model=args.model, **record)

    for e in entries:
        rel = e["file"].relative_to(args.site)
        img = resolve_image_path(args.site, e["file"], e["img_ref"], args.base_url)
        if img is None:
            print(f"  SKIP [{e['type']}]: {rel}:{e['line']} — cannot resolve {e['img_ref'] or '(dynamic src)'}; add alt by hand")
            log(status="unresolved", page=f"{rel}:{e['line']}", image=e["img_ref"], reason=e["reason"])
            skipped += 1
            continue
        print(f"  [{e['type']}, {e['reason']}] {rel}:{e['line']} — {img if isinstance(img, str) else e['img_ref']}")
        if args.list:
            continue
        existing = e["alt"] if e["reason"] in ("short", "duplicate") else ""
        key = (image_key(img), existing)
        if key not in cache:
            if args.limit and calls >= args.limit:
                print("    (limit reached)")
                break
            calls += 1
            start, error, described = time.monotonic(), "", str(img)
            try:
                local, described = load(img, fetch_dir)
                cache[key] = generate_alt_text(local, existing, args)
            except ImageFailed as exc:
                print(f"    ERROR: {exc}", file=sys.stderr)
                cache[key], error = "", str(exc)
            log(status="ok" if cache[key] else "error", error=error or ("" if cache[key] else "empty response"),
                page=f"{rel}:{e['line']}", image=described, reason=e["reason"], existing=existing,
                alt=cache[key], applied=args.apply, seconds=round(time.monotonic() - start, 1))
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
    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Model calls: {calls}")
    if not args.apply and processed:
        print("Run with --apply to write changes to files.")


if __name__ == "__main__":
    main()
