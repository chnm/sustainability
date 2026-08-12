/* axe-core audit of the 20.rrchnm.org archive, one page per structural variant.
 *
 * Real headless Chromium, not jsdom: jsdom cannot compute colour contrast
 * (1.4.3) or target size (2.5.8), and cannot run Pagefind's WebAssembly index.
 *
 *   cd 20.rrchnm.org && node tools/serve.js . 8765 &
 *   node tools/a11ycheck/run.js [http://localhost:8765]
 *
 * Exits non-zero if any WCAG 2.0/2.1/2.2 A or AA violation is found.
 *
 * Two things this archive needs that a stock runner does not:
 *
 *   1. URL ENCODING. wget baked query strings into filenames, so the tree
 *      holds real files called `browse?collection=1&page=3.html`. The '?' must
 *      reach the server as %3F or everything after it becomes a query string;
 *      '&' is encoded as %26 for the same reason.
 *
 *   2. HOST BLOCKING. Media lives in an object bucket that a local preview does
 *      not have, and Matomo and the CARTO basemap are live third parties. They
 *      are blocked so a sandboxed run audits the same DOM a connected one
 *      would, and so a missing bucket cannot look like an accessibility
 *      regression.
 */
const { chromium } = require('playwright');
const { AxeBuilder } = require('@axe-core/playwright');

const BASE = process.argv[2] || 'http://localhost:8765';

const BLOCK = [
  '**://stats.rrchnm.org/**',
  '**://*.basemaps.cartocdn.com/**',
  '**://20.rrchnm.org/**',
  '**://ajax.googleapis.com/**',
  '**://fonts.googleapis.com/**',
  '**://fonts.gstatic.com/**',
  '**://cdn.knightlab.com/**',
  '**://api.simile-widgets.org/**',
  '**://drive.google.com/**',
];

/* One page per body class x theme x structural variant, chosen so that every
   transform tools/retrofit.py performs is exercised at least once. */
const PAGES = [
  // Berlin -- chrome variants
  ['/index.html', 'home two-col (the only page that had no h1)'],
  ['/about.html', 'page simple-page (h1->h3 skip, <div> inside <p>)'],
  ['/about-this-site.html', 'page simple-page (plain prose)'],
  ['/search.html', 'site-wide Pagefind search'],

  // Berlin -- items
  ['/items/browse.html', 'items browse (two pagination navs, next only)'],
  ['/items/browse?collection=1&page=3.html', 'items browse (prev+next, was a duplicate id)'],
  ['/items?page=43.html', 'items browse (short last page)'],
  ['/items/browse/type/project.html', 'items browse by type'],
  ['/items/search.html', 'faceted Pagefind item search'],
  ['/items/show/341.html', 'items show (image, no collection, no geolocation)'],
  ['/items/show/62.html', 'items show + geolocation map'],
  ['/items/show/389.html', 'items show + <video>'],
  ['/exhibits/show/september-11-digital-archive/item/198.html',
   'items show + PDF <object> + Item Relations table + collection'],
  ['/items/tags.html', 'items tags (empty -- "No tags are available")'],
  ['/items/map.html', 'map browse (Leaflet, 55 markers)'],
  ['/collections/show/1.html', 'collections show'],
  ['/files/show/909.html', 'files show primary-secondary'],
  ['/neatline-time/timelines/show/1.html', 'timelines primary (static replacement)'],

  // Berlin -- exhibits
  ['/exhibits.html', 'exhibits browse (+ the recovered missing-image note)'],
  ['/exhibits/tags.html', "exhibits tags (the archive's only tag cloud)"],
  ['/exhibits/show/websites.html', 'exhibits summary (Berlin)'],
  ['/exhibits/show/making1989.html', 'exhibits summary (Berlin, h1->h3 skip)'],
  ['/exhibits/show/websites/1998.html', 'exhibits show (h1->h4, unclosed span, page nav)'],
  ['/exhibits/show/september-11-digital-archive/resources.html', 'exhibits show (prose headings)'],
  ['/exhibits/show/pwd/funding-preservation.html', 'exhibits show (guard case: already has h2)'],
  ['/exhibits/show/timeline.html', 'exhibits show (KnightLab embed replaced)'],

  // neatscape -- all 31 pages are one of these three shapes
  ['/exhibits/show/history-matters.html', 'neatscape exhibits summary (had two h1)'],
  ['/exhibits/show/the-lost-museum.html', 'neatscape exhibits summary'],
  ['/exhibits/show/the-lost-museum/building-the-lost-museum.html', 'neatscape exhibits show'],
  ['/exhibits/show/the-lost-museum/item/503.html', 'neatscape items show'],
];

const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

function encodePath(p) {
  // Encode only the characters that would otherwise be parsed as a query
  // string; leave the rest of the path readable in the report.
  return p.replace(/\?/g, '%3F').replace(/&/g, '%26');
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  for (const pattern of BLOCK) {
    await context.route(pattern, (route) => route.abort());
  }

  let failed = 0;
  const consoleErrors = [];

  for (const [path, label] of PAGES) {
    const page = await context.newPage();
    page.on('pageerror', (e) => consoleErrors.push([path, e.message]));
    const url = BASE + encodePath(path);
    let res;
    try {
      res = await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    } catch (e) {
      console.log(`[31mLOAD FAIL[0m ${path}  ${e.message}`);
      failed++;
      await page.close();
      continue;
    }
    if (!res || res.status() >= 400) {
      console.log(`[31mHTTP ${res ? res.status() : '?'}[0m ${path}`);
      failed++;
      await page.close();
      continue;
    }

    const results = await new AxeBuilder({ page })
      .withTags(TAGS)
      .analyze();

    const v = results.violations;
    if (v.length === 0) {
      console.log(`[32m  ok[0m  ${path}  [2m${label}[0m`);
    } else {
      failed++;
      console.log(`[31mFAIL[0m  ${path}  [2m${label}[0m`);
      for (const issue of v) {
        console.log(`        ${issue.id} (${issue.impact}) x${issue.nodes.length}` +
                    ` -- ${issue.help}`);
        for (const node of issue.nodes.slice(0, 3)) {
          console.log(`          ${node.target.join(' ')}`);
          const msg = (node.failureSummary || '').split('\n').slice(1, 3)
            .map((l) => l.trim()).filter(Boolean).join(' / ');
          if (msg) { console.log(`          [2m${msg}[0m`); }
        }
      }
    }
    await page.close();
  }

  if (consoleErrors.length) {
    console.log('\nUncaught page errors:');
    for (const [p, m] of consoleErrors) { console.log(`  ${p}: ${m}`); }
  }

  console.log(`\n${PAGES.length - failed}/${PAGES.length} pages clean`);
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
