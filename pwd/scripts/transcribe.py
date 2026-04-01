#!/usr/bin/env python3
"""
AI transcription of Papers of the War Department document images.

Uses Claude to transcribe handwritten 18th-century document images.
Images are fetched from MinIO and sent to the API as URLs.

Usage:
    # Test a single document (prints to stdout)
    uv run python3 scripts/transcribe.py --test 38299

    # Transcribe a batch of documents (saves to data/transcriptions_ai.json)
    uv run python3 scripts/transcribe.py --batch --limit 10

    # Resume a batch run (skips already-transcribed documents)
    uv run python3 scripts/transcribe.py --batch --resume

    # Use a specific model
    uv run python3 scripts/transcribe.py --test 38299 --model claude-sonnet-4-6
"""

import argparse
import base64
import glob
import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

import anthropic
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Paths relative to hugo/ directory
HUGO_DIR = Path(__file__).parent.parent
CONTENT_DIR = HUGO_DIR / "content" / "document"
OUTPUT_PATH = HUGO_DIR / "data" / "transcriptions_ai.json"

MEDIA_BASE_URL = "https://obj.rrchnm.org/wardepartmentpapers.org"

SYSTEM_PROMPT = """\
You are an expert paleographer and archival transcriptionist specializing in \
18th-century American handwritten documents. You are transcribing documents \
from the Papers of the War Department, 1784-1800, a collection of \
correspondence and records from the early United States federal government.

Your task is to produce a faithful, accurate transcription of the handwritten \
text in the provided image(s). Follow these guidelines, which are based on \
the project's human transcription standards.

## General

- Transcribe the document exactly as it appears. Do not add commentary, \
notes, or metadata — only the transcribed text.
- Only transcribe the document in the record you are working from. Some \
documents are part of letter books, so you may see many pages or many \
letters per page. Only transcribe the letter or document that is the \
primary subject of the image(s).
- Record any marginalia or notes written on the document, including postal \
notations and administrative notes, in [brackets].
- If the document indicates it is a draft, note this. Include notation in \
[brackets] for documents marked "Private", "Confidential", or "Copy" by \
the author.

## Spelling

- Preserve the spelling of the document, even if words are misspelled. \
Spelling can be widely variable, even among documents written by the same \
person. Do NOT modernize or correct spelling.

## Punctuation

- Preserve punctuation of the document, even if it seems wrong.
- Preserve capitalization exactly as written.
- Indicate strikethroughs using [strikethrough: text].
- Indicate underlined text using [underline: text].

## Formatting

- Render superscript characters using HTML <sup> tags, e.g., \
May 19<sup>th</sup>, 1793.
- To indicate a paragraph break, use two line breaks (a blank line) \
between paragraphs, exactly as in the original.
- Note any illustrations, charts, seals, or symbols that cannot be \
reproduced in [brackets], e.g., [seal] or [illustration of a map].

## Illegible text

- If you cannot make out a word, include [undecipherable] in its place.
- If you can partially read a word, provide your best reading with a \
note: [undecipherable: probable reading]. Never guess or fabricate text.

## Multi-page documents

- When multiple page images are provided, transcribe each page in order \
as a continuous document. Do not insert page markers or separators.

## Output format

- Return ONLY the transcription text. Do not include any commentary, \
analysis, metadata, or explanation.\
"""


def load_existing_transcriptions():
    """Load existing AI transcriptions if the file exists."""
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {}


