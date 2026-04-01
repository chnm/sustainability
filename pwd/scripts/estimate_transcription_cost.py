#!/usr/bin/env python3
"""
Estimate the cost of a full AI transcription run.

Samples a set of document images to measure average size, then extrapolates
token counts and costs across the full corpus.

Usage:
    uv run python3 scripts/estimate_transcription_cost.py
    uv run python3 scripts/estimate_transcription_cost.py --samples 20
"""

import argparse
import base64
import glob
import json
import random
import sys
from pathlib import Path
from urllib.request import urlopen, Request

HUGO_DIR = Path(__file__).parent.parent
CONTENT_DIR = HUGO_DIR / "content" / "document"
MEDIA_MAP_PATH = HUGO_DIR / "data" / "media_map.json"
MEDIA_BASE_URL = "https://obj.rrchnm.org/wardepartmentpapers.org"

# Pricing per million tokens (as of 2025)
# https://docs.anthropic.com/en/docs/about-claude/models
MODELS = {
    "claude-sonnet-4-6": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
    },
    "claude-haiku-4-5": {
        "input_per_m": 0.80,
        "output_per_m": 4.00,
    },
    "claude-opus-4-6": {
        "input_per_m": 15.00,
        "output_per_m": 75.00,
    },
}

# Claude image token estimation:
# Images are resized to fit within 1568px on the longest side.
# Token cost depends on image dimensions after resizing.
# Rough formula from Anthropic docs: tokens ≈ (width * height) / 750
# A typical document scan at 1568x1200 ≈ ~2,510 tokens per image.
# We'll measure actual sizes from samples to be more precise.


def load_media_map():
    with open(MEDIA_MAP_PATH) as f:
        return json.load(f)


def parse_document_frontmatter(filepath):
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return None, None
    end = content.index("---", 3)
    frontmatter = content[3:end]
    omeka_id = None
    image_id = None
    for line in frontmatter.split("\n"):
        if line.startswith("omeka_id:"):
            omeka_id = line.split(":", 1)[1].strip()
        elif line.startswith("image_id:"):
            image_id = line.split(":", 1)[1].strip()
    return omeka_id, image_id


