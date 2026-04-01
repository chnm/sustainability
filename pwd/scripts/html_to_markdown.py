#!/usr/bin/env python3
"""Convert HTML body content in editorial .md files to clean Markdown.

Targets the ~24 editorial pages in content/ that have HTML body content
from the Omeka S block layout system. Item files (content/item/*.md) are
skipped since they have no body content.

Usage:
    python3 scripts/html_to_markdown.py           # dry-run (shows diff)
    python3 scripts/html_to_markdown.py --write    # write changes
"""

import argparse
import glob
import os
import re

from markdownify import MarkdownConverter


class PWDConverter(MarkdownConverter):
    """Custom converter for PWD editorial pages."""

    def convert_div(self, el, text, parent_tags):
        # <div class="break opaque"></div> → horizontal rule
        classes = el.get("class", [])
        if "break" in classes and "opaque" in classes:
            return "\n\n---\n\n"
        # Other divs with inline styles (e.g., screenshot boxes) — just pass through content
        return text

    def convert_u(self, el, text, parent_tags):
        # <u>text</u> → just text (no markdown underline)
        return text

    def convert_sup(self, el, text, parent_tags):
        # Keep <sup> as HTML since markdown has no equivalent
        return f"<sup>{text}</sup>"

    def convert_iframe(self, el, text, parent_tags):
        # Keep iframes as-is
        attrs = []
        for k, v in el.attrs.items():
            if isinstance(v, list):
                v = " ".join(v)
            attrs.append(f'{k}="{v}"')
        attr_str = " ".join(attrs)
        return f"\n\n<iframe {attr_str}></iframe>\n\n"

    def convert_img(self, el, text, parent_tags):
        src = el.get("src", "")
        alt = el.get("alt", "")
        return f"![{alt}]({src})"


def convert_file(filepath, write=False):
    """Convert a single file's HTML body to markdown."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split front matter from body
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    front_matter = parts[1]
    body = parts[2]

    # Skip files with no meaningful body
    stripped_body = body.strip()
    if not stripped_body:
        return None

    # Skip files that don't contain HTML tags
    if not re.search(r"<[a-z]", stripped_body):
        return None

    # Convert HTML to markdown using custom converter
    converted = PWDConverter(
        heading_style="atx",
        bullets="-",
        strip=["br"],
        autolinks=False,
    ).convert(stripped_body)

    # Clean up the converted markdown
    # Fix HTML entities that markdownify might leave
    converted = converted.replace("&nbsp;", " ")
    converted = converted.replace("&ldquo;", "\u201c")
    converted = converted.replace("&rdquo;", "\u201d")
    converted = converted.replace("&lsquo;", "\u2018")
    converted = converted.replace("&rsquo;", "\u2019")
    converted = converted.replace("&amp;", "&")
    converted = converted.replace("&#39;", "'")
    converted = converted.replace("&quot;", '"')

    # Clean up excessive blank lines (3+ → 2)
    converted = re.sub(r"\n{3,}", "\n\n", converted)

    # Remove trailing whitespace on lines
    converted = "\n".join(line.rstrip() for line in converted.split("\n"))

    # Ensure single trailing newline
    converted = converted.strip() + "\n"

    new_content = f"---{front_matter}---\n\n{converted}"

    if new_content == content:
        return None

    if write:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return filepath
    else:
        return filepath


def main():
    parser = argparse.ArgumentParser(description="Convert HTML to Markdown in editorial pages")
    parser.add_argument("--write", action="store_true", help="Write changes (default: dry-run)")
    args = parser.parse_args()

    content_dir = os.path.join(os.path.dirname(__file__), "..", "content")
    content_dir = os.path.normpath(content_dir)

    # Only process top-level .md files (editorial pages), not item subdirectories
    files = sorted(glob.glob(os.path.join(content_dir, "*.md")))

    changed = []
    for filepath in files:
        result = convert_file(filepath, write=args.write)
        if result:
            changed.append(os.path.basename(result))

    if not changed:
        print("No files need conversion.")
        return

    action = "Converted" if args.write else "Would convert"
    print(f"{action} {len(changed)} file(s):")
    for name in changed:
        print(f"  {name}")

    if not args.write:
        print("\nRun with --write to apply changes.")


if __name__ == "__main__":
    main()
