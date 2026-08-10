#!/usr/bin/env python3
"""Rebuild items/show/<id>.html (+ .dcmes.xml) from Wayback captures.

The 2026 crawl missed 37 item pages: nothing on the site linked to them
except JavaScript wget could not follow, so wget never fetched them, while
map/data/items.json still points every map marker at one. This rebuilds the
ones the Internet Archive holds.

Only <title> and the div[role=main] content region come from the capture. The
chrome (head, header, nav, footer) is copied from an item page the crawl did
get, so a rebuilt page carries every archive-wide fix — Pagefind search form,
Matomo, the accessibility pass — rather than whatever the snapshot froze.

The content region is then put through the same transformations wget
--convert-links and this repo's later commits applied to the crawled pages,
and pre-2018 captures are additionally brought up to the markup Omeka emitted
by 2026. Verified by rebuilding pages the crawl *did* get from their own
captures: 7 of 7 post-2020 captures and 7 of 11 2014-2017 captures come back
byte-identical, the remaining 4 differing only where the item was edited
between the snapshot and the crawl.

Usage, from the archive root:

    python3 tools/backfill_items.py 141 171 177 ...      # fetch and rebuild
    python3 tools/backfill_items.py --cache .captures 141

Coordinates come from map/data/markers.json (captured from the live server in
2026) in preference to the snapshot's, so a rebuilt map matches the main map.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request

ORIGIN = "https://mallhistory.org"
ACCESSED = "May 27, 2026"                       # the date every crawled page cites
TEMPLATE_PAGE = "items/show/440.html"           # any page the crawl did get
CDX = ("https://web.archive.org/cdx/search/cdx?url=mallhistory.org/items/show/%s"
       "&matchType=exact&filter=statuscode:200&fl=timestamp&limit=-1")
CAPTURE = "https://web.archive.org/web/%sid_/%s/items/show/%s"

MAIN_START = '<div role="main"'
FOOTER = "<footer>"

# The aside skeleton 418 of the 445 crawled item pages share.
ASIDE = ("<aside>\n" + " " * 84 + "\n" + " " * 8 + "\n" + " " * 8 +
         '<div class="images">\n%(anchors)s' + " " * 16 + "</div>\n" + " " * 16 + "\n" + " " * 4)

GEOLOCATION = (
    '<div id="item-map-%(id)s" class="map geolocation-map" style="width: ; height: 300px"></div>'
    "<script type='text/javascript'>var itemMap%(id)s;"
    'OmekaMapSingle = new OmekaMapSingle("item-map-%(id)s", '
    '{"latitude":%(lat)s,"longitude":%(lng)s,"zoomLevel":%(zoom)s,"show":true}, '
    '{"basemap":"CartoDB.Voyager","cluster":true}); </script>'
)

DCMES_HEADER = (
    '<?xml version="1.0"?><!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"\n'
    '"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">\n'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n'
    'xmlns:dc="http://purl.org/dc/elements/1.1/">\n\n'
    '<rdf:Description rdf:about="%s/items/show/%%s">\n' % ORIGIN
)
DCMES_FOOTER = "</rdf:Description></rdf:RDF>\n"

ELEMENT = re.compile(
    r'<div id="dublin-core-([a-z-]+)" class="element">(.*?)</div><!-- end element -->', re.S)
ELEMENT_TEXT = re.compile(r'<div class="element-text">(.*?)</div>', re.S)
BROWSE_LINK = re.compile(r'(<a href="/items/browse\?[^"]*">)(.*?)(</a>)', re.S)


def markers():
    with open("map/data/markers.json", encoding="utf-8") as fh:
        features = json.load(fh)["features"]
    return {str(f["properties"]["id"]): tuple(reversed(f["geometry"]["coordinates"]))
            for f in features}


def split_page(text):
    return text[:text.index(MAIN_START)], text[text.index(MAIN_START):text.index(FOOTER)], \
        text[text.index(FOOTER):]


# --------------------------------------------------------------------------- links

def local_target(path):
    """Local file for an origin URL path, or None if the crawl never got it."""
    rel = path.lstrip("/") or "index"
    for candidate in (rel, rel + ".html", rel.rstrip("/") + "/index.html"):
        if os.path.isfile(candidate):
            return candidate
    return None


def escape_attr(value):
    return re.sub(r"&(?![A-Za-z][A-Za-z0-9]*;|#\d+;)", "&amp;", value)


def convert_url(raw, from_dir):
    value = html.unescape(raw)
    m = re.match(r"^(?:https?://mallhistory\.org)?(/[^\s]*)$", value)
    if not m:
        return escape_attr(raw)                      # external, mailto:, #, relative
    path, _, query = m.group(1).partition("?")
    if (path.startswith(("/files/", "/application/views/scripts/images/"))
            or path.endswith(".dcmes.xml")):
        # Media (bucket redirect), Omeka's media placeholders and the static
        # output formats are all addressed from the site root in this archive.
        return escape_attr(path)
    if not query:
        target = local_target(path)
        if target:
            return escape_attr(os.path.relpath(target, from_dir))
    return escape_attr(ORIGIN + path + ("?" + query if query else ""))


# --------------------------------------------------------------------------- page

def modernise(main, item_id, coords):
    """Bring a pre-2018 capture up to the markup the 2026 crawl produced."""
    # Images: the newer template indents deeper and does not self-close <img>.
    aside = re.match(r'(?s).*?<aside>\s*<div class="images">(.*?)</div>\s*'
                     r'(?=<div id="item-citation")', main)
    if aside:
        anchors = [a.replace("/>\n</a>", "></a>").replace("/>", ">")
                   for a in re.findall(r"<a href=.*?</a>", aside.group(1), re.S)]
        rebuilt = ASIDE % {"anchors": "".join(" " * 24 + a + "\n" for a in anchors)}
        start = aside.start(0) + aside.group(0).index("<aside>")
        main = main[:start] + rebuilt + main[aside.end(0):]

    # Citation: the URL gained a wrapping span.
    main = re.sub(r"(accessed [A-Z][a-z]+ \d{1,2}, \d{4}, )"
                  r"(https?://mallhistory\.org/items/show/\d+)\.",
                  r'\g<1><span class="citation-url">\g<2></span>.', main)

    # COinS field names lost their capitals.
    main = re.sub(r"rft\.([A-Za-z]+)=", lambda m: "rft." + m.group(1).lower() + "=", main)

    # Geolocation: <style> + div.map.panel + a markerHtml-carrying call became a
    # plain div plus a call taking the basemap options separately.
    old_map = re.search(r'(?:<style[^>]*>.*?</style>)?<div id="item-map-%s" class="map panel">'
                        r'</div><script[^>]*>.*?</script>' % re.escape(item_id), main, re.S)
    if old_map:
        frozen = re.search(r'\{"latitude":([-\d.]+),"longitude":([-\d.]+),"zoomLevel":(\d+)',
                           old_map.group(0))
        lat, lng = coords.get(item_id, (frozen.group(1), frozen.group(2)))
        main = (main[:old_map.start()] +
                GEOLOCATION % {"id": item_id, "lat": lat, "lng": lng, "zoom": frozen.group(3)} +
                main[old_map.end():])
    return main


def transform(main, item_id, coords, from_dir="items/show"):
    main = main.replace('<div role="main">', '<div role="main" data-pagefind-body>', 1)
    if 'class="citation-url"' not in main:
        main = modernise(main, item_id, coords)

    # Captures predating the origin's move to HTTPS cite themselves as http://.
    main = main.replace("http://mallhistory.org", ORIGIN)
    main = main.replace("http%3A%2F%2Fmallhistory.org", "https%3A%2F%2Fmallhistory.org")

    # Output formats: this repo keeps dcmes-xml as a static file and purged the rest.
    main = re.sub(r'[ \t]*<li><a href="[^"]*\?output=(?!dcmes-xml)[a-z-]+">[a-z-]+</a></li>\n',
                  "", main)
    main = re.sub(r'href="[^"]*/items/show/(\d+)\?output=dcmes-xml"',
                  r'href="/items/show/\1.dcmes.xml"', main)

    # The citation names the date the page was rendered; crawled pages cite the crawl.
    main = re.sub(r"(<em>Histories of the National Mall</em>, accessed )[A-Z][a-z]+ \d{1,2}, \d{4}",
                  r"\g<1>" + ACCESSED, main)

    def convert(m):
        attr, value = m.group(1), m.group(2)
        if value.startswith(("#", "mailto:", "javascript:", "data:")):
            return m.group(0)
        return '%s="%s"' % (attr, convert_url(value, from_dir))

    return re.sub(r'\b(href|src)="([^"]*)"', convert, main)


def build_page(item_id, capture, template, coords):
    title = re.search(r"<title>(.*?)</title>", capture, re.S).group(1).strip()
    _, main, _ = split_page(capture)
    head, _, tail = split_page(template)
    head = re.sub(r"<title>.*?</title>", "<title>%s</title>" % title, head, count=1, flags=re.S)
    return head + transform(main, item_id, coords) + tail


# --------------------------------------------------------------------------- dcmes-xml

def xml_escape(value):
    """PHP htmlspecialchars($value, ENT_QUOTES), which is what Omeka applies."""
    return (value.replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#039;")
                 .replace("<", "&lt;").replace(">", "&gt;"))


def stored_value(name, rendered):
    """Recover the stored element value from the way the page rendered it."""
    if name == "title":
        return html.unescape(rendered)      # the theme escapes the title, nothing else
    # Omeka builds the browse links itself and escapes their visible text.
    return BROWSE_LINK.sub(lambda m: m.group(1) + html.unescape(m.group(2)) + m.group(3),
                           rendered)


def build_dcmes(item_id, capture):
    out = [DCMES_HEADER % item_id]
    for name, block in ELEMENT.findall(capture):
        for value in ELEMENT_TEXT.findall(block):
            out.append("<dc:%s>%s</dc:%s>\n"
                       % (name, xml_escape(stored_value(name, value.strip())), name))
    out.append(DCMES_FOOTER)
    return "".join(out)


# --------------------------------------------------------------------------- driver

def fetch_capture(item_id, cache):
    path = os.path.join(cache, "%s.html" % item_id)
    if os.path.isfile(path):
        return open(path, encoding="utf-8", errors="replace").read()
    with urllib.request.urlopen(CDX % item_id, timeout=90) as fh:
        stamps = fh.read().decode().split()
    if not stamps:
        raise LookupError("no Wayback capture of items/show/%s" % item_id)
    with urllib.request.urlopen(CAPTURE % (stamps[-1], ORIGIN, item_id), timeout=90) as fh:
        capture = fh.read().decode("utf-8", "replace")
    os.makedirs(cache, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as out:
        out.write(capture)
    return capture


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("ids", nargs="+", help="item ids to rebuild")
    parser.add_argument("--cache", default=".captures", help="directory for downloaded captures")
    parser.add_argument("--out", default="items/show", help="where to write the pages")
    args = parser.parse_args(argv)

    template = open(TEMPLATE_PAGE, encoding="utf-8").read()
    coords = markers()
    for item_id in args.ids:
        try:
            capture = fetch_capture(item_id, args.cache)
        except LookupError as exc:
            print("skipped %s: %s" % (item_id, exc), file=sys.stderr)
            continue
        write(os.path.join(args.out, "%s.html" % item_id),
              build_page(item_id, capture, template, coords))
        write(os.path.join(args.out, "%s.dcmes.xml" % item_id), build_dcmes(item_id, capture))
        print("rebuilt items/show/%s.html" % item_id)


if __name__ == "__main__":
    main()
