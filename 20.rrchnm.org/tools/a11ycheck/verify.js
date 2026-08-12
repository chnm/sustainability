/* Functional verification of the 20.rrchnm.org archive -- the things axe cannot
 * decide: does the map actually draw its markers, does search return sensible
 * results, can a keyboard reach the navigation, does the page box paginate.
 *
 *   cd 20.rrchnm.org && node tools/serve.js . 8765 &
 *   node tools/a11ycheck/verify.js
 *
 * Use tools/serve.js, not `python3 -m http.server`: the basemap is a PMTiles
 * archive read with HTTP Range requests, and http.server ignores Range and
 * returns the whole 14 MB file, so the map silently fails to draw.
 *
 * Exits non-zero on the first failed expectation. Counts are pinned to this
 * archive's contents (55 geolocated items, 145 Person records, ...), so a
 * failure here means either a regression or a content change that needs the
 * expectation updated.
 */
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://localhost:8765';
let fails = 0;

function check(name, ok, detail) {
  console.log(`${ok ? '  ok  ' : 'FAIL  '}${name}${detail ? '  — ' + detail : ''}`);
  if (!ok) fails++;
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const requests = [];
  ctx.on('request', (r) => requests.push(r.url()));
  // Media lives in a bucket this preview does not have; Matomo is a live beacon.
  await ctx.route('**://20.rrchnm.org/**', (r) => r.abort());
  await ctx.route('**://stats.rrchnm.org/**', (r) => r.abort());

  // ---- 1. Browse map -----------------------------------------------------
  let p = await ctx.newPage();
  await p.goto(`${BASE}/items/map.html`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2500);
  const markers = await p.locator('#map_browse .leaflet-marker-icon').count();
  check('map: 55 markers rendered', markers === 55, `${markers} markers`);
  // The basemap is self-hosted Protomaps vector tiles rendered to <canvas>,
  // not raster <img> tiles. Count distinct pixel values rather than elements:
  // a canvas that loaded but painted nothing is exactly the failure mode of
  // omitting the `flavor` option, and it is otherwise silent.
  const painted = await p.evaluate(() => {
    let best = 0;
    for (const cv of document.querySelectorAll('#map_browse canvas')) {
      const d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height).data;
      const seen = new Set();
      for (let i = 0; i < d.length; i += 400) {
        seen.add(`${d[i]},${d[i + 1]},${d[i + 2]},${d[i + 3]}`);
      }
      best = Math.max(best, seen.size);
    }
    return best;
  });
  check('map: basemap painted (self-hosted vector tiles)', painted > 3,
        `${painted} distinct colours`);
  const links = await p.locator('#map-links a').count();
  check('map: "Find An Item" list populated', links >= 55, `${links} links`);
  // Markers overlap at zoom 4, so a real pointer click can be intercepted by
  // a neighbour; dispatch straight at the element instead.
  await p.locator('#map_browse .leaflet-marker-icon').first().dispatchEvent('click');
  await p.waitForTimeout(700);
  const popupHref = await p.locator('.leaflet-popup a.view-item').first()
    .getAttribute('href').catch(() => null);
  check('map: popup links at an .html item page',
        !!popupHref && /\/items\/show\/\d+\.html$/.test(popupHref), popupHref);
  const noPagination = await p.locator('.pagination-nav').count();
  check('map: pagination removed', noPagination === 0);
  await p.close();

  // ---- 2. Per-item map ---------------------------------------------------
  p = await ctx.newPage();
  await p.goto(`${BASE}/items/show/62.html`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2000);
  check('item map: marker rendered',
        (await p.locator('.geolocation-map .leaflet-marker-icon').count()) === 1);
  await p.close();

  // ---- 3. Site-wide search ----------------------------------------------
  p = await ctx.newPage();
  await p.goto(`${BASE}/search.html?query=Dan+Cohen`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2500);
  const n = await p.locator('#search .pagefind-ui__result').count();
  check('search: results for "Dan Cohen"', n > 0, `${n} results`);
  const titles = await p.locator('#search .pagefind-ui__result-title').allInnerTexts();
  check('search: per-page titles, not a repeated chrome h1',
        new Set(titles).size === titles.length && !titles.some((t) => /^RRCHNM20$/.test(t)),
        titles.slice(0, 2).join(' | '));
  check('search: header box is the only visible search field',
        await p.locator('#search .pagefind-ui__search-input')
          .evaluate((e) => e.getAttribute('aria-hidden') === 'true' &&
                           e.getAttribute('tabindex') === '-1'));
  await p.close();

  // ---- 4. Faceted item search -------------------------------------------
  p = await ctx.newPage();
  await p.goto(`${BASE}/items/search.html`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2500);
  const groups = await p.locator('.facet-group legend').allInnerTexts();
  check('facets: rendered before any query typed',
        groups.length === 2 && groups.includes('Item Type') && groups.includes('Collection'),
        groups.join(', '));
  const facetText = await p.locator('#facet-groups').innerText();
  check('facets: Person count is 145', /Person \(145\)/.test(facetText));
  check('facets: Collection counts 66/63',
        /Digital Projects \(66\)/.test(facetText) &&
        /20th Anniversary Contributions \(63\)/.test(facetText));
  // union, not intersection
  await p.locator('label:has-text("Person (145)") input').check();
  await p.waitForTimeout(600);
  await p.locator('label:has-text("Project (66)") input').check();
  await p.waitForTimeout(900);
  const status = await p.locator('#results-status').innerText();
  check('facets: two values in one group are OR-ed, not AND-ed',
        /^211 items$/.test(status), status);
  await p.close();

  // ---- 5. The People nav link -------------------------------------------
  p = await ctx.newPage();
  await p.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  const people = await p.locator('#primary-nav a', { hasText: 'People' }).first()
    .getAttribute('href');
  check('nav: People link repointed', people === '/items/search.html?filter=Item+Type:Person',
        people);
  await p.goto(`${BASE}${people}`, { waitUntil: 'networkidle' });
  await p.waitForTimeout(2500);
  const st = await p.locator('#results-status').innerText();
  check('nav: People link lands pre-filtered on 145 items', /^145 items$/.test(st), st);
  await p.close();

  // ---- 6. Keyboard: the two 2.1.1 failures -------------------------------
  p = await ctx.newPage();
  await p.setViewportSize({ width: 375, height: 800 });
  await p.goto(`${BASE}/items/browse.html`, { waitUntil: 'networkidle' });
  const opener = p.locator('#mobile-nav > button.menu');
  check('mobile nav: opener is a real <button>', await opener.count() === 1);
  await opener.focus();
  check('mobile nav: opener is focusable',
        await p.evaluate(() => document.activeElement.tagName) === 'BUTTON');
  check('mobile nav: starts collapsed',
        await opener.getAttribute('aria-expanded') === 'false');
  await p.keyboard.press('Enter');
  await p.waitForTimeout(600);
  check('mobile nav: Enter opens it',
        await opener.getAttribute('aria-expanded') === 'true' &&
        await p.locator('#mobile-nav-list').isVisible());
  await p.setViewportSize({ width: 1280, height: 900 });

  await p.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  await p.locator('#primary-nav a', { hasText: 'About' }).first().focus();
  await p.keyboard.press('Tab');
  const focused = await p.evaluate(() => document.activeElement.textContent.trim());
  const subVisible = await p.locator('#primary-nav li ul a', { hasText: 'Brief History' })
    .first().isVisible();
  check('desktop nav: submenu reachable by keyboard (:focus-within)',
        subVisible, `focus on "${focused}"`);
  await p.close();

  // ---- 7. Advanced-search disclosure ------------------------------------
  p = await ctx.newPage();
  await p.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  const adv = p.locator('#advanced-search');
  check('disclosure: is a <button> with aria-expanded',
        (await adv.evaluate((e) => e.tagName)) === 'BUTTON' &&
        (await adv.getAttribute('aria-expanded')) === 'false');
  await adv.click();
  await p.waitForTimeout(600);
  check('disclosure: opens', await adv.getAttribute('aria-expanded') === 'true');
  await p.keyboard.press('Escape');
  await p.waitForTimeout(600);
  check('disclosure: Escape closes it',
        await adv.getAttribute('aria-expanded') === 'false');
  await p.close();

  // ---- 8. Pagination "Go" actually paginates -----------------------------
  p = await ctx.newPage();
  await p.goto(`${BASE}/items/browse.html`, { waitUntil: 'networkidle' });
  await p.locator('input[name="page"]').first().fill('5');
  await p.locator('button.pagination-go').first().click();
  await p.waitForLoadState('networkidle');
  check('pagination: "Go" lands on page 5, not page 1',
        p.url().includes('page=5'), p.url().replace(BASE, ''));
  await p.close();

  // ---- 9. Reflow at 320px -----------------------------------------------
  p = await ctx.newPage();
  await p.setViewportSize({ width: 320, height: 640 });
  for (const u of ['/index.html', '/items/browse.html', '/items/show/341.html',
                   '/exhibits/show/history-matters.html', '/items/search.html']) {
    await p.goto(BASE + u, { waitUntil: 'networkidle' });
    const w = await p.evaluate(() => document.documentElement.scrollWidth);
    check(`reflow: no horizontal scroll at 320px  ${u}`, w <= 320, `${w}px`);
  }
  await p.close();

  // ---- 10. Network hygiene ----------------------------------------------
  requests.length = 0;
  p = await ctx.newPage();
  for (const u of ['/index.html', '/items/show/341.html',
                   '/exhibits/show/history-matters.html']) {
    await p.goto(BASE + u, { waitUntil: 'networkidle' });
  }
  const external = requests.filter((u) => !u.startsWith(BASE));
  const banned = external.filter((u) => /googleapis|google-analytics|googletagmanager|knightlab|simile-widgets|drive\.google|cartocdn/.test(u));
  check('network: no CDN/analytics/dead-embed requests', banned.length === 0,
        banned.slice(0, 3).join(' '));
  const matomo = requests.filter((u) => /stats\.rrchnm\.org/.test(u));
  check('network: Matomo present on all three pages', matomo.length >= 3,
        `${matomo.length} beacons`);
  await p.close();

  await browser.close();
  console.log(`\n${fails === 0 ? 'ALL CHECKS PASSED' : fails + ' CHECK(S) FAILED'}`);
  process.exit(fails ? 1 : 0);
})();
