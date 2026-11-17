#!/usr/bin/env python3
"""WCAG 2.2 AA fixes for the static copy of locallinkages.org (chnm/sustainability#152).

Per page: links locallinkages/a11y.css after the theme stylesheet plus a11y.js (menu button aria-expanded), adds a
skip link to <main id="main-content"> (on the home page, the hero, which was a second role="banner" <header>,
becomes that target), removes
whitespace-only title attributes, turns the "Estimated time" <h6> lines into paragraphs and drops empty <h6>s, and
gives the content tables row headers (the 1.2 question table also gets a caption and column headers). Idempotent.
Run from the repo root:  python3 scripts/locallinkages_a11y.py
"""
import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'locallinkages'
SKIP = '<a class="skip-link" href="#main-content">Skip to main content</a>\n'


def row_headers(table):
    # a row whose only cell spans the table is a note, not a labelled row
    return re.sub(r'(<tr[^>]*>\s*)<td(?![^>]*colspan)([^>]*)>(.*?)</td>', r'\1<th scope="row"\2>\3</th>', table, flags=re.S)


def question_table(table):
    """1.2: first row is a caption, second row holds the column headers."""
    table = re.sub(r'<tbody>\s*<tr>\s*<td colspan="3">(.*?)</td>\s*</tr>', r'<caption>\1</caption>\n<tbody>', table, flags=re.S)
    table = re.sub(r'(<tbody>\s*<tr>)(.*?)(</tr>)',
                   lambda m: m.group(1) + re.sub(r'<td>(.*?)</td>', r'<th scope="col">\1</th>', m.group(2)) + m.group(3),
                   table, count=1, flags=re.S)
    head, sep, rest = table.partition('</tr>')
    return head + sep + row_headers(rest)


def fix(doc, rel):
    if 'a11y.css' not in doc:
        doc = re.sub(r"(<link rel='stylesheet' id='main-stylesheet-css'[^>]*>\n)",
                     lambda m: m.group(1) + "<link rel='stylesheet' id='a11y-css' href='%sa11y.css' type='text/css' media='all' />\n" % rel, doc)
    if 'a11y.js' not in doc:
        doc = re.sub(r"(<link rel='stylesheet' id='a11y-css'[^>]*>\n)",
                     lambda m: m.group(1) + "<script src='%sa11y.js' defer></script>\n" % rel, doc)
    if 'class="skip-link"' not in doc:
        doc = re.sub(r'(<body[^>]*>\n?)', lambda m: m.group(1) + SKIP, doc, count=1)
    doc = re.sub(r'<main class="(main-content[^"]*)">', r'<main id="main-content" class="\1">', doc)
    # Home page: the theme styles `.home > .benefits`, so a <main> wrapper would break it. The hero (a second
    # banner) becomes the skip-link target instead.
    doc = re.sub(r'<header class="front-hero" role="banner">(.*?)</header>', r'<div id="main-content" class="front-hero">\1</div>', doc, flags=re.S)
    doc = re.sub(r'\s+title="\s*"', '', doc)
    doc = re.sub(r'<h6>((?:<[^>]+>)*Estimated time.*?)</h6>', r'<p class="ll-time">\1</p>', doc)
    doc = re.sub(r'<h6>\s*</h6>\n?', '', doc)
    if '<th' not in doc:
        if 'Topic: the arrival of a new group' in doc:
            doc = re.sub(r'<table>.*?</table>', lambda m: question_table(m.group(0)), doc, flags=re.S)
        else:
            doc = re.sub(r'<table>.*?</table>', lambda m: row_headers(m.group(0)), doc, flags=re.S)
    return doc


def main():
    n = 0
    for p in sorted(ROOT.rglob('*.html')):
        rel = os.path.relpath(ROOT, p.parent).replace(os.sep, '/')
        rel = '' if rel == '.' else rel + '/'
        old = p.read_bytes().decode('utf-8')
        new = fix(old, rel)
        if new != old:
            p.write_bytes(new.encode('utf-8'))
            n += 1
    print('fixed %d pages' % n)


if __name__ == '__main__':
    t = '<table>\n<tbody>\n<tr>\n<td>A</td>\n<td>b</td>\n</tr>\n</tbody>\n</table>'
    assert row_headers('<tr>\n<td colspan="2">n</td>\n</tr>') == '<tr>\n<td colspan="2">n</td>\n</tr>'
    assert row_headers(t).count('<th scope="row">A</th>') == 1 and '<td>b</td>' in row_headers(t)
    q = question_table('<table>\n<tbody>\n<tr>\n<td colspan="3">Topic: x</td>\n</tr>\n<tr>\n<td>C</td>\n<td>Q</td>\n</tr>\n<tr>\n<td>r</td>\n<td>d</td>\n</tr>\n</tbody>\n</table>')
    assert '<caption>Topic: x</caption>' in q and '<th scope="col">C</th>' in q and '<th scope="row">r</th>' in q and '<td>d</td>' in q
    assert fix(fix('<h6>Estimated time: 4</h6>', ''), '') == '<p class="ll-time">Estimated time: 4</p>'
    main()