def get_image_size_bytes(filename):
    """Fetch just the Content-Length header for an image without downloading."""
    url = f"{MEDIA_BASE_URL}/files/original/{filename}"
    req = Request(url, method="HEAD", headers={"User-Agent": "PWD-Estimate/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            length = resp.headers.get("Content-Length")
            return int(length) if length else None
    except Exception:
        return None


def estimate_image_tokens(width=1200, height=1568):
    """Estimate tokens for an image using Anthropic's formula.

    Images are scaled to fit in 1568x1568. A typical document scan
    uses about (w*h)/750 tokens. We use a conservative estimate based
    on typical document dimensions.
    """
    return (width * height) // 750


def main():
    parser = argparse.ArgumentParser(
        description="Estimate cost of full transcription run"
    )
    parser.add_argument(
        "--samples", type=int, default=10,
        help="Number of documents to sample for size estimation (default: 10)"
    )
    args = parser.parse_args()

    media_map = load_media_map()

    # Collect unique image_ids referenced by documents
    # (many documents share image_ids, so we transcribe per unique image_id)
    print("Scanning documents...")
    doc_files = sorted(glob.glob(str(CONTENT_DIR / "*.md")))
    image_id_to_docs = {}
    total_docs_with_images = 0

    for doc_path in doc_files:
        omeka_id, image_id = parse_document_frontmatter(doc_path)
        if not omeka_id or not image_id:
            continue
        image_files = media_map.get(str(image_id), [])
        if image_files:
            total_docs_with_images += 1
            image_id_to_docs.setdefault(image_id, []).append(omeka_id)

    # Build unique transcription jobs (one per image_id)
    from collections import Counter
    jobs = []
    for image_id, doc_ids in image_id_to_docs.items():
        image_files = media_map.get(str(image_id), [])
        jobs.append((image_id, doc_ids, image_files))

    total_unique_ids = len(jobs)
    total_images = sum(len(j[2]) for j in jobs)
    shared_ids = sum(1 for j in jobs if len(j[1]) > 1)

    print(f"Documents with images: {total_docs_with_images:,}")
    print(f"Unique image_ids to transcribe: {total_unique_ids:,}")
    print(f"  (of which {shared_ids:,} are shared across multiple docs)")
    print(f"Total unique image files: {total_images:,}")

    # Distribution
    page_dist = Counter(len(j[2]) for j in jobs)
    print(f"\nPages-per-image_id distribution:")
    for n in sorted(page_dist.keys())[:8]:
        print(f"  {n:>3} page(s): {page_dist[n]:>6,} image_ids")
    over8 = sum(v for k, v in page_dist.items() if k > 8)
    if over8:
        print(f"   9+ page(s): {over8:>6,} image_ids")
    print(f"  Max pages:   {max(page_dist.keys())}")

    avg_pages = total_images / total_unique_ids
    print(f"  Avg pages:   {avg_pages:.1f}")

    # Sample image file sizes
    print(f"\nSampling {args.samples} random images for size estimation...")
    all_filenames = [f for j in jobs for f in j[2]]
    sample_files = random.sample(all_filenames, min(args.samples, len(all_filenames)))

    sizes = []
    for filename in sample_files:
        size = get_image_size_bytes(filename)
        if size:
            sizes.append(size)
            print(f"  {filename[:16]}... {size / 1024:.0f} KB")

    if not sizes:
        print("Error: couldn't fetch any image sizes")
        sys.exit(1)

    avg_size_kb = sum(sizes) / len(sizes) / 1024
    print(f"\n  Average image size: {avg_size_kb:.0f} KB")

    # Token estimation
    # System prompt tokens (~500 tokens)
    system_tokens = 500
    # User prompt tokens (~30 tokens)
    user_prompt_tokens = 30
    # Image tokens: Anthropic charges ~2,500 tokens per typical document image
    # (1568x1200 at the standard scaling)
    tokens_per_image = estimate_image_tokens()
    # Output tokens: estimate ~500 tokens per page for handwritten transcription
    output_tokens_per_page = 500

    print(f"\n{'=' * 60}")
    print("TOKEN ESTIMATES")
    print(f"{'=' * 60}")
    print(f"  System prompt:       ~{system_tokens:,} tokens (per request)")
    print(f"  Image tokens:        ~{tokens_per_image:,} tokens (per image)")
    print(f"  User prompt:         ~{user_prompt_tokens:,} tokens (per request)")
    print(f"  Output estimate:     ~{output_tokens_per_page:,} tokens (per page)")
    print()

    # For image_ids with many pages, we cap at 50 (script default)
    max_pages = 50
    capped_images = sum(min(len(j[2]), max_pages) for j in jobs)
    capped_note = ""
    if capped_images < total_images:
        capped_note = f" (capped from {total_images:,} at {max_pages} pages/job)"

    total_input_tokens = (
        total_unique_ids * (system_tokens + user_prompt_tokens)
        + capped_images * tokens_per_image
    )
    total_output_tokens = capped_images * output_tokens_per_page

    print(f"  Total images to process: {capped_images:,}{capped_note}")
    print(f"  Total input tokens:  ~{total_input_tokens:,.0f}")
    print(f"  Total output tokens: ~{total_output_tokens:,.0f}")

    print(f"\n{'=' * 60}")
    print("COST ESTIMATES")
    print(f"{'=' * 60}")
    print(f"  {'Model':<20} {'Input':>10} {'Output':>10} {'Total':>10}")
    print(f"  {'-' * 50}")
    for model_name, prices in MODELS.items():
        input_cost = (total_input_tokens / 1_000_000) * prices["input_per_m"]
        output_cost = (total_output_tokens / 1_000_000) * prices["output_per_m"]
        total_cost = input_cost + output_cost
        print(f"  {model_name:<20} ${input_cost:>8,.2f} ${output_cost:>8,.2f} ${total_cost:>8,.2f}")

    # Batch API discount
    print(f"\n  With Batch API (50% discount):")
    print(f"  {'-' * 50}")
    for model_name, prices in MODELS.items():
        input_cost = (total_input_tokens / 1_000_000) * prices["input_per_m"] * 0.5
        output_cost = (total_output_tokens / 1_000_000) * prices["output_per_m"] * 0.5
        total_cost = input_cost + output_cost
        print(f"  {model_name:<20} ${input_cost:>8,.2f} ${output_cost:>8,.2f} ${total_cost:>8,.2f}")

    # Time estimate
    avg_seconds = 10  # ~10s per job based on test
    total_hours = (total_unique_ids * avg_seconds) / 3600
    print(f"\n  Time estimate (sequential): ~{total_hours:.0f} hours")
    print(f"  Time estimate (Batch API):  ~24 hours (async)")


if __name__ == "__main__":
    main()
