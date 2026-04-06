#!/usr/bin/env -S uv run python3
"""
Extract image filenames from Hugo document frontmatter using yq.

Produces images.tsv with one line per document:
    omeka_id<TAB>image1.jpg,image2.jpg,...

Only includes documents that have a non-empty images list.

Usage:
    python3 build_image_list.py
    python3 build_image_list.py --content-dir ../hugo/content/document
    python3 build_image_list.py -o images.tsv
"""

import argparse
import glob
import os
import subprocess
from pathlib import Path

YQ = os.environ.get("YQ", "yq")


def get_frontmatter_field(filepath, expression):
    """Use yq to extract a field from YAML frontmatter."""
    result = subprocess.run(
        [YQ, "--front-matter=extract", expression, str(filepath)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Build image manifest from Hugo document frontmatter"
    )
    parser.add_argument(
        "--content-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "hugo", "content", "document"),
        help="Path to hugo/content/document/",
    )
    parser.add_argument(
        "-o", "--output",
        default=os.path.join(os.path.dirname(__file__), "images.tsv"),
        help="Output manifest file (default: transcription/images.tsv)",
    )
    args = parser.parse_args()

    content_dir = Path(args.content_dir).resolve()
    doc_files = sorted(glob.glob(str(content_dir / "*.md")))

    print(f"Scanning {len(doc_files)} documents in {content_dir}...")

    total_docs = 0
    total_images = 0

    with open(args.output, "w") as out:
        for i, doc_path in enumerate(doc_files):
            if (i + 1) % 5000 == 0:
                print(f"  Progress: {i + 1}/{len(doc_files)}...")

            omeka_id = get_frontmatter_field(doc_path, ".omeka_id")
            if not omeka_id or omeka_id == "null":
                continue

            images_raw = get_frontmatter_field(doc_path, ".images[]")
            if not images_raw or images_raw == "null":
                continue

            image_files = [line.strip() for line in images_raw.splitlines() if line.strip()]
            if not image_files:
                continue

            out.write(f"{omeka_id}\t{','.join(image_files)}\n")
            total_docs += 1
            total_images += len(image_files)

    print(f"Wrote {args.output}")
    print(f"  Documents with images: {total_docs}")
    print(f"  Total image files: {total_images}")


if __name__ == "__main__":
    main()
