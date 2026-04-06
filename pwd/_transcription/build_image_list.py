#!/usr/bin/env python3
"""
Extract image filenames from Hugo document frontmatter.

Produces images.tsv with one line per document:
    omeka_id<TAB>image1.jpg,image2.jpg,...

Only includes documents that have a non-empty images list.

Usage:
    python3 build_image_list.py
    python3 build_image_list.py --content-dir ../content/document
    python3 build_image_list.py -o images.tsv
"""

import argparse
import glob
import os
import re
from pathlib import Path


def parse_frontmatter(filepath):
    """Extract omeka_id and images list from Hugo markdown frontmatter.

    Uses simple regex parsing to avoid external dependencies (no yaml/yq).
    """
    with open(filepath) as f:
        content = f.read(8192)  # frontmatter is near the top
    if not content.startswith("---"):
        return None
    try:
        end = content.index("---", 3)
    except ValueError:
        return None
    fm = content[3:end]

    # Extract omeka_id
    m = re.search(r'^omeka_id:\s*(\S+)', fm, re.MULTILINE)
    omeka_id = m.group(1).strip("'\"") if m else None

    # Extract images list (YAML list items following "images:")
    images = []
    m = re.search(r'^images:', fm, re.MULTILINE)
    if m:
        rest = fm[m.end():]
        # Skip "images: []" (empty list)
        if rest.lstrip().startswith("[]"):
            pass
        else:
            for line in rest.splitlines():
                stripped = line.strip()
                if stripped.startswith("- "):
                    images.append(stripped[2:].strip())
                elif stripped and not stripped.startswith("#"):
                    break  # next key

    return {"omeka_id": omeka_id, "images": images}


def main():
    parser = argparse.ArgumentParser(
        description="Build image manifest from Hugo document frontmatter"
    )
    parser.add_argument(
        "--content-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "content", "document"),
        help="Path to content/document/",
    )
    parser.add_argument(
        "-o", "--output",
        default=os.path.join(os.path.dirname(__file__), "images.tsv"),
        help="Output manifest file (default: _transcription/images.tsv)",
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

            fm = parse_frontmatter(doc_path)
            if not fm:
                continue

            omeka_id = fm.get("omeka_id")
            if not omeka_id:
                continue

            images = fm.get("images", [])
            if not images:
                continue

            out.write(f"{omeka_id}\t{','.join(images)}\n")
            total_docs += 1
            total_images += len(images)

    print(f"Wrote {args.output}")
    print(f"  Documents with images: {total_docs}")
    print(f"  Total image files: {total_images}")


if __name__ == "__main__":
    main()
