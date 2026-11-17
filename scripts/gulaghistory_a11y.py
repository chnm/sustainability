#!/usr/bin/env python3
"""WCAG 2.2 AA fixes for the static gulaghistory.org copy (gulaghistory/).

Idempotent: a second run changes nothing. Line endings are preserved.

    python3 scripts/gulaghistory_a11y.py           # apply
    python3 scripts/gulaghistory_a11y.py --check   # self-check only
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "gulaghistory"
SCREEN_CSS = ROOT / "themes" / "gulag" / "css" / "screen.css"
NPS_CSS = ROOT / "nps" / "c" / "style.css"
SITE_NAME = "Gulag: Many Days, Many Lives"

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
LATIN = re.compile(r"[A-Za-z]")
TAGS = re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)

CSS_START = "/* WCAG 2.2 AA fixes: scripts/gulaghistory_a11y.py */"
CSS_END = "/* end WCAG 2.2 AA fixes */"

SCREEN_BLOCK = f"""{CSS_START}
/* 2.4.1: skip link, visible on focus. */
.a11y-skip {{ position: absolute; left: -9999px; top: 0; z-index: 1000; padding: 8px 12px; background: #fff; color: #000; }}
.a11y-skip:focus {{ left: 8px; top: 8px; }}
/* 2.4.7: a focus ring that shows on the blue header and the pale panels. */
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, audio:focus-visible, video:focus-visible {{
  outline: 3px solid #1d3f61; outline-offset: 2px; }}
#header a:focus-visible {{ outline-color: #fff; }}
/* 1.4.3: #369 links on the #B5C7DA pager and current tab were 3.5:1 (anchored on #content to beat .archive a:link). */
#content .pagination a:link, #content .pagination a:visited, #content #secondary-nav .current a {{ color: #1d3f61; }}
/* 1.4.1: links in running text and exhibit breadcrumbs are underlined. */
#content p a, #content li a, #content td a, #content h1 a {{ text-decoration: underline; }}
/* 2.5.8: stacked file links and tag links get 24px targets. */
#content .item-file a, #content .tags a, #content [class*="popular"] a {{
  display: inline-block; min-height: 24px; min-width: 24px; line-height: 24px; text-align: center; }}
#content .item-file {{ margin-bottom: 4px; }}
/* 1.4.10: the 940px layout stacks into one column at narrow widths. */
@media (max-width: 959px) {{
  body {{ min-width: 0 !important; }}
  #header #primary-nav {{ position: static; }}
  #wrap, #wrap div, #wrap ul, #wrap h1, #wrap h2, #wrap h3, #wrap p, #footer, #footer div, #footer ul {{
    width: auto !important; max-width: 100%; float: none !important; box-sizing: border-box; }}
  #wrap img, #wrap video, #wrap audio, #wrap object, #wrap iframe {{ max-width: 100%; height: auto; }}
  #header h1 a, .home #header h1 a {{ max-width: 100%; background-size: contain; }}
  #wrap table {{ display: block; overflow-x: auto; }}
}}
/* 1.4.3: links on the #C7D5E3 panels (home features, podcast blurb) were #369 at 4.0:1. */
#blurb-about a:link, #blurb-about a:visited, .home .featured a:link, .home .featured a:visited {{ color: #1d3f61; }}
{CSS_END}
"""

NPS_BLOCK = f"""{CSS_START}
/* 1.4.3: #606060 footer text and links on #111 were 3:1. */
#footer, #footer p, #footer a:link, #footer a:visited {{ color: #a3a3a3; }}
/* 1.4.3: links were #999 on white (2.8:1), the current tab #777 (4.5:1 at 11px), section titles #8493A5 (3:1). */
a:link, a:visited {{ color: #595959; }}
#footer a:link, #footer a:visited {{ color: #a3a3a3; }}
#reflections #reflections_nav a, #online #online_nav a, #traveling #traveling_nav a,
#resources #teacher_nav a, #about #about_nav a, #onlinenav li.on li a, #aboutnav li.on li a {{ color: #595959; }}
#onlinenav li.on a, #aboutnav li.on a {{ color: #3d5a7a; }}
#navigation a:link, #navigation a:visited {{ color: #fff; }}
h2, h5 {{ color: #595959; }}
/* 1.4.10: the 750px layout stacks into one column at narrow widths. */
@media (max-width: 769px) {{
  body, html {{ min-width: 0 !important; width: auto !important; }}
  #header h1 {{ height: auto; }}
  #wrap, #wrap div, #wrap ul, #wrap h1, #wrap h2, #wrap p {{
    width: auto !important; max-width: 100%; float: none !important; box-sizing: border-box; }}
  #wrap img {{ max-width: 100%; height: auto; }}
  #header ul#navigation li {{ width: auto !important; float: none; }}
  /* The museum map's hotspots sit over a fixed-size image; it scrolls instead (maps are exempt). */
  #museummap {{ overflow-x: auto; }}
}}
a:focus-visible {{ outline: 3px solid #fff; outline-offset: 2px; }}
{CSS_END}
"""


def read(p: Path) -> str:
    with open(p, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def write(p: Path, text: str) -> None:
    with open(p, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(text)


def outside_comments(text: str, fn) -> str:
    """Apply fn to the text between HTML comments, leaving commented-out markup alone."""
    out, last = [], 0
    for m in COMMENT.finditer(text):
        out.append(fn(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(fn(text[last:]))
    return "".join(out)


def page_lang(text: str) -> str:
    body = TAGS.sub(" ", text[text.find("<body"):] if "<body" in text else text)
    return "ru" if len(CYRILLIC.findall(body)) > len(LATIN.findall(body)) else "en"


def fix_lang(text: str) -> str:
    # 3.1.1: no page declared a language; the Russian exhibit pages are Russian.
    if re.search(r"<html\b[^>]*\blang=", text):
        return text
    lang = page_lang(text)
    return re.sub(r"<html\b([^>]*)>", rf'<html\1 lang="{lang}">', text, count=1)


def fix_viewport(text: str) -> str:
    # 1.4.10: no page had a viewport meta, so phones rendered the fixed 980px desktop layout.
    if 'name="viewport"' in text:
        return text
    return re.sub(r"(<head\b[^>]*>)", r'\1\n<meta name="viewport" content="width=device-width, initial-scale=1" />', text, count=1)


def fix_stylesheets(text: str) -> str:
    # wget turned Omeka's exhibit stylesheet route into a link to the page itself, or to "".
    return re.sub(r'[ \t]*<link rel="stylesheet" media="screen" href="(?![^"]*\.css")[^"]*" />\r?\n?', "", text)


def fix_header(text: str) -> str:
    # 2.4.4 / 4.1.2: the logo link is an image-replaced <a> with no text.
    return re.sub(r'(<div id="header">.*?<h1><a href="[^"]*">)(</a></h1>)', rf"\1{SITE_NAME}\2", text, count=1, flags=re.S)


def fix_skip(text: str) -> str:
    # 2.4.1: a skip link to #content on the Omeka theme pages.
    if 'class="a11y-skip"' in text or 'id="content"' not in text or "themes/gulag/css/screen.css" not in text:
        return text
    return re.sub(r"(<body\b[^>]*>)", r'\1<a class="a11y-skip" href="#content">Skip to main content</a>', text, count=1)


def fix_empty_links(text: str) -> str:
    # 2.4.4: items without an image left empty <a> elements beside their title links.
    return re.sub(r'<a href="[^"]*"[^>]*>\s*</a>', "", text)


def fix_php_leak(text: str) -> str:
    # The exhibit template commented out its Previous/Next Page block with <?php/* ... */ ?>;
    # in static HTML that comment leaks, so the links (some to empty -1.html pages) showed.
    return re.sub(r"[ \t]*<\?php/\*.*?\*/\s*\?>", "", text, flags=re.S)


def fix_search(text: str) -> str:
    # 1.3.1 / 3.3.2: the unlabelled Omeka search form posts to a route the static copy cannot answer.
    return re.sub(r'[ \t]*<form id="items_search"[^>]*>.*?</form>\r?\n?', "", text, flags=re.S)


def fix_dead_pages(text: str) -> str:
    # The first page of each exhibit section had a "Previous Page" link to an empty -1.html page.
    return re.sub(r'<a href="(?:[^"]*/)?-1\.html">[^<]*</a>', "", text)


def fix_plugin_audio(text: str) -> str:
    # 1.1.1 / 2.1.1 / 4.1.2: QuickTime <object>/<embed> audio players become native <audio>.
    def repl(m: re.Match) -> str:
        return f'<audio controls preload="none" src="{m.group(1)}"><a href="{m.group(1)}">Download the audio</a></audio>'
    return outside_comments(text, lambda t: re.sub(
        r'<object classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B".*?<embed src="([^"]+)".*?</object>', repl, t, flags=re.S))


def fix_podcast(text: str) -> str:
    # podPress injected a Flash player with script; swap in <audio> and drop the script-only links.
    m = re.search(r'<div id="podPressPlayerSpace_(\d+)">&nbsp;</div>\s*<a href="([^"]+\.mp3)"', text)
    if not m:
        return text
    n, src = m.group(1), m.group(2)
    text = text.replace(f'<div id="podPressPlayerSpace_{n}">&nbsp;</div>',
                        f'<div id="podPressPlayerSpace_{n}"><audio controls preload="none" src="{src}"></audio></div>')
    text = re.sub(r'<a href="[^"]*#" onclick="javascript: podPress(?:ShowHidePlayer|PopupPlayer)\([^"]*">.*?</a>\s*\|?\s*', "", text)
    return re.sub(r'<script type="text/javascript"><!--\s*podPressShowHidePlayer\(.*?</script>', "", text, flags=re.S)


def fix_broken_href(text: str) -> str:
    # Item 30's credit link lost its closing quote, which swallowed the item pager.
    return text.replace('href="http://digitalgallery.nypl.org/nypldigital/id?52110>New York Public Library</a>',
                        'href="http://digitalgallery.nypl.org/nypldigital/id?52110">New York Public Library</a>')


def fix_wp_script(text: str) -> str:
    return text.replace("wp-mailto-links.js%3Fver=1.5.0.html", "wp-mailto-links.js").replace(
        "wp-mailto-links.js?ver=1.5.0.html", "wp-mailto-links.js")


def fix_css(text: str, block: str) -> str:
    text = re.sub(re.escape(CSS_START) + r".*?" + re.escape(CSS_END) + r"\n?", "", text, flags=re.S)
    return text.rstrip("\n") + "\n\n" + block


PAGE_FIXES = (fix_lang, fix_viewport, fix_stylesheets, fix_header, fix_skip, fix_php_leak, fix_dead_pages,
              fix_empty_links, fix_search, fix_plugin_audio, fix_podcast, fix_broken_href, fix_wp_script)


def apply() -> int:
    changed = 0
    js = ROOT / "podcast/wp-content/plugins/wp-mailto-links/js/wp-mailto-links.js?ver=1.5.0.html"
    if js.exists():
        js.rename(js.with_name("wp-mailto-links.js"))
        changed += 1
    for dead in sorted(ROOT.rglob("-1.html")):
        dead.unlink()
        changed += 1
    for page in sorted(ROOT.rglob("*.html")):
        old = read(page)
        new = old
        for fn in PAGE_FIXES:
            new = fn(new)
        if new != old:
            write(page, new)
            changed += 1
    for css, block in ((SCREEN_CSS, SCREEN_BLOCK), (NPS_CSS, NPS_BLOCK)):
        old = read(css)
        new = fix_css(old, block)
        if new != old:
            write(css, new)
            changed += 1
    return changed


def selfcheck() -> None:
    assert fix_lang("<html xmlns='x'><body>Привет мир</body>") == "<html xmlns='x' lang=\"ru\"><body>Привет мир</body>"
    assert fix_lang("<html><body>Hello <b>мир</b> world</body>") == '<html lang="en"><body>Hello <b>мир</b> world</body>'
    assert fix_lang('<html lang="en">') == '<html lang="en">'
    css = '<link rel="stylesheet" media="screen" href="a.css" />\n<link rel="stylesheet" media="screen" href="" />\n'
    assert fix_stylesheets(css) == '<link rel="stylesheet" media="screen" href="a.css" />\n'
    h = '<div id="header">\n<div><h1><a href="../index.html"></a></h1>'
    assert fix_header(h).endswith(f'<a href="../index.html">{SITE_NAME}</a></h1>') and fix_header(fix_header(h)) == fix_header(h)
    s = '<link href="themes/gulag/css/screen.css"><body class="x"><div id="content">'
    assert fix_skip(fix_skip(s)).count("a11y-skip") == 1
    assert fix_empty_links('<div class="item-img">\n<a href="show/1.html"></a>\n</div>') == '<div class="item-img">\n\n</div>'
    assert fix_empty_links('<a href="x"><img src="y" alt=""></a>') == '<a href="x"><img src="y" alt=""></a>'
    leak = '<div>\n\t<?php/*\n\t<div id="exhibit-pagination"><a href="-1.html">Previous Page</a></div>\n\t*/ ?>\n\t</div>'
    assert fix_php_leak(leak) == "<div>\n\n\t</div>" and fix_php_leak(fix_php_leak(leak)) == fix_php_leak(leak)
    assert fix_dead_pages('<a href="-1.html">Previous Page</a>') == ""
    obj = ('<object classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" w="1"><param name="src" value="x" />'
           '<embed src="../a.mp3" type="video/quicktime"></embed></object>')
    assert fix_plugin_audio(obj).startswith('<audio controls preload="none" src="../a.mp3">')
    assert fix_plugin_audio(f"<!-- {obj} -->") == f"<!-- {obj} -->"
    assert fix_dead_pages('<a href="arrest/-1.html">Previous Page</a> <a href="arrest/1.html">Next Page</a>') == \
        ' <a href="arrest/1.html">Next Page</a>'
    pod = ('<div id="podPressPlayerSpace_1">&nbsp;</div>\n<a href="p/G.mp3" target="new">icon</a> Episode 1: '
           '<a href="index.html#" onclick="javascript: podPressShowHidePlayer(\'1\',\'u\'); return false;"><span>Play Now</span></a> | '
           '<a href="index.html#" onclick="javascript: podPressPopupPlayer(\'1\', \'u\'); return false;">Play in Popup</a> | '
           '<a href="p/G.mp3">Download</a>\n<script type="text/javascript"><!--\npodPressShowHidePlayer(\'1\');\n-->\n</script>')
    out = fix_podcast(pod)
    assert '<audio controls preload="none" src="p/G.mp3">' in out and "podPress(" not in out and fix_podcast(out) == out
    assert fix_css(fix_css("a{}\n", SCREEN_BLOCK), SCREEN_BLOCK).count(CSS_START) == 1


if __name__ == "__main__":
    selfcheck()
    if "--check" in sys.argv:
        print("self-check passed")
    else:
        print(f"{apply()} files changed")
