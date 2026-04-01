#!/usr/bin/env python3
"""Extract news/blog posts from wget'd WordPress HTML into Hugo content files."""

import glob
import os
import re
import sys
from datetime import datetime

from bs4 import BeautifulSoup, Comment
import yaml

NEWS_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "wardepartmentpapers.org", "news",
)
CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content", "news")

# Map category slugs from article classes to display names
CATEGORY_MAP = {
    "documents": "Document Guides",
    "getting-started": "Getting Started",
    "interviews": "Interviews",
    "monthly-updates": "Monthly Updates",
    "news": "News",
    "transcription": "Transcription",
    "uncategorized": "Uncategorized",
}


def fix_internal_links(html):
    """Rewrite internal links from old formats to Hugo paths."""
    # Omeka item links: /s/home/item/NNN -> /item/NNN/
    html = re.sub(r'href="/?s/home/item/(\d+)"', r'href="/item/\1/"', html)
    # Old PHP document links: /document.php?id=NNN -> /item/NNN/
    html = re.sub(r'href="/?document\.php\?id=(\d+)"', r'href="/item/\1/"', html)
    # Old PHP index links: /index.php -> /
    html = re.sub(r'href="/?index\.php"', r'href="/"', html)
    # Omeka page links: /s/home/page/slug -> /slug/
    html = re.sub(r'href="/?s/home/page/([^"]+)"', r'href="/\1/"', html)
    # Strip wardepartmentpapers.org domain from absolute URLs
    html = re.sub(
        r'href="https?://(?:www\.)?wardepartmentpapers\.org(/[^"]*)"',
        r'href="\1"',
        html,
    )
    return html


def parse_date(date_str):
    """Parse WordPress date string to datetime.

    Format: "July 3, 2019 at 3:00 pm"
    """
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y at %I:%M %p")
    except ValueError:
        # Try without leading zero on day
        try:
            return datetime.strptime(date_str.strip(), "%B %d, %Y at %I:%M %p")
        except ValueError:
            print(f"  WARNING: Could not parse date: {date_str}", file=sys.stderr)
            return None


def extract_post(filepath):
    """Extract a single news post from a WordPress HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    article = soup.find("article")
    if not article:
        return None

    # Post ID from article id attribute (e.g., "post-2114")
    article_id = article.get("id", "")
    post_id = None
    if article_id.startswith("post-"):
        try:
            post_id = int(article_id.replace("post-", ""))
        except ValueError:
            pass

    # Categories and tags from article classes
    classes = article.get("class", [])
    categories = []
    tags = []
    for cls in classes:
        if cls.startswith("category-"):
            cat_slug = cls.replace("category-", "")
            categories.append(CATEGORY_MAP.get(cat_slug, cat_slug.replace("-", " ").title()))
        elif cls.startswith("tag-"):
            tags.append(cls.replace("tag-", ""))

    # Title from second <h2> (first is "News" heading)
    h2_tags = article.find_all("h2")
    title = None
    for h2 in h2_tags:
        a_tag = h2.find("a")
        if a_tag:
            title = a_tag.get_text(strip=True)
            break
    if not title:
        title = "[Untitled]"

    # Author from <span class="author">
    author = None
    author_span = article.find("span", class_="author")
    if author_span:
        a_tag = author_span.find("a")
        if a_tag:
            author = a_tag.get_text(strip=True)

    # Date from <span class="date">
    date = None
    date_span = article.find("span", class_="date")
    if date_span:
        date = parse_date(date_span.get_text())

    # Slug from <body> last class
    body_tag = soup.find("body")
    slug = None
    if body_tag:
        body_classes = body_tag.get("class", [])
        if body_classes:
            slug = body_classes[-1]

    # Body content: everything after post-meta div
    post_meta = article.find("div", class_="post-meta")
    body_parts = []
    if post_meta:
        # Get all siblings after post-meta
        for sibling in post_meta.next_siblings:
            # Skip Comment nodes (BeautifulSoup Comment type)
            if isinstance(sibling, Comment):
                continue
            text = str(sibling).strip()
            if text:
                body_parts.append(text)

    body_html = "\n".join(body_parts).strip()
    body_html = fix_internal_links(body_html)

    return {
        "title": title,
        "date": date,
        "author": author,
        "categories": categories,
        "tags": tags,
        "slug": slug,
        "wp_post_id": post_id,
        "body": body_html,
    }


def write_post(post):
    """Write a single news post as a Hugo content file."""
    slug = post["slug"] or f"post-{post['wp_post_id']}"
    output_path = os.path.join(CONTENT_DIR, f"{slug}.md")

    fm = {
        "title": post["title"],
        "type": "news",
    }

    if post["date"]:
        fm["date"] = post["date"].strftime("%Y-%m-%dT%H:%M:%S")

    if post["author"]:
        fm["author"] = post["author"]

    if post["categories"]:
        fm["categories"] = post["categories"]

    if post["tags"]:
        fm["tags"] = post["tags"]

    if post["wp_post_id"]:
        fm["wp_post_id"] = post["wp_post_id"]
        fm["aliases"] = [f"/news/?p={post['wp_post_id']}"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml.dump(fm, default_flow_style=False, allow_unicode=True, width=200))
        f.write("---\n\n")
        f.write(post["body"])
        f.write("\n")

    return slug


def main():
    os.makedirs(CONTENT_DIR, exist_ok=True)

    # Find individual post files (index.html?p=ID.html)
    pattern = os.path.join(NEWS_SOURCE_DIR, "index.html?p=*.html")
    post_files = sorted(glob.glob(pattern))
    print(f"Found {len(post_files)} post files in {NEWS_SOURCE_DIR}")

    if not post_files:
        print("No post files found. Check the source directory path.", file=sys.stderr)
        sys.exit(1)

    extracted = 0
    errors = 0

    for filepath in post_files:
        filename = os.path.basename(filepath)
        try:
            post = extract_post(filepath)
            if post is None:
                print(f"  SKIP {filename}: no <article> found")
                continue

            slug = write_post(post)
            extracted += 1
            print(f"  {slug}.md — {post['title']}")

        except Exception as e:
            errors += 1
            print(f"  ERROR {filename}: {e}", file=sys.stderr)

    print(f"\nDone! Extracted {extracted} posts to {CONTENT_DIR} ({errors} errors)")


if __name__ == "__main__":
    main()
