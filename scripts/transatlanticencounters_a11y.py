#!/usr/bin/env python3
"""WCAG 2.2 AA fixes for the flattened transatlanticencounters.rrchnm.org copy.

Idempotent: a second run changes nothing. Files are read and written with their
line endings untouched. Run from anywhere:

    python3 scripts/transatlanticencounters_a11y.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "transatlanticencounters"
THEME = ROOT / "themes" / "centerrow"
STYLE = THEME / "css" / "style.css?v=2.8.css"
ITEMS_JS = THEME / "js" / "items-show.js?v=2.8"

# 1.4.4: the theme pinned the zoom level with maximum-scale/minimum-scale.
OLD_VIEWPORT = 'content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=yes"'
NEW_VIEWPORT = 'content="width=device-width, initial-scale=1.0"'

# 1.1.1: staff photos on the contact page, named from the caption beside each.
CONTACT_ALTS = {
    "images/greet.JPG": "Michele Greet",
    "images/ospina.jpg": "Adriana Ospina",
    "images/shook.jpg": "Beth Shook",
    "images/derecola.jpg": "Melissa Derecola",
    "images/gilbert.jpg": "Suzanne Gilbert",
    "photos/_DSC8292-1-crop.jpg": "Julie Goforth",
}

# 4.1.2 / 2.4.2: the three Leaflet pages embedded on maps.html were all titled "leaflet".
MAP_PAGES = {
    "artists.html": "Map of Latin American artists residing in Paris",
    "table.html": "Map legend: marker colors by artist nationality",
    "galleries.html": "Map of Parisian galleries that exhibited Latin American art",
}

# 240 items use the same "NO IMAGE AVAILABLE" graphic, uploaded as placeholder5.png.
PLACEHOLDER = "placeholder5.png"

CSS_START = "/* WCAG 2.2 AA fixes: scripts/transatlanticencounters_a11y.py */"
CSS_END = "/* end WCAG 2.2 AA fixes */"
CSS_BLOCK = f"""{CSS_START}
/* 1.4.1 Use of Color: links in running text are underlined. */
#content a, footer p a {{ text-decoration: underline; }}
/* 2.4.7 Focus Visible: a ring that holds up on the cream background and the photos. */
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {{
  outline: 3px solid #1d3557; outline-offset: 2px; }}
/* 1.4.10 Reflow: long citation URLs wrap; the maps stack at phone width. */
.citation-url, #content .element-text {{ overflow-wrap: anywhere; }}
#content img {{ max-width: 100%; }}
@media (max-width: 600px) {{
  #map-1 iframe, #map-2 iframe {{ width: 100% !important; float: none; display: block; }}
}}
{CSS_END}
"""


def read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def fix_all_pages(text: str) -> str:
    text = text.replace(OLD_VIEWPORT, NEW_VIEWPORT)
    # 3.1.1 Language of Page: three Leaflet pages had no lang.
    return re.sub(r"<html(?![^>]*\blang=)([^>]*)>", r'<html lang="en"\1>', text, count=1)


def fix_home(text: str) -> str:
    # Each home-page tile is an image link and a text link to the same page. The image
    # links had misleading or empty names (an artist's name, or nothing); hide them from
    # the keyboard and screen readers and leave the text link as the one way in.
    return re.sub(
        r'(<div id="grid-\d-\d"[^>]*>)<a href="([^"]*)"><img ([^>]*?)alt="[^"]*"',
        r'\1<a href="\2" tabindex="-1" aria-hidden="true"><img \3alt=""',
        text,
    )


def fix_contact(text: str) -> str:
    for src, name in CONTACT_ALTS.items():
        text = re.sub(
            rf'<img class="floatLeft" src="{re.escape(src)}"(?![^>]*\balt=)',
            f'<img class="floatLeft" src="{src}" alt="{name}"',
            text,
        )
    return text


def fix_search(text: str) -> str:
    # 1.3.1 / 4.1.2: the Geolocation label pointed at an id that does not exist.
    return text.replace('<label for="geolocation-address">', '<label for="geolocation-address-input">')


def fix_maps(text: str) -> str:
    text = re.sub(r'(<iframe id ="Maps" src="artists\.html")(?! title=)', rf'\1 title="{MAP_PAGES["artists.html"]}"', text)
    text = re.sub(r'(<iframe src="table\.html")(?![^>]*title=)', rf'\1 title="{MAP_PAGES["table.html"]}"', text)
    return text.replace('title="iframe map"', f'title="{MAP_PAGES["galleries.html"]}"')


def fix_map_page(text: str, name: str) -> str:
    text = text.replace("<title>leaflet</title>", f"<title>{MAP_PAGES[name]}</title>", 1)
    if name == "table.html":
        text = text.replace("<CTYPE html>", "<!DOCTYPE html>", 1)
        # 1.3.1: the legend's header row used <td>.
        text = re.sub(r"<thead>(.*?)</thead>",
                      lambda m: "<thead><tr>" + m.group(1).replace("<td", "<th").replace("</td>", "</th>") + "</tr></thead>"
                      if "<th" not in m.group(1) else m.group(0),
                      text, count=1, flags=re.S)
    return text


def fix_item(text: str) -> str:
    # 1.1.1 / 2.4.4: the placeholder graphic reads "NO IMAGE AVAILABLE".
    text = text.replace(f'alt="{PLACEHOLDER}" title="{PLACEHOLDER}"', 'alt="No image available"')
    return re.sub(rf'(<div class="media-link-1">\s*<a href="[^"]*">){re.escape(PLACEHOLDER)}</a>',
                  r"\1No image available</a>", text)


def fix_items_js(text: str) -> str:
    # 1.1.1 / 4.1.2: lightSlider's gallery pager drew one unlabelled href="#" thumbnail
    # link on every item page, and every item has a single file. Only draw the pager
    # when there is something to page through.
    return text.replace("gallery:true,", "gallery: $('#itemfiles > li').length > 1,")


def fix_style(text: str) -> str:
    text = re.sub(re.escape(CSS_START) + r".*?" + re.escape(CSS_END) + r"\n?", "", text, flags=re.S)
    return text.rstrip("\n") + "\n\n" + CSS_BLOCK


def apply() -> int:
    changed = 0
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        old = read(path)
        new = fix_all_pages(old)
        if rel == "index.html":
            new = fix_home(new)
        elif rel == "contact.html":
            new = fix_contact(new)
        elif rel == "items/search.html":
            new = fix_search(new)
        elif rel == "maps.html":
            new = fix_maps(new)
        elif rel in MAP_PAGES:
            new = fix_map_page(new, rel)
        elif rel.startswith("items/show/"):
            new = fix_item(new)
        if new != old:
            write(path, new)
            changed += 1
    for path, fn in ((ITEMS_JS, fix_items_js), (STYLE, fix_style)):
        old = read(path)
        new = fn(old)
        if new != old:
            write(path, new)
            changed += 1
    return changed


def selfcheck() -> None:
    assert NEW_VIEWPORT in fix_all_pages(f'<html><meta name="viewport" {OLD_VIEWPORT} />')
    assert fix_all_pages('<html style="x">') == '<html lang="en" style="x">'
    assert fix_all_pages('<html lang="fr">') == '<html lang="fr">'
    home = '<div id="grid-1-2" class="col-4"><a href="x"><img src="p.jpg" alt="Diego Rivera" /></a>'
    assert fix_home(home) == '<div id="grid-1-2" class="col-4"><a href="x" tabindex="-1" aria-hidden="true"><img src="p.jpg" alt="" /></a>'
    assert fix_home(fix_home(home)) == fix_home(home)
    c = '<img class="floatLeft" src="images/shook.jpg" width="150px">'
    assert fix_contact(c) == '<img class="floatLeft" src="images/shook.jpg" alt="Beth Shook" width="150px">'
    assert fix_contact(fix_contact(c)) == fix_contact(c)
    t = "<CTYPE html><title>leaflet</title><thead>\n<td>A</td><td>B</td>\n</thead>"
    once = fix_map_page(t, "table.html")
    assert "<!DOCTYPE html>" in once and "<th>A</th>" in once and fix_map_page(once, "table.html") == once
    item = f'<img src="u" alt="{PLACEHOLDER}" title="{PLACEHOLDER}"><div class="media-link-1">\n<a href="u">{PLACEHOLDER}</a>'
    assert fix_item(item) == '<img src="u" alt="No image available"><div class="media-link-1">\n<a href="u">No image available</a>'
    css = fix_style("a{}\n")
    assert fix_style(css) == css and css.count(CSS_START) == 1


if __name__ == "__main__":
    selfcheck()
    if "--check" in sys.argv:
        print("self-check passed")
    else:
        print(f"{apply()} files changed")
