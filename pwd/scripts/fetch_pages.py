#!/usr/bin/env python3
"""Fetch editorial pages from the Omeka S API and generate Hugo content files."""

import json
import os
import re
import requests
import yaml

API_BASE = "https://www.wardepartmentpapers.org/api"
CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")

# Pages that should be the homepage (skip generating a separate file)
SKIP_SLUGS = {"home", "collection"}


def fix_internal_links(html):
    """Fix internal links in HTML content to use Hugo paths."""
    # Fix links to other pages: /s/home/page/slug -> /slug/
    html = re.sub(r'href="/?s/home/page/([^"]+)"', r'href="/\1/"', html)
    # Fix links to items: /s/home/item/NNN -> /item/NNN/
    html = re.sub(r'href="/?s/home/item/(\d+)"', r'href="/item/\1/"', html)
    # Fix links to item sets: /s/home/item-set/NNN -> /item-set/NNN/
    html = re.sub(r'href="/?s/home/item-set/(\d+)"', r'href="/item-set/\1/"', html)
    # Strip wardepartmentpapers.org domain from URLs
    html = re.sub(
        r'href="https?://(?:www\.)?wardepartmentpapers\.org(/[^"]*)"',
        r'href="\1"',
        html,
    )
    # Fix relative page links (e.g., href="about.html" -> href="/about/")
    html = re.sub(
        r'href="([a-zA-Z][a-zA-Z0-9_-]+)\.html"',
        r'href="/\1/"',
        html,
    )
    return html


def process_blocks(blocks):
    """Convert Omeka page blocks to HTML content."""
    parts = []
    for block in blocks:
        layout = block.get("o:layout", "")
        data = block.get("o:data", {})

        if layout == "html":
            html = data.get("html", "")
            if html:
                divclass = data.get("divclass", "")
                if divclass:
                    parts.append(f'<div class="{divclass}">')
                parts.append(html)
                if divclass:
                    parts.append("</div>")

        elif layout == "lineBreak":
            break_type = data.get("break_type", "opaque")
            parts.append(f'<div class="break {break_type}"></div>')

        elif layout == "tableOfContents":
            # We'll skip TOC blocks - Hugo can generate these
            pass

        elif layout == "itemShowcase":
            # Item showcases reference specific items - we'll preserve references
            attachments = block.get("o:attachment", [])
            if attachments:
                parts.append('<div class="item-showcase">')
                for att in attachments:
                    item = att.get("o:item", {})
                    item_id = item.get("o:id", "")
                    caption = att.get("o:caption", "")
                    if item_id:
                        parts.append(f'<div class="item resource">')
                        parts.append(
                            f'<a href="/item/{item_id}/">View item {item_id}</a>'
                        )
                        if caption:
                            parts.append(f"<p>{caption}</p>")
                        parts.append("</div>")
                parts.append("</div>")

    return fix_internal_links("\n".join(parts))


def fetch_pages():
    """Fetch all site pages from the API."""
    print("Fetching site pages from API...")
    resp = requests.get(f"{API_BASE}/site_pages", params={"per_page": 100})
    resp.raise_for_status()
    pages = resp.json()
    print(f"Found {len(pages)} pages")
    return pages


def write_page(page):
    """Write a single page as a Hugo content file."""
    title = page.get("o:title", "Untitled")
    slug = page.get("o:slug", "untitled")
    page_id = page.get("o:id", 0)
    blocks = page.get("o:block", [])

    if slug in SKIP_SLUGS:
        print(f"  Skipping {slug} (homepage/special page)")
        return

    content = process_blocks(blocks)

    front_matter = {
        "title": title,
        "slug": slug,
        "type": "page",
        "omeka_page_id": page_id,
        "aliases": [f"/s/home/page/{slug}"],
    }

    output_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml.dump(front_matter, default_flow_style=False, allow_unicode=True))
        f.write("---\n\n")
        f.write(content)
        f.write("\n")

    print(f"  Written: {slug}.md ({len(blocks)} blocks)")


def main():
    pages = fetch_pages()

    os.makedirs(CONTENT_DIR, exist_ok=True)

    for page in pages:
        write_page(page)

    print(f"\nDone! Generated {len(pages)} page files in {CONTENT_DIR}")


if __name__ == "__main__":
    main()
