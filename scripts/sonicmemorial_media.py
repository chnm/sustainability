#!/usr/bin/env python3
"""Replace dead plug-in and server-side media on the flattened sonicmemorial.org (chnm/sustainability#156).

- Every recording opened through javascript:assetsWindow('x.mp3') (a pop-up that document.write()s an <EMBED>)
  or linked straight to an .mp3 now plays in place in a native <audio controls> player. The MP3s are the
  originals; text links to them stay, pointing at the file. Speaker icons beside a text link become decoration.
- MP3 links that 404 on the live server lose their link and say the recording is no longer available.
- RealAudio (.ram/.rm) streams are all dead: the links become text marked as no longer available.
- educators_mod_ideals.html: the five edu_audio/civicideals/*.mp links get their missing "3".
- sm_detector.html (Flash detector for the Flash 6 Sonic Browser, whose page and JSP data feed are gone) becomes a
  page with a still of the browser from the press kit and a note on what was lost. The Flash detector and
  installer files go.
- archive.jsp.html (JSP source the server sends unexecuted) keeps its header and says the archive is gone.
- press/banners.html and add_story_sound.jsp.html, empty on the live site, say so.
- The orphaned <map> on stewardesses/stewardess.html (no image uses it; its four MP3s 404) goes.

Idempotent. Run from the repo root:  python3 scripts/sonicmemorial_media.py
"""
import html, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'sonicmemorial'
ENC = 'latin-1'                     # pages declare iso-8859-1/15; latin-1 round-trips every byte
ORIGIN = 'https://sonicmemorial.org/'
LOST = '<span class="sm-lost">%s</span>'

# players whose description is not next to them in the markup, written from the page around them
HAND_LABELS = {
    # artists/artist.html: the section heading and the sentence that introduces each clip
    'studio.mp3': 'Surprising Studios. Kevin and Jenn McCoy, Stephen Vitiello, Kristin Lucas and Nadine Robinson recall their reactions to their studios.',
    'barricades.mp3': 'Through the Barricades. Diane Ludin on security at the WTC and its effect on the artists\' studios.',
    'stream.mp3': 'A Stream of Audio and Ideas. The artists on how the building and its muzak sparked their work.',
    'breathing.mp3': 'Breathing of the Building. Stephen Vitiello and Kevin and Jenn McCoy on the ambient sounds of the towers.',
    'infrastructure.mp3': 'Engaging with Infrastructure. Kristin Lucas and Kevin and Jenn McCoy on working with the inner functions of the towers.',
    # mohawk/mohawk.html
    'peterstacypride.mp3': "Peter Stacey's Pride in the WTC (interview)",   # the Sonic Browser's title for this clip
    'kanasong.mp3': 'recording beside the Mohawk logo (kanasong.mp3)',
    'BradBonaparte.mp3': 'Brad Bonaparte, second recording',
}

A_RE = re.compile(r'<a\s([^>]*)>(.*?)</a>', re.I | re.S)


def read(p):
    return p.read_bytes().decode(ENC)   # bytes: keep the CRLF line endings as they are


def write(p, doc):
    if read(p) != doc:
        p.write_bytes(doc.encode(ENC))
        print('updated', p.relative_to(ROOT))


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def audio_src(attrs):
    """The MP3 an anchor plays, or None."""
    m = re.search(r'href="javascript:assetsWindow\(\'([^\']+\.mp3)\'', attrs, re.I) or \
        re.search(r'href="([^"]+\.mp3)"', attrs, re.I)
    return m.group(1) if m else None


def local(page, src):
    rel = src[len(ORIGIN):] if src.startswith(ORIGIN) else src
    target = (ROOT / rel) if src.startswith(ORIGIN) else (page.parent / rel)
    return target.resolve(), rel if src.startswith(ORIGIN) else src


def player(src, label):
    return ('<audio class="sm-audio" controls preload="none" src="%s" aria-label="%s">'
            '<a href="%s">Download the MP3</a></audio>' % (src, html.escape(label, quote=True).encode('ascii', 'xmlcharrefreplace').decode(), src))


