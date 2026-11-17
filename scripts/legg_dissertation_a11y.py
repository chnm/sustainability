#!/usr/bin/env python3
"""WCAG 2.2 AA fixes for the static Mapping Deaf Missions pages (legg-dissertation/).

Idempotent: run it again after re-pulling the pages from scholarship.rrchnm.org.
Edits both index.html and sources.html in place.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "legg-dissertation"

# Interactive Leaflet maps, keyed by the htmlwidget id in index.html, named after
# the article section each one sits under.
MAP_LABELS = {
    "htmlwidget-9523fe02e32ff94f97ce": "Mapping Sites of Signed Protestant Episcopal Services",
    "htmlwidget-611891fc212272fbdfe8": "Deaf Schools as Centers of Deaf Life",
    "htmlwidget-b0d143f7d03ad87db8cd": "Temporary Deaf Gathering Spaces: Conferences",
    "htmlwidget-831bf0b7c06f5d61af12": "Routes and Railways, deaf mission sites",
    "htmlwidget-1466c3e4e9ed44855b15": "Routes and Railways, railroad network",
}

A11Y_STYLE = """<style id="a11y-fixes">
/* 2.4.7 Focus Visible: Distill and Leaflet suppress the default focus ring. */
a:focus-visible, button:focus-visible, input:focus-visible, [tabindex]:focus-visible,
.leaflet-container :focus-visible { outline: 3px solid #1a5fb4; outline-offset: 2px; }
/* 2.5.8 Target Size: Leaflet layer-control checkboxes are 13px. */
.leaflet-control-layers-selector { width: 24px; height: 24px; margin: 0 6px 0 0; top: 0; vertical-align: middle; }
</style>
"""

NL = r"(?:\\n|\s)*"  # newline inside a JS string literal, or real whitespace


def sub(pattern, repl, text, name, expect, flags=0):
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n == 0:
        print(f"  {name}: nothing to replace (already fixed, or the markup changed)")
    elif n != expect:
        sys.exit(f"{name}: expected {expect} replacement(s), made {n}")
    return new


def fix(path):
    text = path.read_text(encoding="utf-8")
    orig = text
    # 3.1.1 Language of Page: Radix emitted an empty lang attribute.
    text = text.replace('lang xml:lang>', 'lang="en" xml:lang="en">', 1)
    # Landmark for the article body (Radix builds the <d-article> in its inline script).
    text = text.replace("<d-article>", '<d-article role="main">', 1)
    # 1.4.3 Contrast: byline labels were rgba(0,0,0,.5) at 9.6px (4.0:1).
    text = sub(rf"(d-byline h3 \{{{NL}font-size: 0\.6rem;{NL}font-weight: 400;{NL}color: )rgba\(0, 0, 0, 0\.5\)",
               r"\1rgba(0, 0, 0, 0.7)", text, "byline contrast", 1)
    # 1.4.3 Contrast: appendix text (acknowledgements, citation, footnotes) was rgba(0,0,0,.5) at 12.8px.
    text = sub(rf"(d-appendix \{{[^}}]*?color: )rgba\(0,0,0,0\.5\);", r"\1rgba(0,0,0,0.7);", text, "appendix contrast", 3)
    # Keep the a11y style block current on re-runs.
    text = re.sub(r'<style id="a11y-fixes">.*?</style>\n', '', text, count=1, flags=re.S)
    text = text.replace("</head>", A11Y_STYLE + "</head>", 1)

    if path.name == "index.html":
        # 1.4.3 Contrast: paged-table header types and disabled pager were #999 (2.85:1).
        text = sub(rf"(\.pagedtable-header-type \{{{NL}color: )#999;", r"\1#595959;", text, "pagedtable header", 1)
        text = sub(rf"(\.pagedtable-index-nav-disabled \{{{NL}cursor: default;{NL}text-decoration: none;{NL}color: )#999;",
                   r"\1#595959;", text, "pagedtable nav", 1)
        text = sub(rf"(\.pagedtable-index-nav-disabled:hover \{{{NL}text-decoration: none;{NL}color: )#999;",
                   r"\1#595959;", text, "pagedtable nav hover", 1)
        text = sub(rf"(\.pagedtable-info \{{{NL}overflow: hidden;{NL}color: )#999;", r"\1#595959;", text, "pagedtable info", 1)
        # 4.1.2 / 1.3.1: name the focusable map regions.
        for wid, label in MAP_LABELS.items():
            text = sub(rf'<div id="{wid}" (style="[^"]*" class="leaflet html-widget")>',
                       rf'<div id="{wid}" role="region" aria-label="Interactive map: {label}" \1>',
                       text, f"map {wid}", 1)

    if text != orig:
        path.write_text(text, encoding="utf-8")
    return text != orig


if __name__ == "__main__":
    for name in ("index.html", "sources.html"):
        changed = fix(SITE / name)
        print(f"{name}: {'updated' if changed else 'already fixed'}")