def save_transcriptions(transcriptions):
    """Save AI transcriptions to JSON."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(transcriptions, f, indent=2, ensure_ascii=False)


def parse_document_frontmatter(filepath):
    """Extract omeka_id and images list from a document's YAML frontmatter.

    Returns:
        (omeka_id, image_files) where image_files is a list of filename strings.
    """
    with open(filepath) as f:
        content = f.read()

    # Simple YAML frontmatter parser (between --- delimiters)
    if not content.startswith("---"):
        return None, []

    end = content.index("---", 3)
    frontmatter = content[3:end]

    omeka_id = None
    image_files = []
    in_images = False
    for line in frontmatter.split("\n"):
        if line.startswith("omeka_id:"):
            omeka_id = line.split(":", 1)[1].strip()
            in_images = False
        elif line.startswith("images:"):
            in_images = True
            # Handle inline empty list: `images: []`
            val = line.split(":", 1)[1].strip()
            if val == "[]":
                in_images = False
        elif in_images and line.startswith("- "):
            image_files.append(line[2:].strip())
        elif in_images and not line.startswith("- ") and line.strip():
            # We've left the images list
            in_images = False

    return omeka_id, image_files


def get_document_content(filepath):
    """Extract the markdown body (human transcription) from a document."""
    with open(filepath) as f:
        content = f.read()

    if not content.startswith("---"):
        return ""

    end = content.index("---", 3) + 3
    body = content[end:].strip()
    return body


def fetch_image_as_base64(url):
    """Fetch an image from URL and return as base64-encoded string."""
    req = Request(url, headers={"User-Agent": "PWD-Transcribe/1.0"})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    return base64.standard_b64encode(data).decode("utf-8")


def build_image_url(filename, size="original"):
    """Build MinIO URL for an image file."""
    return f"{MEDIA_BASE_URL}/files/{size}/{filename}"


def transcribe_document(client, image_filenames, model="claude-sonnet-4-6",
                        max_pages=50):
    """Send document images to Claude for transcription.

    Args:
        client: Anthropic client
        image_filenames: List of image filename hashes
        model: Model to use
        max_pages: Max pages to transcribe (to control costs on huge docs)

    Returns:
        Transcription text string
    """
    filenames = image_filenames[:max_pages]
    if len(image_filenames) > max_pages:
        print(f"  Warning: document has {len(image_filenames)} pages, "
              f"truncating to {max_pages}")

    # Build content blocks with images
    content = []
    for i, filename in enumerate(filenames):
        url = build_image_url(filename, "original")
        print(f"  Fetching page {i + 1}/{len(filenames)}: {filename[:12]}...")

        try:
            img_data = fetch_image_as_base64(url)
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            continue

        # Determine media type from extension
        ext = filename.rsplit(".", 1)[-1].lower()
        media_type = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }.get(ext, "image/jpeg")

        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": img_data,
            },
        })

    if not content:
        return None

    # Add text prompt after images
    if len(filenames) == 1:
        content.append({
            "type": "text",
            "text": "Please transcribe the handwritten text in this document image.",
        })
    else:
        content.append({
            "type": "text",
            "text": (f"This document consists of {len(filenames)} page(s). "
                     "Please transcribe all pages in order as a continuous "
                     "document."),
        })

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    # Extract text from response
    text_parts = [block.text for block in response.content if block.type == "text"]
    transcription = "\n".join(text_parts)

    return transcription


def test_document(omeka_id, model="claude-sonnet-4-6"):
    """Transcribe a single document and print results for review."""
    client = anthropic.Anthropic()

    # Find the document file
    doc_path = CONTENT_DIR / f"{omeka_id}.md"
    if not doc_path.exists():
        print(f"Error: document {omeka_id} not found at {doc_path}")
        sys.exit(1)

    omeka_id_str, image_files = parse_document_frontmatter(doc_path)
    if not image_files:
        print(f"Error: document {omeka_id} has no images in frontmatter")
        sys.exit(1)

    print(f"Document: {omeka_id}")
    print(f"Pages: {len(image_files)}")
    print(f"Model: {model}")
    print(f"{'=' * 60}")

    # Get human transcription for comparison
    human_text = get_document_content(doc_path)

    # Run AI transcription
    print(f"\nTranscribing...")
    start = time.time()
    ai_text = transcribe_document(client, image_files, model=model)
    elapsed = time.time() - start

    print(f"\nCompleted in {elapsed:.1f}s")
    print(f"\n{'=' * 60}")
    print("AI TRANSCRIPTION:")
    print(f"{'=' * 60}")
    print(ai_text)

    if human_text:
        print(f"\n{'=' * 60}")
        print("HUMAN TRANSCRIPTION (for comparison):")
        print(f"{'=' * 60}")
        print(human_text)
    else:
        print(f"\n(No human transcription available for comparison)")

    return ai_text


def batch_transcribe(model="claude-sonnet-4-6", limit=None,
                     resume=False, max_pages=50):
    """Transcribe all documents with images."""
    client = anthropic.Anthropic()

    # Load existing transcriptions if resuming
    transcriptions = load_existing_transcriptions() if resume else {}
    skipped = 0

    # Collect all documents with images
    doc_files = sorted(glob.glob(str(CONTENT_DIR / "*.md")))
    docs_to_process = []

    for doc_path in doc_files:
        omeka_id, image_files = parse_document_frontmatter(doc_path)
        if not omeka_id or not image_files:
            continue

        if resume and omeka_id in transcriptions:
            skipped += 1
            continue

        docs_to_process.append((omeka_id, image_files))

    if limit:
        docs_to_process = docs_to_process[:limit]

    total = len(docs_to_process)
    print(f"Documents to transcribe: {total}")
    if skipped:
        print(f"Skipped (already transcribed): {skipped}")
    print(f"Model: {model}")
    print(f"Max pages per document: {max_pages}")
    print()

    for i, (omeka_id, image_files) in enumerate(docs_to_process):
        print(f"[{i + 1}/{total}] Document {omeka_id} "
              f"({len(image_files)} page(s))")

        try:
            ai_text = transcribe_document(
                client, image_files, model=model, max_pages=max_pages
            )
            if ai_text:
                transcriptions[omeka_id] = ai_text
                # Save after each document so we don't lose progress
                save_transcriptions(transcriptions)
                print(f"  Saved ({len(ai_text)} chars)")
            else:
                print(f"  No transcription returned")
        except anthropic.RateLimitError:
            print(f"  Rate limited — waiting 60s...")
            time.sleep(60)
            # Retry once
            try:
                ai_text = transcribe_document(
                    client, image_files, model=model, max_pages=max_pages
                )
                if ai_text:
                    transcriptions[omeka_id] = ai_text
                    save_transcriptions(transcriptions)
                    print(f"  Saved ({len(ai_text)} chars)")
            except Exception as e:
                print(f"  Retry failed: {e}")
        except Exception as e:
            print(f"  Error: {e}")

        # Small delay between documents to be polite
        time.sleep(0.5)

    print(f"\nDone. {len(transcriptions)} total transcriptions saved to "
          f"{OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description="AI transcription of War Department document images"
    )
    parser.add_argument(
        "--test", metavar="OMEKA_ID",
        help="Transcribe a single document and print results"
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Transcribe all documents with images"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip already-transcribed documents"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maximum number of documents to transcribe"
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6",
        help="Claude model to use (default: claude-sonnet-4-6)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=50,
        help="Maximum pages per document (default: 50)"
    )

    args = parser.parse_args()

    if args.test:
        test_document(args.test, model=args.model)
    elif args.batch:
        batch_transcribe(
            model=args.model,
            limit=args.limit,
            resume=args.resume,
            max_pages=args.max_pages,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
