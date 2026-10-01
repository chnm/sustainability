#!/usr/bin/env python3
"""Find images with missing or weak alt text in a site directory and generate
replacements with a vision model: Claude via the claude CLI (default), Claude
via the Anthropic API, or any model behind an OpenAI-compatible chat endpoint
(Ollama, LM Studio, vLLM, hosted providers).

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
import urllib.parse
import urllib.request
from pathlib import Path

MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
SRC_RE = re.compile(r'(?<![\w-])src="([^"]+)"', re.I)
ALT_RE = re.compile(r'(?<![\w-])alt="([^"]*)"', re.I)
PLACEHOLDER_RE = re.compile(r"^(\s*|alt|alt[- ]text|image|todo)$", re.I)
# alt that is really a path: a URL, a slash path, or a bare filename with an image extension
FILENAME_RE = re.compile(r"^(https?://\S+|\S*/\S+|\S+\.(jpe?g|png|gif|svg|webp|tiff?))$", re.I)
SKIP_DIRS = {"node_modules", ".git"}
MIN_ALT_LEN = 40
# Omeka serves one upload as several derivatives under the same hash name
# (files/large/abc.jpg, files/square/abc.jpg, files/original/abc.png)
OMEKA_DERIVATIVE_RE = re.compile(r"/files/(?:original|fullsize|large|medium|thumbnails|square_thumbnails|square)/([^/]+?)\.\w+$")
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


def find_weak(site: Path, strict: bool) -> list[dict]:
    """Return one entry per image whose alt needs work."""
    found = []
    images = []  # (file, text, match, alt, ref, kind)
    for md in site_files(site, "*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in MD_IMG_RE.finditer(text):
            ref = m.group(2).split('"')[0].split("'")[0].strip()
            images.append((md, text, m, m.group(1), ref, "markdown"))
    for page in site_files(site, "*.html"):
        text = page.read_text(encoding="utf-8", errors="replace")
        for m in HTML_IMG_RE.finditer(text):
            tag = m.group(0)
            alt = ALT_RE.search(tag)
            src = SRC_RE.search(tag)
            images.append((page, text, m, html.unescape(alt.group(1)) if alt else "",
                           html.unescape(src.group(1)) if src else "", "html"))
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


def image_key(img: Path | str) -> str:
    """Same key for every Omeka derivative of one upload, so it is described once."""
    return OMEKA_DERIVATIVE_RE.sub(r"/files/\1", str(img))


def fetch(url: str, cache_dir: Path) -> Path | None:
    """Download url into cache_dir (once) so the model can read it."""
    suffix = Path(urllib.parse.urlsplit(url).path).suffix
    dest = cache_dir / (hashlib.sha1(url.encode()).hexdigest()[:16] + suffix)
    if dest.exists():
        return dest
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            dest.write_bytes(r.read())
    except Exception as exc:  # 404 from the bucket, network, etc.
        print(f"  ERROR: fetch failed for {url}: {exc}", file=sys.stderr)
        return None
    return dest


def build_prompt(image_phrase: str, existing: str) -> str:
    template = EXTEND_TEMPLATE if existing else PROMPT_TEMPLATE
    return template.format(image=image_phrase, existing=existing)


def generate_alt_text(image_path: Path, existing: str, args) -> str:
    """Fresh alt text, or one extra sentence if alt exists, from the chosen backend."""
    if args.backend != "claude" and image_mime(image_path) not in API_IMAGE_TYPES:
        print(f"  SKIP: {image_path.suffix} is not jpeg/png/gif/webp; use --backend claude or add alt by hand")
        return ""
    if args.backend == "openai":
        prompt = build_prompt("Look at the attached image.", existing)
        text = call_openai(image_path, prompt, args.model, args.api_url, args.api_key)
    elif args.backend == "anthropic":
        text = call_anthropic(image_path, build_prompt("Look at the attached image.", existing), args.model)
    else:
        prompt = build_prompt(f"Read the image at {image_path}.", existing)
        text = call_claude(prompt, args.model)
    return clean(text)


def call_claude(prompt: str, model: str) -> str:
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--allowedTools", "Read"],
            capture_output=True, text=True, timeout=120,
        )
    except FileNotFoundError:
        sys.exit("ERROR: 'claude' CLI not found. Install Claude Code first.")
    except subprocess.TimeoutExpired:
        print("  ERROR: claude timed out", file=sys.stderr)
        return ""
    if result.returncode != 0:
        print(f"  ERROR: claude failed: {result.stderr.strip()}", file=sys.stderr)
        return ""
    return result.stdout


def image_mime(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "image/jpeg"  # extensionless bucket URLs are usually jpeg


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
        print(f"  ERROR: Anthropic API failed for {image_path.name}: {exc}", file=sys.stderr)
        return ""
    if msg.stop_reason == "refusal":
        print(f"  ERROR: Claude declined {image_path.name}; add alt by hand", file=sys.stderr)
        return ""
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
        print(f"  ERROR: {api_url} failed for {image_path.name}: {exc}", file=sys.stderr)
        return ""


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
    alt = alt.replace('"', "&quot;")
    if ALT_RE.search(old):
        return ALT_RE.sub(f'alt="{alt}"', old, count=1)
    body = old[:-1].rstrip()
    close = "/>" if body.endswith("/") else ">"
    return body.rstrip("/").rstrip() + f' alt="{alt}"' + close


def patch(entry: dict, alt: str) -> None:
    """Rewrite the matched image with alt text (first occurrence only)."""
    text = entry["file"].read_text(encoding="utf-8", errors="replace")
    new = patched_tag(entry["match"], entry["type"], alt)
    entry["file"].write_text(text.replace(entry["match"], new, 1), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate alt text for images missing it.")
    parser.add_argument("site", type=Path, help="Site directory to scan, e.g. plastercast")
    parser.add_argument("--apply", action="store_true", help="Patch files in place (default: dry run)")
    parser.add_argument("--list", action="store_true", help="Only list flagged images; no model calls")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N generated alts (0 = no limit)")
    parser.add_argument("--strict", action="store_true", help="Also flag short or duplicated alt text")
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
    args = parser.parse_args()
    if not args.site.is_dir():
        sys.exit(f"ERROR: {args.site} is not a directory")
    if args.backend == "openai" and not args.model:
        sys.exit("ERROR: --backend openai needs --model, e.g. --model qwen2.5vl:7b")
    args.model = args.model or "claude-sonnet-5"

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
        key = (image_key(img), existing)
        if key not in cache:
            if args.limit and len(cache) >= args.limit:
                print("    (limit reached)")
                break
            local = fetch(img, fetch_dir) if isinstance(img, str) else img
            cache[key] = generate_alt_text(local, existing, args) if local else ""
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
    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Model calls: {len(cache)}")
    if not args.apply and processed:
        print("Run with --apply to write changes to files.")


if __name__ == "__main__":
    main()
