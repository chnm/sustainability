#!/usr/bin/env python3
"""Fetch news/blog posts from the flattened WordPress site and write Hugo content files.

The WordPress site at wardepartmentpapers.org/news/ is a static (wget'd) copy.
Posts are paginated at 1 per page: index.html?paged=1 through index.html?paged=239.
Each page contains a single <article> with post content.

This script fetches each paginated page, extracts the post, and writes it as a
Hugo content file. Posts already present (matched by wp_post_id) are skipped.

Usage:
    uv run --with beautifulsoup4,requests,pyyaml python3 scripts/fetch_news.py
"""

import os
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Comment
import yaml

BASE_URL = "https://wardepartmentpapers.org/news/"
CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content", "news")
MAX_PAGES = 300  # Upper bound; we'll stop when we get a 404 or no article
DELAY = 0.5  # Seconds between requests

CATEGORY_MAP = {
    "documents": "Document Guides",
    "getting-started": "Getting Started",
    "interviews": "Interviews",
    "monthly-updates": "Monthly Updates",
    "news": "News",
    "transcription": "Transcription",
    "uncategorized": "Uncategorized",
    "updates": "Updates",
    "guides": "Guides",
}


def fix_internal_links(html):
    """Rewrite internal links from old formats to Hugo paths."""
    # Omeka item links: /s/home/item/NNN -> /document/NNN/
    html = re.sub(r'href="/?s/home/item/(\d+)"', r'href="/document/\1/"', html)
    # Old PHP document links: /document.php?id=NNN -> /document/NNN/
    html = re.sub(r'href="/?document\.php\?id=(\d+)"', r'href="/document/\1/"', html)
    # Old PHP index links: /index.php -> /
    html = re.sub(r'href="/?index\.php"', r'href="/"', html)
    # Omeka page links: /s/home/page/slug -> /slug/
    html = re.sub(r'href="/?s/home/page/([^"]+)"', r'href="/\1/"', html)
    # Relative news links: index.html%3Fp=NNN.html or index.html?p=NNN -> /news/?p=NNN
    html = re.sub(r'href="index\.html[%?]3[Ff]p[=%]3[Dd]?(\d+)\.?html?"', r'href="/news/?p=\1"', html)
    html = re.sub(r'href="index\.html\?p=(\d+)\.html"', r'href="/news/?p=\1"', html)
    # Strip wardepartmentpapers.org domain from absolute URLs
    html = re.sub(
        r'href="https?://(?:www\.)?wardepartmentpapers\.org(/[^"]*)"',
        r'href="\1"',
        html,
    )
    return html


def parse_date(date_str):
    """Parse WordPress date string to datetime."""
    try:
        return datetime.strptime(date_str.strip(), "%B %d, %Y at %I:%M %p")
    except ValueError:
        print(f"  WARNING: Could not parse date: {date_str}", file=sys.stderr)
        return None


def extract_post_from_html(html):
    """Extract a single news post from HTML content."""
    soup = BeautifulSoup(html, "html.parser")

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
            tags.append(cls.replace("tag-", "").replace("-", " "))

    # Title
    title = None
    for h2 in article.find_all("h2"):
        a_tag = h2.find("a")
        if a_tag:
            title = a_tag.get_text(strip=True)
            break
    if not title:
        title = "[Untitled]"

    # Author
    author = None
    author_span = article.find("span", class_="author")
    if author_span:
        a_tag = author_span.find("a")
        if a_tag:
            author = a_tag.get_text(strip=True)

    # Date
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
        for sibling in post_meta.next_siblings:
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


def get_existing_post_ids():
    """Read wp_post_id from all existing news content files."""
    ids = set()
    if not os.path.isdir(CONTENT_DIR):
        return ids
    for fname in os.listdir(CONTENT_DIR):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        fpath = os.path.join(CONTENT_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("wp_post_id:"):
                    try:
                        ids.add(int(line.split(":")[1].strip()))
                    except ValueError:
                        pass
                    break
    return ids


def main():
    os.makedirs(CONTENT_DIR, exist_ok=True)

    existing_ids = get_existing_post_ids()
    print(f"Found {len(existing_ids)} existing posts in {CONTENT_DIR}")

    session = requests.Session()
    session.headers["User-Agent"] = "PWD-Hugo-Migration/1.0"

    extracted = 0
    skipped = 0
    errors = 0
    empty_pages = 0

    for page_num in range(1, MAX_PAGES + 1):
        if page_num == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}index.html%3Fpaged%3D{page_num}.html"

        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                print(f"  Page {page_num}: 404 — stopping pagination")
                break
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Page {page_num}: ERROR fetching — {e}", file=sys.stderr)
            errors += 1
            time.sleep(5)
            continue

        post = extract_post_from_html(resp.text)
        if post is None:
            empty_pages += 1
            if empty_pages >= 3:
                print(f"  Page {page_num}: 3 consecutive empty pages — stopping")
                break
            continue
        empty_pages = 0

        if post["wp_post_id"] and post["wp_post_id"] in existing_ids:
            skipped += 1
            if page_num % 50 == 0:
                print(f"  Page {page_num}: skip (already have post {post['wp_post_id']})")
            continue

        slug = write_post(post)
        extracted += 1
        print(f"  Page {page_num}: {slug}.md — {post['title']}")

        if post["wp_post_id"]:
            existing_ids.add(post["wp_post_id"])

        time.sleep(DELAY)

    total = extracted + skipped
    print(f"\nDone! {extracted} new posts, {skipped} skipped (already existed), {errors} errors")
    print(f"Total posts now: {len(existing_ids)}")


if __name__ == "__main__":
    main()