def audio(page, doc):
    doc = re.sub(r"""(assetsWindow\('edu_audio/civicideals/child_\d+\.mp)"(?=>)""", r"""\g<1>3')" """.rstrip(), doc)
    with_text = set()
    for m in A_RE.finditer(doc):
        src = audio_src(m.group(1))
        if src and text(m.group(2)):
            with_text.add(src)

    def fix(m):
        attrs, inner = m.group(1), m.group(2)
        src = audio_src(attrs)
        inside_player = doc.rfind('<audio', 0, m.start()) > doc.rfind('</audio>', 0, m.start())
        if not src or inside_player or doc.startswith('<br><audio class="sm-audio"', m.end()):
            return m.group(0)
        label = text(inner)
        if not label and src in with_text:      # speaker icon next to a text link: decoration
            return re.sub(r'<img\b(?![^>]*\balt=)', '<img alt=""', inner, flags=re.I)
        path, src = local(page, src)
        if not path.exists():
            return inner + ' ' + LOST % '(This recording is no longer available.)' if label else LOST % 'Recording no longer available.'
        cls = re.search(r'\bclass="([^"]*)"', attrs, re.I)
        if label:
            return '<a href="%s"%s>%s</a><br>%s' % (src, ' class="%s"' % cls.group(1) if cls else '', inner, player(src, label))
        # image-only button ("Listen to MP3", a speaker icon in its own cell): label it from the text before it
        # in the same block, else the cell before, else the cell after, else by hand
        low = doc.lower()
        start = max(low.rfind(t, 0, m.start()) for t in ('<p', '<td', '<li'))
        cell = low.rfind('<td', 0, m.start())
        prev_cell = low.rfind('<td', 0, cell)
        nxt = re.search(r'<td\b[^>]*>(.*?)</td>', doc[m.end():], re.I | re.S)
        ctx = next((c for c in (text(doc[start:m.start()]), text(doc[prev_cell:cell]) if 0 <= prev_cell and '</tr' not in low[prev_cell:cell] else '',
                                text(nxt.group(1)) if nxt and '<tr' not in low[m.end():m.end() + nxt.start()] else '') if re.search(r'[A-Za-z]{3}', c)), '')
        ctx = HAND_LABELS.get(src.rsplit('/', 1)[-1], ctx)
        assert ctx, 'no label for %s on %s' % (src, page)
        return player(src, 'Listen: ' + ctx)
    return A_RE.sub(fix, doc)


def realaudio(doc):
    def fix(m):
        attrs, inner = m.group(1), m.group(2)
        if not re.search(r'href="[^"]*\.(ram|rm)\b', attrs, re.I):
            return m.group(0)
        if 'stories_realaudio' in inner:
            return LOST % 'The NPR RealAudio broadcast of this story is no longer available.'
        cls = re.search(r'\bclass="([^"]*)"', attrs, re.I)
        return '<span class="%s">%s</span> %s' % (cls.group(1) if cls else 'txt12BlueB', inner,
                                                  LOST % '(RealAudio stream, no longer available)')
    return A_RE.sub(fix, doc)


DETECTOR = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="iso-8859-1">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sonic Browser | The Sonic Memorial Project</title>
<link rel="stylesheet" href="styles.css" type="text/css">
<link rel="stylesheet" href="a11y.css" type="text/css">
</head>
<body bgcolor="#012666" text="#FFFFFF" link="#FF9933" vlink="#FF9933">
<a class="skip-link" href="#content">Skip to content</a>
<div class="sm-page">
<p><a href="index.html"><img src="images/sub_logo.gif" width="291" height="21" alt="The Sonic Memorial Project home"></a></p>
<h1 id="content" tabindex="-1">Sonic Browser</h1>
<p><img src="images/sonic_browser_still.jpg" width="720" height="556" alt="Screenshot of the Sonic Browser: orange and blue lines curve down a dark blue screen above the words SONIC BROWSER. Topic labels read CONSTRUCTION, IDENTITY, INTERNATIONAL and MOHAWK IRONWORKERS. Beside them a selected item, Peter Stacey's Pride in the WTC [Interview], shows a photograph of a man on a steel floor and the text: Kahnawake Mohawk ironworker Peter Stacey tells the story of returning to the WTC with his family as a tourist. He reflects on the pride he feels as a contributor to the towers' construction."></p>
<p>The Sonic Browser was the Sonic Memorial's online sound installation: a Flash 6 program in which each contributed
recording was a line. Moving across the lines played the sounds, and choosing one showed its title, images and
description, grouped by topics such as construction, identity, media and Windows on the World.</p>
<p>It no longer works. Browsers stopped running Flash in 2021, and the Sonic Browser loaded its recordings from a
database on the original server that has not survived, so neither the program nor the collection it played can be
shown here. The picture above is a screenshot from the project's 2003 press kit.</p>
<p>Many of the recordings were also published in the project's <a href="stories.html">stories</a> and
<a href="educators.html">lessons for educators</a>, where they still play.</p>
<p><a href="index.html">Back to the Sonic Memorial home page</a></p>
</div>
</body>
</html>
'''

STUB = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="iso-8859-1">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s | The Sonic Memorial Project</title>
<link rel="stylesheet" href="%(up)sstyles.css" type="text/css">
<link rel="stylesheet" href="%(up)sa11y.css" type="text/css">
</head>
<body bgcolor="#FFFEDC" text="#000033" link="#000033" vlink="#000066">
<a class="skip-link" href="#content">Skip to content</a>
<div class="sm-page txt12Blue">
<p><a href="%(up)sindex.html"><img src="%(up)simages/sub_logo.gif" width="291" height="21" alt="The Sonic Memorial Project home" style="background:#000033"></a></p>
<h1 id="content" tabindex="-1" class="txt16Orange">%(title)s</h1>
<p>%(body)s</p>
<p><a href="%(up)sindex.html">Back to the Sonic Memorial home page</a></p>
</div>
</body>
</html>
'''
STUBS = {
    'press/banners.html': ('Banners', 'This page offered web banners for linking to the Sonic Memorial Project. It was '
                           'already empty on the live site when this copy was made, and the banner images are lost.'),
    'add_story_sound.jsp.html': ('Add a Sound', 'This was the form for uploading recordings to the Sonic Memorial archive. '
                                 'The archive no longer accepts contributions, and the form was already gone from the '
                                 'live site when this copy was made.'),
}

