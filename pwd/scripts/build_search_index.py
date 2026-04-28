#!/usr/bin/env python3
"""Build split search index JSON files from Hugo content files for MiniSearch.

Generates separate index files by type so the browser only loads what's needed:
  - static/js/search-documents.json  (documents with metadata + transcriptions)
  - static/js/search-pages.json      (editorial pages + news)

Usage:
    python3 scripts/build_search_index.py
"""

import json
import os
import re

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "js")

# Stopwords to strip from transcription text to reduce index size
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "he", "in", "is", "it", "its", "of", "on", "or",
    "she", "that", "the", "to", "was", "were", "will", "with", "this",
    "but", "they", "not", "been", "had", "her", "his", "him", "how",
    "if", "may", "no", "nor", "can", "did", "do", "does", "than",
    "our", "own", "so", "such", "their", "them", "then", "there",
    "these", "those", "we", "what", "when", "which", "who", "whom",
    "would", "you", "your", "i", "me", "my", "up", "about", "after",
    "all", "also", "am", "any", "because", "before", "between", "both",
    "each", "few", "get", "got", "into", "just", "made", "make",
    "more", "most", "must", "new", "now", "off", "old", "only",
    "other", "out", "over", "said", "same", "should", "some",
    "still", "take", "through", "too", "under", "very",
    "well", "where", "while", "why", "yet",
}


def parse_front_matter_and_body(filepath):
    """Parse YAML front matter and body from a markdown file. Returns (dict, body_str)."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    fm_text = content[3:end]
    body = content[end + 3:].strip()

    fm = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("  - ") or line.startswith("- "):
            val = line.lstrip(" -").strip()
            if current_list is not None:
                current_list.append(val)
            continue
        match = re.match(r"^(\w[\w_]*):\s*(.*)", line)
        if match:
            key = match.group(1)
            val = match.group(2).strip()
            if current_list is not None and current_key:
                fm[current_key] = current_list
            if val == "" or val == "[]":
                current_key = key
                current_list = []
            else:
                current_key = key
                current_list = None
                if (val.startswith("'") and val.endswith("'")) or \
                   (val.startswith('"') and val.endswith('"')):
                    val = val[1:-1]
                fm[key] = val

    if current_list is not None and current_key:
        fm[current_key] = current_list

    return fm, body


def strip_html(text):
    """Remove HTML tags."""
    return re.sub(r"<[^>]+>", " ", text)


def clean_transcription(text):
    """Strip HTML, remove stopwords, collapse whitespace."""
    text = strip_html(text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    filtered = [w for w in words if w.lower() not in STOPWORDS]
    return " ".join(filtered)


def build_documents():
    """Build document index entries with transcription text."""
    entries = []
    doc_dir = os.path.join(CONTENT_DIR, "document")
    if not os.path.isdir(doc_dir):
        return entries

    # Load AI transcriptions
    ai_trans = {}
    ai_path = os.path.join(DATA_DIR, "transcriptions_ai.json")
    if os.path.isfile(ai_path):
        with open(ai_path, "r", encoding="utf-8") as f:
            ai_trans = json.load(f)
        print(f"Loaded {len(ai_trans)} AI transcriptions")

    files = sorted(f for f in os.listdir(doc_dir) if f.endswith(".md"))
    print(f"Processing {len(files)} documents...")
    human_count = 0
    ai_count = 0

    for i, fname in enumerate(files):
        fm, body = parse_front_matter_and_body(os.path.join(doc_dir, fname))
        doc_id = fname.replace(".md", "")
        entry = {
            "id": i + 1,
            "t": fm.get("title", ""),
            "u": f"/document/{doc_id}/",
        }
        if fm.get("year"):
            entry["y"] = fm["year"]
        authors = fm.get("authors", [])
        if isinstance(authors, list) and authors:
            entry["a"] = ", ".join(authors)
        elif isinstance(authors, str) and authors:
            entry["a"] = authors
        recipients = fm.get("recipients", [])
        if isinstance(recipients, list) and recipients:
            entry["r"] = ", ".join(recipients)
        elif isinstance(recipients, str) and recipients:
            entry["r"] = recipients
        dt = fm.get("doc_types", [])
        if isinstance(dt, list) and dt:
            entry["d"] = dt[0]
        if fm.get("description"):
            entry["s"] = fm["description"][:150]

        # Combine human + AI transcription text for search
        trans_parts = []
        if body.strip():
            trans_parts.append(body.strip())
            human_count += 1
        omeka_id = fm.get("omeka_id", doc_id)
        ai_text = ai_trans.get(str(omeka_id), "")
        if ai_text:
            trans_parts.append(ai_text)
            ai_count += 1

        if trans_parts:
            combined = " ".join(trans_parts)
            entry["c"] = clean_transcription(combined)

        entries.append(entry)

    print(f"  {human_count} human transcriptions, {ai_count} AI transcriptions included")
    return entries


def build_pages():
    """Build editorial page and news post index entries."""
    entries = []
    idx = 0

    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        fpath = os.path.join(CONTENT_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        fm, _ = parse_front_matter_and_body(fpath)
        if fm.get("type") != "page":
            continue
        slug = fm.get("slug", fname.replace(".md", ""))
        idx += 1
        entries.append({
            "id": idx,
            "t": fm.get("title", slug),
            "u": f"/{slug}/",
            "T": "P",
        })

    news_dir = os.path.join(CONTENT_DIR, "news")
    if os.path.isdir(news_dir):
        for fname in sorted(os.listdir(news_dir)):
            if not fname.endswith(".md") or fname in ("_index.md", "archive.md"):
                continue
            fm, _ = parse_front_matter_and_body(os.path.join(news_dir, fname))
            slug = fname.replace(".md", "")
            idx += 1
            entry = {
                "id": idx,
                "t": fm.get("title", slug),
                "u": f"/news/{slug}/",
                "T": "N",
            }
            if fm.get("author"):
                entry["a"] = fm["author"]
            entries.append(entry)

    return entries


def write_index(entries, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(path) / 1024
    if size_kb > 1024:
        print(f"  {filename}: {len(entries)} entries ({size_kb/1024:.1f} MB)")
    else:
        print(f"  {filename}: {len(entries)} entries ({size_kb:.0f} KB)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    documents = build_documents()
    pages = build_pages()
    write_index(documents, "search-documents.json")
    write_index(pages, "search-pages.json")
    print(f"\nTotal: {len(documents)} documents, {len(pages)} pages/news")


if __name__ == "__main__":
    main()
