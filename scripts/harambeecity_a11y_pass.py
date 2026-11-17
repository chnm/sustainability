#!/usr/bin/env python3
"""WCAG 2.2 AA markup fixes for the flattened harambeecity.rrchnm.org copy.

Applied to every HTML file under harambeecity/ (chnm/sustainability #148). Idempotent.

- iframes get a title (4.1.2): videos from their oEmbed title, Social Explorer
  maps from the paragraph that introduces them
- Omeka's audio/video placeholder icons say what they link to instead of a bare
  filename (1.1.1, 2.4.4)
- comment gravatars are marked decorative (1.1.1)
- six Simple Pages whose Omeka title was a run of dots ("." / "...") get the
  title their navigation entry uses, in <title>, the h1 and the breadcrumbs (2.4.2)
- the home page slideshow can be paused and stops on prefers-reduced-motion (2.2.2)

Usage: harambeecity_a11y_pass.py [--dry-run] [site-dir]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "harambeecity"

VIDEO_TITLES = {
    "youtube.com/embed/HPOUDSxbrDs": "The Freedom Riders in Anniston, Alabama: Hank Thomas (TIME)",
    "youtube.com/embed/DAEsyMwVpmQ": "Open Mind round table with Malcolm X, James Farmer, Wyatt T. Walker and Alan Morrison",
    "youtube.com/embed/zGGls2gCETw": "The Brooklyn Congress of Racial Equality: a firsthand account from Lawrence Cumberbatch",
    "youtube.com/embed/LRKApBzO9C0": "Cicero March (1966, Film Group)",
    "youtube.com/embed/gc8-r97KZKk": "Interview with James Farmer (WashU Film and Media Archive)",
    "youtube.com/embed/awVQkvfZg8g": "Cleveland racial riots, 1960-1969 (British Pathé)",
    "youtube.com/embed/tKzwn02tsSg": "Carl Stokes speaking at UCLA, 1 November 1968",
    "youtube.com/embed/20bkuvMqPYM": "Dr. Martin Luther King Jr. in Cleveland, 1960s (WEWS archive)",
    "youtube.com/embed/COpm2Swvya8": "Dr. Nishani Frazier talks about Harambee City",
    "vimeo.com/video/155902501": "Louis Kelso's Second Income Plan, part one",
    "vimeo.com/video/176644664": "Louis Kelso's Second Income Plan, part two",
}

# Omeka page title -> the label its navigation entry uses
DOT_TITLES = {
    "about.html": (".", "Harambee City in Omeka and Layar"),
    "layar.html": ("..", "Why Layar?"),
    "to-display.html": ("...", "To Display"),
    "to-speak-outand-speak-back.html": ("....", "To Speak Out (And Speak Back)"),
    "to-unpackand-utilize.html": ("......", "To Unpack (And Utilize)"),
    "to-spread-out.html": (".......", "To Spread Out"),
}

IFRAME_RE = re.compile(r"<iframe\b[^>]*>", re.I)
GRAVATAR_RE = re.compile(r"<img class='gravatar' src='([^']*)' />")
FALLBACK_RE = re.compile(r'(<img\b[^>]*fallback-(audio|video)\.png"[^>]*\balt=")([^"]*)(")', re.I)
TAG_RE = re.compile(r"<[^>]+>")

SLIDESHOW_HTML = """<button type="button" id="slideshow-toggle" aria-pressed="false">Pause background slideshow</button>
"""
SLIDESHOW_JS = """<script type="text/javascript">
// a11y: the background slideshow must be pausable (WCAG 2.2.2); honour prefers-reduced-motion
(function () {
  var b = document.getElementById('slideshow-toggle');
  function set(paused) {
    $.backstretch(paused ? 'pause' : 'resume');
    b.setAttribute('aria-pressed', paused ? 'true' : 'false');
    b.textContent = (paused ? 'Play' : 'Pause') + ' background slideshow';
  }
  b.onclick = function () { set(b.getAttribute('aria-pressed') !== 'true'); };
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) { set(true); }
})();
</script>
</body>"""


def iframe_title(tag: str, before: str) -> str:
    m = re.search(r'src="?([^"\s>]+)', tag)
    src = m.group(1) if m else ""
    for key, title in VIDEO_TITLES.items():
        if key in src:
            return "Video: " + title
    if "socialexplorer.com" in src:
        # the paragraph before the embed introduces the map
        paras = re.findall(r"<p\b[^>]*>(.*?)</p>", before, re.S)
        for p in reversed(paras):
            text = re.sub(r"\s+", " ", TAG_RE.sub("", p)).strip()
            if text and len(text) > 3:
                text = re.split(r"(?<=[.?!])\s", text)[0].rstrip(".:")
                return "Map: " + text[:120]
        return "Map from Social Explorer"
    return "Embedded content"


def fix_iframes(text: str) -> str:
    out, pos = [], 0
    for m in IFRAME_RE.finditer(text):
        tag = m.group(0)
        out.append(text[pos:m.start()])
        if not re.search(r"\btitle=", tag, re.I):
            title = iframe_title(tag, text[max(0, m.start() - 3000):m.start()]).replace('"', "&quot;")
            tag = tag[:-1] + f' title="{title}">'
        out.append(tag)
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def fix_fallbacks(text: str) -> str:
    def repl(m):
        kind, alt = m.group(2).lower(), m.group(3)
        if alt.startswith(("Audio file:", "Video file:")) or not alt:
            return m.group(0)
        return f"{m.group(1)}{kind.capitalize()} file: {alt}{m.group(4)}"
    return FALLBACK_RE.sub(repl, text)


def fix_dot_titles(text: str, name: str) -> str:
    # the about page is linked as "." from every page's breadcrumbs
    text = re.sub(r'(<a href="(?:\.\./)*about\.html">)\.(</a>)', r"\1Harambee City in Omeka and Layar\2", text)
    if name in DOT_TITLES:
        dots, label = DOT_TITLES[name]
        d = re.escape(dots)
        text = re.sub(rf"<title>{d} &middot;", f"<title>{label} &middot;", text)
        text = re.sub(rf"<h1>{d}</h1>", f"<h1>{label}</h1>", text)
        text = re.sub(rf"&gt; {d}</p>", f"&gt; {label}</p>", text)
    return text


def fix_home(text: str) -> str:
    if "slideshow-toggle" in text:
        return text
    text = text.replace('<div id="backstretch"></div>', SLIDESHOW_HTML + '<div id="backstretch"></div>', 1)
    return text.replace("</body>", SLIDESHOW_JS, 1)


def process(text: str, rel: str) -> str:
    text = fix_iframes(text)
    text = fix_fallbacks(text)
    text = GRAVATAR_RE.sub(r'<img class="gravatar" src="\1" alt="" />', text)
    text = fix_dot_titles(text, rel)
    if rel == "index.html":
        text = fix_home(text)
    return text


def main() -> None:
    dry = "--dry-run" in sys.argv
    roots = [Path(a) for a in sys.argv[1:] if a != "--dry-run"] or [ROOT]
    changed = total = 0
    for root in roots:
        for p in sorted(root.rglob("*.html")):
            total += 1
            t = p.read_text(encoding="utf-8", errors="replace")
            n = process(t, p.relative_to(root).as_posix())
            if n != t:
                changed += 1
                if not dry:
                    p.write_text(n, encoding="utf-8")
    print(f"{'would change' if dry else 'changed'} {changed}/{total} html file(s)")


def _selfcheck() -> None:
    before = '<p>EDUCATION: This map overlays black areas. Note the dots.</p>\n<p><iframe width="1000" src="https://www.socialexplorer.com/c7f2d74936/embed"></iframe></p>'
    assert 'title="Map: EDUCATION: This map overlays black areas"' in fix_iframes(before)
    assert 'title="Video: Cicero March' in fix_iframes('<iframe src="https://www.youtube.com/embed/LRKApBzO9C0"></iframe>')
    t = fix_iframes('<iframe title="x" src="https://vimeo.com/video/1"></iframe>')
    assert t.count("title=") == 1
    f = fix_fallbacks('<img src="../fallback-audio.png" alt="stuart wechsler.MP3" title="stuart wechsler.MP3">')
    assert 'alt="Audio file: stuart wechsler.MP3"' in f and fix_fallbacks(f) == f
    d = fix_dot_titles('<title>... &middot; X</title><h1>...</h1><p><a href="about.html">.</a> &gt; ...</p>', "to-display.html")
    assert d == '<title>To Display &middot; X</title><h1>To Display</h1><p><a href="about.html">Harambee City in Omeka and Layar</a> &gt; To Display</p>', d


if __name__ == "__main__":
    _selfcheck()
    main()
