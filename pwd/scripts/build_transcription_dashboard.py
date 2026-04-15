#!/usr/bin/env python3
"""Build transcription dashboard data for Hugo.

Scans all document content files and the AI transcription JSON to produce
data/transcription_dashboard.json with per-document transcription status
and aggregate statistics.
"""

import json
import os
import re
import sys

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "..", "content", "document")
AI_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "transcriptions_ai.json")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "transcription_dashboard.json")


def parse_frontmatter(filepath):
    """Extract YAML frontmatter fields we need without a YAML dependency."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Split on the YAML delimiters
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, ""

    fm_text = parts[1]
    body = parts[2].strip()

    def get_field(name):
        m = re.search(rf"^{name}:\s*(.+)$", fm_text, re.MULTILINE)
        return m.group(1).strip().strip("'\"") if m else ""

    def get_list_first(name):
        """Get the first item of a YAML list field."""
        m = re.search(rf"^{name}:\s*\n- (.+)$", fm_text, re.MULTILINE)
        return m.group(1).strip() if m else ""

    return {
        "omeka_id": get_field("omeka_id"),
        "title": get_field("title"),
        "year": get_field("year"),
        "collection": get_list_first("collections"),
    }, body


def main():
    # Load AI transcriptions
    with open(AI_FILE, "r", encoding="utf-8") as f:
        ai_transcriptions = json.load(f)
    ai_ids = set(ai_transcriptions.keys())

    documents = []
    stats = {
        "total": 0,
        "human_only": 0,
        "ai_only": 0,
        "both": 0,
        "neither": 0,
    }
    collection_stats = {}

    for filename in sorted(os.listdir(CONTENT_DIR)):
        if not filename.endswith(".md") or filename == "_index.md":
            continue

        filepath = os.path.join(CONTENT_DIR, filename)
        meta, body = parse_frontmatter(filepath)
        if not meta or not meta["omeka_id"]:
            continue

        has_human = len(body) > 10  # non-trivial content
        has_ai = meta["omeka_id"] in ai_ids

        if has_human and has_ai:
            status = "both"
        elif has_human:
            status = "human_only"
        elif has_ai:
            status = "ai_only"
        else:
            status = "neither"

        stats["total"] += 1
        stats[status] += 1

        # Track per-collection stats
        coll = meta["collection"] or "Uncategorized"
        if coll not in collection_stats:
            collection_stats[coll] = {"total": 0, "human_only": 0, "ai_only": 0, "both": 0, "neither": 0}
        collection_stats[coll]["total"] += 1
        collection_stats[coll][status] += 1

        documents.append({
            "id": meta["omeka_id"],
            "title": meta["title"],
            "year": meta["year"],
            "collection": coll,
            "status": status,
        })

    # Sort collections by name for output
    collection_list = []
    for name in sorted(collection_stats.keys()):
        s = collection_stats[name]
        collection_list.append({
            "name": name,
            **s,
        })

    dashboard = {
        "stats": stats,
        "collections": collection_list,
        "documents": documents,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard, f)

    print(f"Dashboard built: {stats['total']} documents")
    print(f"  Both:       {stats['both']}")
    print(f"  Human only: {stats['human_only']}")
    print(f"  AI only:    {stats['ai_only']}")
    print(f"  Neither:    {stats['neither']}")
    print(f"  Collections: {len(collection_list)}")


if __name__ == "__main__":
    main()
