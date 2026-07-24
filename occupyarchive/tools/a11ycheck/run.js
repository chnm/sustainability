const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
const axe = require('axe-core');

const ROOT = path.resolve(__dirname, '..', '..');
const PAGES = [
  'index.html', 'about.html', 'contact.html', 'collections.html',
  'items.html', 'search.html', 'items/browse.html', 'items/show/958.html',
  'items/tags.html', 'items/advanced-search.html', 'items/map.html',
  'collections/show/205.html', 'items/index/page/177.html',
];

// WCAG 2.2 A/AA tags we care about (axe uses wcag2a, wcag2aa, wcag21aa, wcag22aa)
const AA_TAGS = new Set(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']);

async function auditFile(rel) {
  const abs = path.join(ROOT, rel);
  let html = fs.readFileSync(abs, 'utf8');
  // Drop external fonts/scripts/jquery so jsdom doesn't hit the network; keep local CSS.
  html = html
    .replace(/<link[^>]*fonts\.googleapis[^>]*>/gi, '')
    .replace(/<script[^>]*ajax\.googleapis[^>]*>\s*<\/script>/gi, '')
    .replace(/<script[^>]*stats\.rrchnm[^>]*>[\s\S]*?<\/script>/gi, '');
  const dom = new JSDOM(html, {
    url: 'file://' + abs,
    resources: 'usable',
    pretendToBeVisual: true,
    runScripts: 'dangerously',
  });
  const { window } = dom;
  await new Promise((r) => {
    if (window.document.readyState === 'complete') return r();
    window.addEventListener('load', r);
    setTimeout(r, 1500);
  });
  const s = window.document.createElement('script');
  s.textContent = axe.source;
  window.document.head.appendChild(s);
  const results = await window.axe.run(window.document, {
    resultTypes: ['violations', 'incomplete'],
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] },
  });
  dom.window.close();
  return results;
}

(async () => {
  let grandAA = 0;
  const contrastIncomplete = {};
  for (const p of PAGES) {
    let res;
    try { res = await auditFile(p); }
    catch (e) { console.log(`\n### ${p}\n  ERROR: ${e.message}`); continue; }
    const aa = res.violations.filter(v => v.tags.some(t => AA_TAGS.has(t)));
    const bp = res.violations.filter(v => !v.tags.some(t => AA_TAGS.has(t)));
    grandAA += aa.length;
    const ci = res.incomplete.find(i => i.id === 'color-contrast');
    contrastIncomplete[p] = ci ? ci.nodes.length : 0;
    console.log(`\n### ${p}`);
    console.log(`  AA/A violations: ${aa.length} | best-practice: ${bp.length} | contrast-needs-review: ${contrastIncomplete[p]}`);
    for (const v of aa) {
      console.log(`  [AA] ${v.id} (${v.impact}) x${v.nodes.length} — ${v.help}`);
      console.log(`       ${v.nodes[0].target.join(' ')}  ::  ${(v.nodes[0].html||'').slice(0,90)}`);
    }
    for (const v of bp) {
      console.log(`  [bp] ${v.id} x${v.nodes.length} — ${v.help}`);
    }
  }
  console.log(`\n==== TOTAL A/AA violations across ${PAGES.length} pages: ${grandAA} ====`);
})();
