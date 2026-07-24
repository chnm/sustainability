#!/usr/bin/env python3
"""
WCAG 2.2 AA remediation for the Occupy Archive static export.

Idempotent: safe to re-run. Operates on every *.html file (excluding .git).

Global template fixes
  - 3.1.1  Language of Page   : add lang/xml:lang to <html>
  - 1.4.4/1.4.10             : add responsive viewport meta
  - 1.1.1  Non-text Content   : add alt to the header logo image
  - 2.4.1  Bypass Blocks      : add a skip link + ARIA landmark roles
  - hardening                : upgrade http Google Fonts links to https

Per-anchor fix
  - 2.4.4 / 4.1.2 Link name   : give every image-only link an accessible name
                                (listing thumbnails inherit their item's title;
                                 download links / inline images get sensible names)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGO_SUFFIX_OLD = '9db742119491388f000e3770520a36f5.jpg" title="Occupy Archive" />'
LOGO_SUFFIX_NEW = '9db742119491388f000e3770520a36f5.jpg" alt="Occupy Archive" title="Occupy Archive" />'

CT_META = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1" />'

A_RE = re.compile(r'<a\b[^>]*>.*?</a>', re.I | re.S)
IMG_RE = re.compile(r'<img\b[^>]*>', re.I)
HREF_RE = re.compile(r'\bhref\s*=\s*"([^"]*)"', re.I)
ALT_RE = re.compile(r'\balt\s*=\s*"([^"]*)"', re.I)
TITLE_RE = re.compile(r'\btitle\s*=\s*"([^"]*)"', re.I)
CLASS_RE = re.compile(r'\bclass\s*=\s*"([^"]*)"', re.I)
PERMALINK_A_RE = re.compile(
    r'<a\b[^>]*\bclass="[^"]*\bpermalink\b[^"]*"[^>]*>(.*?)</a>', re.I | re.S)
TAG_STRIP_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')


def attr_escape(text):
    """Escape a run of text for use in a double-quoted HTML attribute.
    Leaves existing &entity; references intact (only bare & is escaped)."""
    text = re.sub(r'&(?!#?\w+;)', '&amp;', text)
    text = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return WS_RE.sub(' ', text).strip()


def visible_text(html):
    t = TAG_STRIP_RE.sub('', html)
    t = t.replace('&nbsp;', ' ')
    return t.strip()


def set_img_alt(img_tag, name):
    """Return img_tag with alt set to name (replacing an empty alt or adding one)."""
    if ALT_RE.search(img_tag):
        return ALT_RE.sub('alt="%s"' % name.replace('\\', '\\\\'), img_tag, count=1)
    return re.sub(r'<img\b', '<img alt="%s"' % name.replace('\\', '\\\\'), img_tag,
                  count=1, flags=re.I)


def make_anchor_fixer(permalink_map):
    def fix(m):
        anchor = m.group(0)
        # Anchor already has an accessible name of its own.
        if re.search(r'\baria-label\s*=', anchor, re.I):
            return anchor
        # Skip links with visible text.
        open_tag_end = anchor.index('>') + 1
        inner = anchor[open_tag_end:anchor.rindex('</a>')]
        if visible_text(inner):
            return anchor
        imgs = IMG_RE.findall(inner)
        if not imgs:
            return anchor
        # Already named via a non-empty img alt?
        if any((ALT_RE.search(t) and ALT_RE.search(t).group(1).strip()) for t in imgs):
            return anchor

        open_tag = anchor[:open_tag_end]
        href_m = HREF_RE.search(open_tag)
        href = href_m.group(1).strip() if href_m else ''
        cls_m = CLASS_RE.search(open_tag)
        cls = cls_m.group(1) if cls_m else ''
        first_img = imgs[0]
        title_m = TITLE_RE.search(first_img)

        # 1. Listing thumbnail: reuse the item's own title (same href permalink).
        if href in permalink_map and permalink_map[href]:
            name = permalink_map[href]
            new_inner = inner.replace(first_img, set_img_alt(first_img, name), 1)
            return open_tag + new_inner + '</a>'
        # 2. File download link.
        if 'download-file' in cls:
            return '<a aria-label="Download original file"' + anchor[2:]
        # 3. Featured item link on the home page.
        if 'image' in cls.split():
            return '<a aria-label="Featured archive item"' + anchor[2:]
        # 4. Inline image that carries its own title.
        if title_m and title_m.group(1).strip():
            name = attr_escape(title_m.group(1))
            new_inner = inner.replace(first_img, set_img_alt(first_img, name), 1)
            return open_tag + new_inner + '</a>'
        # 5. Fallback: name the link by its purpose (opens the image/target).
        return '<a aria-label="View image"' + anchor[2:]
    return fix


def build_permalink_map(s):
    m = {}
    for a in PERMALINK_A_RE.finditer(s):
        href_m = HREF_RE.search(a.group(0)[:a.group(0).index('>') + 1])
        if not href_m:
            continue
        title = attr_escape(visible_text(a.group(1)))
        if title:
            m[href_m.group(1).strip()] = title
    return m


def remediate(s):
    counts = {}

    def bump(k, before):
        if s_local[0] != before:
            counts[k] = counts.get(k, 0) + 1

    # --- global string fixes (each guarded for idempotency) ---
    s_local = [s]

    if 'lang="en"' not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace(
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">', 1)
        bump('lang', b)

    if VIEWPORT not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace(CT_META, CT_META + '\n' + VIEWPORT, 1)
        bump('viewport', b)

    if "http://fonts.googleapis.com/" in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace("http://fonts.googleapis.com/",
                                        "https://fonts.googleapis.com/")
        bump('fonts_https', b)

    if LOGO_SUFFIX_OLD in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace(LOGO_SUFFIX_OLD, LOGO_SUFFIX_NEW)
        bump('logo_alt', b)

    if '<div id="header" role=' not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace('<div id="header">',
                                        '<div id="header" role="banner">', 1)
        bump('role_banner', b)

    if '<div id="primary-nav" role=' not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace(
            '<div id="primary-nav">',
            '<div id="primary-nav" role="navigation" aria-label="Primary">', 1)
        bump('role_nav', b)

    if '<div id="primary" data-pagefind-body role=' not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace(
            '<div id="primary" data-pagefind-body>',
            '<div id="primary" data-pagefind-body role="main" tabindex="-1">', 1)
        bump('role_main', b)

    if '<div id="footer" role=' not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace('<div id="footer">',
                                        '<div id="footer" role="contentinfo">', 1)
        bump('role_contentinfo', b)

    if 'class="skip-link"' not in s_local[0]:
        b = s_local[0]
        s_local[0] = s_local[0].replace(
            '<div id="wrap">',
            '<a class="skip-link" href="#primary">Skip to main content</a>\n\t<div id="wrap">', 1)
        bump('skip_link', b)

    # --- per-anchor accessible names ---
    permalink_map = build_permalink_map(s_local[0])
    b = s_local[0]
    s_local[0] = A_RE.sub(make_anchor_fixer(permalink_map), s_local[0])
    if s_local[0] != b:
        counts['anchor_named'] = 1  # per-file flag; link total counted separately

    return s_local[0], counts


def main():
    totals = {}
    files_changed = 0
    anchor_links_named = 0
    # count individual links named for reporting
    for root, _, files in os.walk(ROOT):
        if '/.git' in root or root.endswith('/.git'):
            continue
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            with open(p, encoding='utf-8', errors='replace') as fh:
                s = fh.read()
            new, counts = remediate(s)
            if new != s:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(new)
                files_changed += 1
                for k, v in counts.items():
                    totals[k] = totals.get(k, 0) + v
    print("files changed:", files_changed)
    for k in sorted(totals):
        print("  %-18s %d" % (k, totals[k]))


if __name__ == '__main__':
    main()
