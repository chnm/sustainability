#!/usr/bin/env python3
"""Replace plug-in content on the flattened dohistory.org with HTML that works today (chnm/sustainability#147).

- film/*.html: QuickTime <embed> clips -> <video> playing media/*.mp4 (transcoded from the .mov with ffmpeg)
- diary/exercises/tryTranscribing.html, two_stories/conclusion.html: QuickTime audio -> <audio> (mp3)
- man-midwife/index.html: the Shockwave cartoon -> the still image from index_alt.html, with a note
- home.html: the "If you're interested in..." submenu opens on keyboard focus and its links accept Enter
- diary/exercises/lens/index.html: the Java "Magic Lens" applet -> an HTML/CSS/JS lens that also works
  from the keyboard and on touch screens, plus a link to the plain transcription

Idempotent. Run from the repo root:  python3 scripts/dohistory_media.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dohistory'
ENC = 'latin-1'
FONT = '<font face="Arial, Helvetica, sans-serif" size="-1">'


def edit(rel, fn):
    p = ROOT / rel
    doc = p.read_bytes().decode(ENC)   # bytes: keep the old Mac CR line endings as they are
    new = fn(doc)
    if new != doc:
        p.write_bytes(new.encode(ENC))
        print('updated', rel)


def film(doc):
    m = re.search(r'<embed src="media/(\w+)\.mov" width="240" height="196"[^>]*>\s*</embed>', doc)
    if not m:
        return doc
    clip = m.group(1)
    video = ('<video controls preload="metadata" width="480" height="360" style="max-width:100%%;height:auto;background:#000">'
             '<source src="media/%s.mp4" type="video/mp4">'
             'Your browser cannot play this video. <a href="media/%s.mov">Download the QuickTime file</a>.</video>' % (clip, clip))
    doc = doc[:m.start()] + video + doc[m.end():]
    return re.sub(r'QuickTime plug-in\s+3\.0 or later is required to view this clip\.\s*<a href="http://www\.apple\.com/quicktime/download/">Download\s+it here</a>\.',
                  'This clip plays in the browser. The original QuickTime file is <a href="media/%s.mov">%s.mov</a>.' % (clip, clip), doc)


def audio(src, label):
    def fn(doc):
        return re.sub(r'<embed src="media/%s\.mov"[^>]*>\s*</embed>' % re.escape(src),
                      '<audio controls preload="none" src="media/%s.mp3" aria-label="%s"></audio>' % (src, label), doc, flags=re.I)
    return fn


def shockwave(doc):
    alt_src = (ROOT / 'man-midwife/index_alt.html').read_text(ENC)
    img = re.search(r'<img src="images/midwife\.jpg"[^>]*>', alt_src).group(0)
    note = ('<p>%sThe interactive Shockwave version of this cartoon no longer runs in current browsers, '
            'so the still image is shown here. The text below describes the items it pointed out.</font></p>' % FONT)
    return re.sub(r'<object classid="clsid:166B1BCA[^"]*".*?</object>', img + note, doc, count=1, flags=re.S)


LENS_HTML = '''<style>
.lens-stage { position: relative; display: block; width: 520px; max-width: 100%; overflow: hidden; cursor: crosshair; touch-action: none; background: #222; }
.lens-stage img { display: block; width: 100%; height: auto; }
.lens-stage:focus { outline: 3px solid #ffcc33; outline-offset: 2px; }
#lens-box { position: absolute; left: 0; top: 0; border: 2px solid #ffcc33; box-shadow: 0 0 0 1px #333366, 0 0 10px rgba(0,0,0,.7); background-repeat: no-repeat; pointer-events: none; box-sizing: border-box; }
.lens-controls button { font: 14px Arial, Helvetica, sans-serif; padding: 6px 10px; margin: 0 6px 6px 0; min-height: 32px; cursor: pointer; }
.lens-controls img { vertical-align: middle; }
</style>
<p id="lens-help">''' + FONT + '''Move the mouse or your finger over the page, or focus the page and use the arrow keys, to move the lens.
Change its size with the buttons below or the + and - keys. Rotate the page with the rotate buttons or the R key.</font></p>
<div id="lens-stage" class="lens-stage" tabindex="0" role="application" aria-label="Magic lens over the diary page for December 23, 1789" aria-describedby="lens-help">
<img id="lens-page" src="withoutlens_n.jpg" width="520" height="685" alt="Martha Ballard's handwritten diary page for December 23, 1789">
<div id="lens-box" aria-hidden="true"></div>
</div>
<p class="lens-controls">
<button type="button" id="lens-smaller">Smaller lens</button>
<button type="button" id="lens-larger">Larger lens</button>
<button type="button" id="lens-left"><img src="r_left.gif" width="70" height="20" alt="Rotate page left"></button>
<button type="button" id="lens-right"><img src="r_right.gif" width="70" height="20" alt="Rotate page right"></button>
</p>
<p id="lens-status" class="visually-hidden" aria-live="polite"></p>
<p>''' + FONT + '''Prefer plain text? <a href="../../1789/12/17891223_txt.html">Read the transcription of this diary page</a>.</font></p>
<script>
(function () {
  var order = ['n', 'e', 's', 'w'], o = 0;
  var sizes = { n: [520, 685], e: [685, 520], s: [520, 685], w: [685, 520] };
  var st = { x: 150, y: 220, w: 220, h: 120 };
  var stage = document.getElementById('lens-stage'), page = document.getElementById('lens-page');
  var box = document.getElementById('lens-box'), status = document.getElementById('lens-status');
  function render() {
    var W = sizes[order[o]][0], H = sizes[order[o]][1];
    stage.style.width = W + 'px';
    var scale = stage.clientWidth / W;
    stage.style.height = Math.round(H * scale) + 'px';
    if (page.getAttribute('src') !== 'withoutlens_' + order[o] + '.jpg') { page.src = 'withoutlens_' + order[o] + '.jpg'; page.width = W; page.height = H; }
    st.w = Math.max(60, Math.min(st.w, W)); st.h = Math.max(40, Math.min(st.h, H));
    st.x = Math.max(0, Math.min(st.x, W - st.w)); st.y = Math.max(0, Math.min(st.y, H - st.h));
    box.style.left = st.x * scale + 'px'; box.style.top = st.y * scale + 'px';
    box.style.width = st.w * scale + 'px'; box.style.height = st.h * scale + 'px';
    box.style.backgroundImage = 'url(withlens_' + order[o] + '.jpg)';
    box.style.backgroundSize = W * scale + 'px ' + H * scale + 'px';
    box.style.backgroundPosition = (-st.x * scale) + 'px ' + (-st.y * scale) + 'px';
  }
  function say(t) { status.textContent = t; }
  function grow(d) { st.w += 30 * d; st.h += 20 * d; st.x -= 15 * d; st.y -= 10 * d; render(); say('Lens is now ' + st.w + ' by ' + st.h + ' pixels.'); }
  function rotate(d) { o = (o + d + 4) % 4; render(); say('Page rotated. Its top now points ' + { n: 'up', e: 'right', s: 'down', w: 'left' }[order[o]] + '.'); }
  stage.addEventListener('pointermove', function (e) {
    if (e.pointerType === 'touch' && !e.buttons) return;
    var r = stage.getBoundingClientRect(), scale = stage.clientWidth / sizes[order[o]][0];
    st.x = (e.clientX - r.left) / scale - st.w / 2; st.y = (e.clientY - r.top) / scale - st.h / 2; render();
  });
  stage.addEventListener('keydown', function (e) {
    var step = e.shiftKey ? 40 : 10, k = e.key;
    if (k === 'ArrowLeft') st.x -= step; else if (k === 'ArrowRight') st.x += step;
    else if (k === 'ArrowUp') st.y -= step; else if (k === 'ArrowDown') st.y += step;
    else if (k === '+' || k === '=') { grow(1); } else if (k === '-' || k === '_') { grow(-1); }
    else if (k === 'r' || k === 'R') { rotate(1); } else return;
    e.preventDefault(); render();
  });
  document.getElementById('lens-smaller').onclick = function () { grow(-1); };
  document.getElementById('lens-larger').onclick = function () { grow(1); };
  document.getElementById('lens-left').onclick = function () { rotate(-1); };
  document.getElementById('lens-right').onclick = function () { rotate(1); };
  window.addEventListener('resize', render); page.addEventListener('load', render); render();
})();
</script>'''


def lens(doc):
    if 'lens-stage' in doc:
        return doc
    doc = re.sub(r'<table cellspacing="0" cellpadding="0">\s*<tr>\s*<td width="685">\s*<applet .*?</applet>\s*</td>\s*<tr>\s*</table>', LENS_HTML, doc, count=1, flags=re.S)
    doc = re.sub(r'<p>\s*<br>\s*<font face="Arial, Helvetica, sans-serif">Note: This page uses a java\s+applet.*?</font>\s*</p>',
                 '<p><br><font face="Arial, Helvetica, sans-serif">Note: the original Magic Lens was a Java applet. This page now uses a version '
                 'built into the page, so nothing needs to be installed.</font></p>', doc, count=1, flags=re.S)
    doc = doc.replace('You can change the size of the lens box by clicking on an \n        edge and dragging it.',
                      'You can change the size of the lens box with the buttons below it.')
    return re.sub(r'You can change the size of the lens box by clicking on an\s+edge and dragging it\.',
                  'You can change the size of the lens box with the buttons below it.', doc)


def home_menu(doc):
    """The "If you're interested in..." submenu only worked with a mouse: its links refused clicks unless hovered
    and stayed invisible on focus. Show it on focus and let the links work."""
    doc = doc.replace(' onClick="return (menu_active)"', '')
    if 'onBlur="deactivateMenu()"' in doc:
        return doc
    doc = re.sub(r'(<A HREF="interests/i_[^"]+")', r'\1 onFocus="menu_active = true; activateMenu()" onBlur="deactivateMenu()"', doc)
    heading = ' onFocus="menu_active = true; activateMenu(true); rollOver(\'interests_heading\',\'on\')"' \
              ' onBlur="deactivateMenu(); rollOver(\'interests_heading\',\'off\')"'
    return doc.replace('<A HREF="interests/index.html"', '<A HREF="interests/index.html"' + heading, 1)


def no_java(doc):
    return re.sub(r'<a href="diary/exercises/lens/index.html">Magic Lens</a>\s*\(requires\s+Java\)', '<a href="diary/exercises/lens/index.html">Magic Lens</a>', doc)


if __name__ == '__main__':
    for f in ('benpage', 'canoe', 'death', 'parade', 'rape', 'wakingup'):
        assert (ROOT / 'film/media' / (f + '.mp4')).exists(), f
        edit('film/%s.html' % f, film)
    edit('diary/exercises/tryTranscribing.html', audio('kaiulani', 'Kaiulani Lee reads part of this diary passage'))
    edit('two_stories/conclusion.html', audio('LTU_cryptic_entries', "Laurel Thatcher Ulrich on the diary's cryptic entries"))
    edit('man-midwife/index.html', shockwave)
    edit('diary/exercises/lens/index.html', lens)
    edit('sitemap.html', no_java)
    edit('home.html', home_menu)
