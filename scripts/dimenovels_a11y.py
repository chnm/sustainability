#!/usr/bin/env python3
"""WCAG 2.2 AA pass over the flattened American Women's Dime Novel Project (chnm/sustainability#155).

Every page shares one WordPress theme (Elegant Themes "Flexible"), so each fix is a regex over the same template:

- viewport allows zoom; a11y.css linked; skip link to #main-area, which becomes the main landmark
- the logo is a div (each page's own title is its h1); empty footer/sidebar headings and the footer's stray <li> fixed
- the mobile "Navigation Menu" link becomes a button outside the main area (custom.js puts the menu after it,
  not inside it, and sets aria-expanded)
- the home slider no longer auto-advances (2.2.2), its slide dots are focusable, and its slide images no longer
  repeat the slide-title link
- the sidebar's title search, author/publisher filters and site search needed WordPress; they become browse links
- the cover gallery's AJAX "Next" (dead) points at the Books archive, which holds every cover
- Google Books cover links on the e-book pages, and four cover-gallery links, get alt text; one empty link goes
- dead trackers (Piwik on chnmdev, Universal Analytics) and the emoji loader, which hung window.load, are removed

Idempotent. Run from the repo root:  python3 scripts/dimenovels_a11y.py
"""
import html, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'dimenovels'
WIDGET = r'<div id="%s" class="widget[^"]*">.*?</div> <!-- end \.widget -->'
BROWSE = ('<div id="text-3" class="widget widget_text"><h4 class="widgettitle">Find a Book</h4>\t\t\t<div class="textwidget"><ul class="browse-links">'
          '<li><a href="{up}books.html">All books</a></li><li><a href="{up}the-authors.html">By author</a></li>'
          '<li><a href="{up}the-publishers.html">By publisher</a></li></ul></div>\n\t\t</div> <!-- end .widget -->')
DEAD = [r'<script[^>]*>\s*window\._wpemojiSettings.*?</script>\s*',
        r'<style type="text/css">\s*img\.wp-smiley.*?</style>\s*',
        r'<!-- Google Analytics Tracking by Google Analyticator.*?ga\(\'send\', \'pageview\'\);\s*</script>\s*',
        r'<!-- Piwik -->.*?<!-- End Piwik Code -->\s*',
        r"<script[^>]*google-analyticator/external-tracking[^>]*></script>\s*"]


def ebook_alt(m):
    """Google Books rows: <a><img/></a></td><td><p><b>Title</b> -> the image names the link."""
    title = html.unescape(re.sub('<[^>]+>', '', m.group(3))).strip()
    return '%s alt="%s, on Google Play" src=\'https://%s' % (m.group(1), html.escape(title), m.group(2))


# theme scripts shared by every page: (file, old, new)
THEME = [
    ('wp/wp-content/themes/Flexible/js/custom.js',
     "$main_menu.clone().attr('id','mobile_menu').removeClass().appendTo( $et_mobile_nav_button );\n\t\t$cloned_nav = $et_mobile_nav_button.find('> ul');",
     "$main_menu.clone().attr('id','mobile_menu').removeClass().insertAfter( $et_mobile_nav_button );   // a11y: menu follows the button, not inside it\n"
     "\t\t$cloned_nav = $('#mobile_menu');\n\t\t$et_mobile_nav_button.attr('aria-controls', 'mobile_menu');"),
    ('wp/wp-content/themes/Flexible/js/custom.js',
     "$(this).removeClass( 'closed' ).addClass( 'opened' );", "$(this).removeClass( 'closed' ).addClass( 'opened' ).attr( 'aria-expanded', 'true' );"),
    ('wp/wp-content/themes/Flexible/js/custom.js',
     "$(this).removeClass( 'opened' ).addClass( 'closed' );", "$(this).removeClass( 'opened' ).addClass( 'closed' ).attr( 'aria-expanded', 'false' );"),
    ('wp/wp-content/themes/Flexible/js/custom.js',   # threw on every resize: this theme has no featured slider
     "if ( ! $featured.is(':visible') ) et_slider.pause();", "if ( ! $featured.is(':visible') && et_slider ) et_slider.pause();"),
] + [(js, 'e.append("<li><a>"+s+"</a></li>")', 'e.append(\'<li><a href="#" aria-label="Slide \'+s+\'">\'+s+"</a></li>")')
       for js in ('wp/wp-content/plugins/responsive-slider/responsive-slider.js',   # slide dots were <a> without href: not focusable;
                  'wp/wp-content/themes/Flexible/js/jquery.flexslider-min.js')]   # the theme's copy loads last and wins


def book_title(rel):
    return re.search(r'<h1 class="page_title">(.*?)</h1>', (ROOT / rel).read_bytes().decode('utf-8')).group(1).strip()


