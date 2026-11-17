# sonicmemorial.org

The Sonic Memorial Project (NPR's Lost & Found Sound, Picture Projects, dotsperinch and others, 2002–2004):
an audio archive and online sound installation about the life and history of the World Trade Center and 9/11.
Dreamweaver-era static HTML with Netscape 4 scripts, a Flash "Sonic Browser" and a JSP archive. Tracked in
chnm/sustainability#156. Nothing in MARS; this copy comes from the live site.

## wget

Crawled on 2026-11-17 from `https://sonicmemorial.org/` in four passes, all into one tree. The site opens most
of its pages and every recording through JavaScript (`Pop()`, `Pop2()`, `open_window()`, `openBrowserWindow()`,
`assetsWindow('…mp3')`), which wget does not follow, so passes 2–4 seed wget with those targets.

**Pass 1** (13:22:30–13:24:17): 171 files, 51M

```
wget --mirror --page-requisites --convert-links --adjust-extension --no-parent -e robots=off --wait=0.5 --random-wait --tries=3 https://sonicmemorial.org/
```

**Pass 2** (13:25:14–13:26:36): 102 files, 1.1M. Seeds: every `Pop()`/`Pop2()`/`window.open()`/`<option value>`
target, resolved against its page, repeated until no new seed appeared (21 seeds, two rounds). `--no-parent` is
dropped because seeds sit in sub-directories but load `../images/`; wget stays on the host either way.

```
wget --mirror --page-requisites --convert-links --adjust-extension -e robots=off --wait=0.5 --random-wait --tries=3 -i seeds.txt
```

**Pass 3** (13:27:41–13:31:21): 242 files, 84M. Same command; seeds are every quoted `.mp3`, `.html`, `.gif`, `.jpg`
etc. path in HTML and JS (slide pop-ups, rollover images, `assetsWindow()` audio), repeated until closure.

**Pass 4**: five files by hand. `educators_mod_ideals.html` links `edu_audio/civicideals/child_{103,155,210,263,363}.mp`;
the `.mp3` files exist on the server and were fetched with `wget -x -nH`.

**Result:** 515 files, 138M (86 HTML pages, 101 MP3, 159 GIF, 143 JPEG, 22 press-kit zip/sit archives).

**Responses** (all passes)

| 2xx | 304 | 4xx | 5xx |
|-----|-----|-----|-----|
| 520 | 21  | 124 (31 unique) | 0 |

### Failures (31 unique URLs, all 404)

| url | referenced from |
|-----|-----------------|
| `public/sm_browser.html` | `sm_detector.html` (the Flash Sonic Browser) |
| `alt_content/index.html` | `sm_detector.html` (its no-Flash fallback) |
| `audio/captain.mp3`, `audio/elevator.mp3`, `audio/hingson.mp3`, `audio/swoman.mp3` | image map on `stewardesses/stewardess.html` |
| `SMSgiasante1.mp3` | `stations.html` |
| `audio/RHOVERTHESIDEBOUNCE1.MP3` | `mohawk/mohawk.html` |
| `edu_audio/civicideals/child_{103,155,210,263,363}.mp` | `educators_mod_ideals.html` (typo; `.mp3` fetched, see pass 4) |
| `images/nav/rrchnm_logo.png` | the RRCHNM banner already on every page |
| `images/spacer_left.gif`, `images/leer.gif`, `images/mp3.gif`, `freshkills/untitled-1.gif`, `radiorow/images/stories_mp3.gif`, `stewardesses/images/stories_mp3.gif` | layout and icon images |
| `press/images/sm1.jpg`, `sm1.zip`, `sm1.sit`, `sm2.jpg`, `sm2.zip`, `sm2.sit`, `press/images/spacer.gif` | `press/banners.html` |
| `press/www.picture-projects.com/bosnia.html` | `press/release082603.html` (missing `http://`) |
| `<list:prevLink/>`, `<list:nextLink/>`, `radiorow/+assetURL+` | unrendered JSP tags and a JS string, not real URLs |

## Media inventory

| what | count | state |
|------|------:|-------|
| MP3 recordings (`audio/`, `artists/audio/`, `freshkills/audio/`, `edu_audio/*/`) | 101 files, 86 MB, 213 min | Saved. All MPEG-1/2 layer III, playable natively. Opened through `assetsWindow()`, a pop-up that `document.write`s an `<EMBED>`. |
| MP3 links that 404 | 6 | Lost on the live server; not in the Wayback Machine (checked 2026-11-17). |
| RealAudio (`.ram`/`.rm`) | 21 unique links on 6 pages | All dead: `stream.realimpact.net` and `real20.audiovideoweb.com` no longer resolve; `www.npr.org/ramfiles/…` return 404. Not recoverable. |
| Flash | 1: the Sonic Browser (`sm_browser.swf`, Flash 6) | `sm_detector.html` sends visitors to `public/sm_browser.html`, which 404s. The SWF survives in the Wayback Machine (2017-05-02, 271 KB), but it loads its sounds from `init.jsp`/`su2xml.jsp` on the dead server. Not recoverable. |
| JSP archive (`archive.jsp`, `add_story_sound.jsp`, `contact_us.jsp`) | 3 | The server sends the JSP source unexecuted, so the searchable archive of contributed sounds is gone. |
| Windows Media, QuickTime, Shockwave | 0 | None referenced. |
| Press kit (`press/images/*.zip`, `*.sit`) | 22 | Saved. TIFF photos with `captions.txt`, PICT Sonic Browser screenshots, EPS logos. |

**Transcripts:** none. No page on the site contains the word "transcript", and no recording has a text version.

Matomo (`stats.rrchnm.org`, site 102) and the RRCHNM static-copy banner were already on the live pages.
