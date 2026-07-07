#!/usr/bin/env -S uv run python3
"""
Transcribe War Department document images using `claude -p`.

Downloads each document's images from object storage, passes them to
`claude -p` with the transcription prompt, saves the result, then
deletes the local image copies. Tracks progress in a cache file so
runs can be interrupted and resumed.

Usage:
    # First, build the image manifest (from project root):
    python3 _transcription/build_image_list.py --content-dir content/document

    # Transcribe all documents (resumes automatically):
    python3 _transcription/transcribe.py

    # Limit to N documents:
    python3 _transcription/transcribe.py --limit 10

    # Start fresh (ignore cache):
    python3 _transcription/transcribe.py --no-resume

    # Use a different model:
    python3 _transcription/transcribe.py --model claude-sonnet-4-6
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen, Request


SCRIPT_DIR = Path(__file__).parent
MANIFEST = SCRIPT_DIR / "images.tsv"
PROMPT_FILE = SCRIPT_DIR / "prompt.txt"
CACHE_FILE = SCRIPT_DIR / ".transcribe_progress"
OUTPUT_FILE = SCRIPT_DIR / "transcriptions.json"

MEDIA_BASE_URL = "https://obj.rrchnm.org/wardepartmentpapers.org/files/original"


def load_cache():
    """Load set of already-transcribed omeka_ids."""
    if CACHE_FILE.exists():
        return set(CACHE_FILE.read_text().strip().splitlines())
    return set()


def append_cache(omeka_id):
    """Mark a document as done in the cache."""
    with open(CACHE_FILE, "a") as f:
        f.write(f"{omeka_id}\n")


def load_output():
    """Load existing transcriptions JSON."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {}


def save_output(transcriptions):
    """Save transcriptions JSON."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(transcriptions, f, indent=2, ensure_ascii=False)


def download_image(filename, dest_dir):
    """Download an image from object storage. Returns local path."""
    url = f"{MEDIA_BASE_URL}/{filename}"
    local_path = os.path.join(dest_dir, filename)
    req = Request(url, headers={"User-Agent": "PWD-Transcribe/1.0"})
    try:
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(local_path, "wb") as f:
            f.write(data)
        return local_path
    except Exception as e:
        print(f"    Error downloading {filename}: {e}")
        return None


def transcribe_images(image_paths, model="claude-sonnet-4-6"):
    """Run `claude -p` with the prompt and image files. Returns transcription text."""
    prompt = PROMPT_FILE.read_text() + "\n\nPlease read and transcribe the following image files:\n"
    for path in image_paths:
        prompt += f"- {path}\n"

    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--allowedTools", "Read",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"    claude error (exit {result.returncode}): {result.stderr[:200]}")
        return None

    return result.stdout.strip()


def load_manifest():
    """Read the image manifest TSV. Returns list of (omeka_id, [filenames])."""
    if not MANIFEST.exists():
        print(f"Error: manifest not found at {MANIFEST}")
        print("Run build_image_list.py first.")
        sys.exit(1)

    entries = []
    with open(MANIFEST) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            omeka_id, images_str = line.split("\t", 1)
            images = images_str.split(",")
            entries.append((omeka_id, images))
    return entries


def load_ids_file(path):
    """Load a set of omeka_ids from a file (one per line, blanks ignored)."""
    text = Path(path).read_text()
    return {line.strip() for line in text.splitlines() if line.strip()}


def select_todo(manifest, done, max_pages, ids_filter=None):
    """Select the (omeka_id, [images]) documents to transcribe.

    manifest: list of (omeka_id, [images]).

    When ids_filter is a set: select exactly those ids present in the manifest,
    forcing re-transcription (ignore `done`), still respecting max_pages. Ids in
    ids_filter but not in the manifest are simply absent from the result.

    When ids_filter is None: skip ids already in `done`, respect max_pages.

    Manifest order is preserved.
    """
    todo = []
    for oid, imgs in manifest:
        if len(imgs) > max_pages:
            continue
        if ids_filter is not None:
            if oid in ids_filter:
                todo.append((oid, imgs))
        elif oid not in done:
            todo.append((oid, imgs))
    return todo


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe War Department documents via claude -p"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Max documents to transcribe",
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Start fresh, ignoring the progress cache",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6",
        help="Claude model (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=50,
        help="Max pages per document (default: 50)",
    )
    parser.add_argument(
        "--ids-file", default=None,
        help="Re-transcribe only these omeka_ids (one per line), forcing "
             "re-transcription even if already done.",
    )
    args = parser.parse_args()

    manifest = load_manifest()

    ids_filter = load_ids_file(args.ids_file) if args.ids_file else None

    # In ids-file (forced) mode, always preserve existing transcriptions so
    # untargeted entries survive and only the targeted ids get overwritten.
    if ids_filter is not None:
        done = load_cache()
        transcriptions = load_output()
    else:
        done = set() if args.no_resume else load_cache()
        transcriptions = {} if args.no_resume else load_output()

    todo = select_todo(manifest, done, args.max_pages, ids_filter=ids_filter)
    if args.limit:
        todo = todo[:args.limit]

    skipped_big = len([oid for oid, imgs in manifest if len(imgs) > args.max_pages])
    print(f"Manifest: {len(manifest)} documents")
    if ids_filter is not None:
        manifest_ids = {oid for oid, _ in manifest}
        found = ids_filter & manifest_ids
        missing = ids_filter - manifest_ids
        print(f"Mode: targeted re-transcription via --ids-file ({args.ids_file})")
        print(f"IDs requested: {len(ids_filter)}")
        print(f"IDs found in manifest: {len(found)}")
        if missing:
            print(f"IDs listed but NOT in manifest: {len(missing)}")
        print(f"Skipped (>{args.max_pages} pages): "
              f"{len(found) - len(todo) if args.limit is None else 'n/a (limited)'}")
    else:
        skipped_done = len([oid for oid, _ in manifest if oid in done])
        print(f"Already done: {skipped_done}")
        print(f"Skipped (>{args.max_pages} pages): {skipped_big}")
    print(f"To transcribe: {len(todo)}")
    print(f"Model: {args.model}")
    print()

    for i, (omeka_id, image_files) in enumerate(todo):
        image_files = image_files[:args.max_pages]
        print(f"[{i + 1}/{len(todo)}] Document {omeka_id} ({len(image_files)} page(s))")

        # Download images to a temp directory
        with tempfile.TemporaryDirectory(prefix="pwd_transcribe_") as tmpdir:
            local_paths = []
            for filename in image_files:
                print(f"    Downloading {filename[:16]}...")
                path = download_image(filename, tmpdir)
                if path:
                    local_paths.append(path)

            if not local_paths:
                print(f"    No images downloaded, skipping")
                continue

            # Transcribe
            print(f"    Transcribing with claude -p...")
            start = time.time()
            text = transcribe_images(local_paths, model=args.model)
            elapsed = time.time() - start

            if text:
                transcriptions[omeka_id] = text
                save_output(transcriptions)
                append_cache(omeka_id)
                print(f"    Done ({len(text)} chars, {elapsed:.1f}s)")
            else:
                print(f"    No transcription returned")

            # tempdir cleanup is automatic — images are deleted here

    print(f"\nFinished. {len(transcriptions)} transcriptions in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