def fix(s, up):
    s = s.replace('content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0"', 'content="width=device-width, initial-scale=1.0"')
    if 'a11y.css' not in s:
        s = s.replace('</head>', '<link rel="stylesheet" href="%sa11y.css" type="text/css" />\n</head>' % up, 1)
    if 'class="skip-link"' not in s:
        s = re.sub(r'(<body[^>]*>)', r'\1\n<a class="skip-link" href="#main-area">Skip to content</a>', s, count=1)
    for pat in DEAD:
        s = re.sub(pat, '', s, flags=re.S)

    # headings and landmarks
    if 'page_title' in s:   # pages without a title heading (home, archives) keep the logo as their h1
        s = re.sub(r'<h1 id="logo">(.*?)</h1>', r'<div id="logo">\1</div>', s, flags=re.S)
    s = s.replace('<nav id="top-menu">', '<nav id="top-menu" aria-label="Main">')
    s = re.sub(r'<li class="widget"><h2 class="widgettitle"> </h[23]>(.*?)</li>(\s*<p id="copyright")', r'<div class="widget">\1</div>\2', s, flags=re.S)
    s = re.sub(r'<div id="main-area">\s*<a href="[^"]*#" id="mobile_nav" class="closed"><span></span>Navigation Menu</a>',
               '<nav id="mobile_nav_wrap" aria-label="Main (small screens)"><button type="button" id="mobile_nav" class="closed" aria-expanded="false">'
               '<span></span>Navigation Menu</button></nav>\n\t\t<div id="main-area" role="main" tabindex="-1">', s)

    # sidebar: dead WordPress forms -> browse links
    if 'class="browse-links"' not in s:
        s = re.sub(WIDGET % 'text-3', lambda m: BROWSE.format(up=up), s, flags=re.S)
    s = re.sub(WIDGET % 'wp_views_filter-2', '', s, flags=re.S)
    s = re.sub(WIDGET % 'search-4', '', s, flags=re.S)
    s = re.sub(r'<script type="text/javascript">\s*jQuery\(document\)\.on\(\'ready\', function\(\)\{\s*jQuery\(\'#wpv_control_select_book_author.*?</script>\s*', '', s, flags=re.S)

    # home slider: no autoplay; one link per slide (the title), image alt left for the alt-text pass
    s = s.replace('"start":"1"', '"start":"0"')
    s = re.sub(r'(<div id="slide-\d+" class="slide">)<a href="[^"]*" title="[^"]*" >(<img [^>]*>)</a>', r'\1\2', s)

    # cover gallery: AJAX pagination -> Books archive
    s = re.sub(r'Showing page 1 of 9\s*<a href="cover-gallery\.html#" class="wpv-filter-next-link"[^>]*>Next</a>',
               'More covers: <a href="books.html">browse all books</a>', s)

    # an empty duplicate link after a real one (the-authors/laura-jean-libbey.html)
    s = re.sub(r'<a href="[^"]*"[^>]*>((?:&nbsp;|\s)*)</a>', r'\1', s)

    # cover gallery: four covers uploaded in 2015 have alt="" inside their only link; give them the book's title
    s = re.sub(r'(<a href="(books/[^"]+\.html)"><img [^>]*alt=)""', lambda m: '%s"%s"' % (m.group(1), book_title(m.group(2))), s)

    # images for the alt-text pass (utils/alt-text flags only missing or filename alts): drop slug alts
    # ("A-Dark-Marriage-Morn"), each book page's cover alt that only repeats its h1, and alt="" on two slider
    # images and the Street & Smith page's cover, which pointed at the live site's never-crawled covers/ folder
    s = s.replace('https://chnm.gmu.edu/dimenovels/covers/a_sinful_secret_tm.jpg', up + 'wp/wp-content/uploads/2013/04/a_sinful_secret_tm.jpg')
    s = re.sub(r'(<img [^>]*?)\s*alt=(["\'])(?=[^"\' ]*[-_])[\w.-]+\2', r'\1', s)   # also belles_tm, miller_smaller
    s = re.sub(r'(<img [^>]*?(?:slide1\.png|slide4\.jpg|a_sinful_secret_tm\.jpg)"[^>]*?)\s*alt=""', r'\1', s)
    title = re.search(r'<h1 class="page_title">(.*?)</h1>', s)
    if title and up == '../' and '<div id="slide-' not in s:
        s = re.sub(r"(<img src=\"\.\./wp/wp-content/uploads/et_temp/[^\"]*_320x480\.jpg\") alt='%s'" % re.escape(title.group(1).strip()), r'\1', s)

    # e-book pages: Google Books cover links
    s = re.sub(r"(<img style='[^']*') src='http://(books\.google\.com/books/content\?[^']*'/></a> </td><td style='vertical-align:middle;'><p>)<b>(.*?)</b>",
               lambda m: ebook_alt(m) + '<b>' + m.group(3) + '</b>', s)
    return s


def main():
    for rel, old, new in THEME:
        p = ROOT / rel
        s = p.read_text()
        if new not in s:
            assert s.count(old) == 1, (rel, old)
            p.write_text(s.replace(old, new))
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        rel = p.relative_to(ROOT).as_posix()
        up = '../' * rel.count('/')
        old = p.read_bytes().decode('utf-8')
        new = fix(old, up)
        assert fix(new, up) == new, rel   # idempotent
        if new != old:
            p.write_bytes(new.encode('utf-8'))
            n += 1
    print('updated %d pages' % n)


if __name__ == '__main__':
    main()