ARCHIVE_NOTE = '''<!-- ******* CONTENT ******* -->
<TABLE BORDER=0 WIDTH=730 CELLPADDING=0 CELLSPACING=0>
<TR><TD WIDTH=35><IMG SRC="images/spacer.gif" WIDTH="35" HEIGHT="1" BORDER="0"></TD>
<TD CLASS="txt12Blue sm-archive-note">
<h1 id="content" tabindex="-1" class="txt16Orange">Archive</h1>
<p>The archive let visitors search and listen to the more than 1,000 stories, sounds and images contributed to the
Sonic Memorial Project. It ran on a database on the original server, which has not survived, so the archive cannot be
searched or played here.</p>
<p>Many of the recordings were published in the project's <a href="stories.html">stories</a> and
<a href="educators.html">lessons for educators</a>, where they still play.</p>
</TD></TR></TABLE>
'''


def archive(doc):
    if 'sm-archive-note' in doc:
        return doc
    doc = re.sub(r'\A.*?(?=<html)', '', doc, flags=re.S | re.I)        # JSP directives and useBean before <html>
    head, rest = doc.split('<!-- ******* SEARCH ******* -->', 1)
    return head + ARCHIVE_NOTE + '\n</div>\n</BODY>\n</HTML>\n'


def main():
    for p in sorted(ROOT.rglob('*.html')):
        doc = read(p)
        new = realaudio(audio(p, doc))
        if p.name == 'stewardess.html':
            new = re.sub(r'<map name="Map">.*?</map>\s*', '', new, flags=re.S | re.I)
        write(p, new)

    write(ROOT / 'sm_detector.html', DETECTOR.replace('\n', '\r\n'))
    for rel, (title, body) in STUBS.items():
        p = ROOT / rel
        write(p, STUB % {'title': title, 'body': body, 'up': '../' * rel.count('/')})
    write(ROOT / 'archive.jsp.html', archive(read(ROOT / 'archive.jsp.html')))

    for rel in ('Dispatcher.js', 'Dispatcher.vbs.html', 'install_flash', 'upgrade_flash'):
        p = ROOT / rel
        if p.is_dir():
            shutil.rmtree(p); print('removed', rel)
        elif p.exists():
            p.unlink(); print('removed', rel)

    # self-check
    for p in ROOT.rglob('*.html'):
        doc = read(p)
        assert 'assetsWindow(\'' not in re.sub(r'<script.*?</script>', '', doc, flags=re.S | re.I).replace('function assetsWindow', ''), p
        assert not re.search(r'href="[^"]*\.(ram|rm)\b', doc, re.I), p
        for src in re.findall(r'<audio [^>]*src="([^"]+)"', doc):
            assert (p.parent / src).exists(), (p, src)
    assert 'MM_FlashDispatch' not in read(ROOT / 'sm_detector.html')
    assert '<%' not in read(ROOT / 'archive.jsp.html')
    print('self-check ok')


if __name__ == '__main__':
    main()
