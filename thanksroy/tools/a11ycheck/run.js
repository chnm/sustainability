/*
 * WCAG 2.2 A/AA audit for the thanksroy.org static archive.
 *
 * Adapted from occupyarchive/tools/a11ycheck/run.js, but driven by a real
 * headless Chromium rather than jsdom. The archive needs it: jsdom cannot
 * compute colour contrast (1.4.3) or target size (2.5.8), and it cannot run
 * Pagefind's WebAssembly index, so the two search pages -- the whole point of
 * this retrofit -- would audit as empty shells.
 *
 * Serve the archive first, then point this at it:
 *
 *     cd thanksroy && python3 -m http.server 8765 &
 *     node tools/a11ycheck/run.js [http://localhost:8765]
 *
 * Requires a Chromium that playwright-core can launch:
 *     npx playwright install chromium && npx playwright install-deps chromium
 */
const path = require('path');
const axe = require('axe-core');
const { chromium } = require('playwright-core');

const BASE = process.argv[2] || 'http://localhost:8765';

// One page of every distinct type in the archive.
const PAGES = [
  { url: '/index.html', name: 'home' },
  { url: '/about.html', name: 'simple page' },
  { url: '/memorial-events.html', name: 'simple page (embedded HTML)' },
  { url: '/formal-notices.html', name: 'simple page' },
  { url: '/howtohelp.html', name: 'simple page' },
  { url: '/items.html', name: 'browse (root)' },
  { url: '/items/browse.html', name: 'browse + pagination' },
  { url: '/items/tags.html', name: 'tag cloud' },
  { url: '/items/show/614.html', name: 'item (image only)' },
  { url: '/items/show/697.html', name: 'item (text + collection + tags)' },
  { url: '/items/show/506.html', name: 'item ([Untitled])' },
  { url: '/collections/show/1.html', name: 'collection' },
  { url: '/search.html?query=roy', name: 'site search (with results)', settle: '.pagefind-ui__result' },
  { url: '/items/search.html', name: 'faceted item search', settle: '#facet-groups fieldset' },
  { url: '/items/search%3Fpage=5.html', name: 'redirect stub', stripRefresh: true },
];

const AA_TAGS = new Set(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']);

(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const ctx = await browser.newContext();

  // The archive still references these hosts; block them so a sandboxed or
  // offline run audits the same DOM a connected one would.
  await ctx.route('**://ajax.googleapis.com/**', r => r.abort());
  await ctx.route('**://stats.rrchnm.org/**', r => r.abort());
  await ctx.route('**://thanksroy.org/**', r => r.abort());

  let totalAA = 0;
  const bpTotals = {};

  for (const spec of PAGES) {
    const page = await ctx.newPage();
    try {
      if (spec.stripRefresh) {
        // The stub's <meta http-equiv="refresh" content="0;..."> fires before
        // axe can be injected. Audit the markup a reader would see if the
        // refresh did not fire -- which is what the visible fallback link is
        // there for -- by serving the same bytes without that one tag.
        const res = await ctx.request.get(BASE + spec.url);
        const html = (await res.text()).replace(/<meta http-equiv="refresh"[^>]*>/i, '');
        await page.setContent(html, { waitUntil: 'domcontentloaded' });
      } else {
        await page.goto(BASE + spec.url, { waitUntil: 'networkidle', timeout: 30000 });
      }
      if (spec.settle) {
        await page.waitForSelector(spec.settle, { timeout: 30000 });
        await page.waitForTimeout(500);
      }
      await page.addScriptTag({ path: path.join(__dirname, 'node_modules/axe-core/axe.min.js') });
      const res = await page.evaluate(async () => await window.axe.run(document, {
        resultTypes: ['violations', 'incomplete'],
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'],
        },
      }));

      const aa = res.violations.filter(v => v.tags.some(t => AA_TAGS.has(t)));
      const bp = res.violations.filter(v => !v.tags.some(t => AA_TAGS.has(t)));
      const contrast = (res.incomplete.find(i => i.id === 'color-contrast') || { nodes: [] }).nodes.length;
      totalAA += aa.length;

      console.log(`\n### ${spec.url}  (${spec.name})`);
      console.log(`  A/AA: ${aa.length} | best-practice: ${bp.length} | contrast-needs-review: ${contrast}`);
      for (const v of aa) {
        console.log(`  [AA] ${v.id} (${v.impact}) x${v.nodes.length} -- ${v.help}`);
        for (const n of v.nodes.slice(0, 3)) {
          console.log(`       ${n.target.join(' ')} :: ${(n.html || '').slice(0, 110)}`);
        }
      }
      for (const v of bp) {
        bpTotals[v.id] = (bpTotals[v.id] || 0) + v.nodes.length;
        console.log(`  [bp] ${v.id} x${v.nodes.length} -- ${v.help}`);
        console.log(`       ${(v.nodes[0].html || '').slice(0, 110)}`);
      }
    } catch (e) {
      console.log(`\n### ${spec.url}\n  ERROR: ${e.message.split('\n')[0]}`);
      totalAA += 1;
    } finally {
      await page.close();
    }
  }

  console.log(`\n==== TOTAL A/AA violations across ${PAGES.length} pages: ${totalAA} ====`);
  if (Object.keys(bpTotals).length) {
    console.log('best-practice totals:', JSON.stringify(bpTotals));
  }
  await browser.close();
  process.exit(totalAA ? 1 : 0);
})();
