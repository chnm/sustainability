// Static keyword search over the pagefind index (/pagefind/pagefind.js),
// built from the item pages in the Docker image. Renders results as the same
// thumbnail+title cards the browse pages use, paged with a "show more" button
// to keep large result sets cheap to render — mirroring the legacy Omeka
// /items/browse?search= behaviour. An item-type facet bar narrows results by
// the pagefind "type" filter, matching the browse tabs.

const PAGE_SIZE = 50;

// URL ?type= slug <-> Omeka item_type stored in the pagefind "type" filter.
const SLUG_TO_TYPE = {
  image: 'Still Image',
  story: 'Document',
  'oral-history': 'Oral History',
  video: 'Moving Image',
};
const TYPE_TO_SLUG = Object.fromEntries(
  Object.entries(SLUG_TO_TYPE).map(([slug, type]) => [type, slug])
);

const input = document.getElementById('search-q');
const statusEl = document.getElementById('search-status');
const resultsEl = document.getElementById('items-primary');
const moreEl = document.getElementById('search-more');
const filtersEl = document.getElementById('search-filters');

let pagefind = null;
let results = [];
let shown = 0;
let curQuery = '';
let curType = ''; // '' = all types, else an item_type value

async function ensurePagefind() {
  if (!pagefind) {
    // Absolute path: the site is served from the domain root.
    pagefind = await import('/pagefind/pagefind.js');
    await pagefind.options({ excerptLength: 25 });
    // Preload the filter index so per-type counts are populated on the very
    // first (unfiltered) search rather than only after a facet is clicked.
    await pagefind.filters();
  }
  return pagefind;
}

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function truncate(s, n) {
  s = String(s == null ? '' : s);
  return s.length > n ? s.slice(0, n) + '…' : s;
}

function cardHTML(d) {
  const url = d.url || '#';
  const title = (d.meta && d.meta.title) || d.url || 'Untitled';
  const img = d.meta && d.meta.image;
  if (img) {
    return (
      '<div class="item hentry"><div class="item-meta"><div class="item-img">' +
      '<a href="' + escapeHtml(url) + '"><img src="' + escapeHtml(img) + '" alt="" loading="lazy"></a>' +
      '<p><a href="' + escapeHtml(url) + '">' + escapeHtml(truncate(title, 20)) + '</a></p>' +
      '</div></div></div>'
    );
  }
  return (
    '<div class="item hentry"><div class="item-meta"><div class="browse-item-description">' +
    '<h5><a href="' + escapeHtml(url) + '">' + escapeHtml(title) + '</a></h5></div>' +
    '<p><a href="' + escapeHtml(url) + '">' + escapeHtml(truncate(title, 20)) + '</a></p>' +
    '</div></div>'
  );
}

function updateMore() {
  moreEl.innerHTML = '';
  const remaining = results.length - shown;
  if (remaining > 0) {
    const b = document.createElement('button');
    b.type = 'button';
    b.id = 'show-more';
    b.textContent = 'Show more (' + remaining + ' remaining)';
    b.addEventListener('click', renderMore);
    moreEl.appendChild(b);
  }
}

async function renderMore() {
  const slice = results.slice(shown, shown + PAGE_SIZE);
  const datas = await Promise.all(slice.map((r) => r.data()));
  resultsEl.insertAdjacentHTML('beforeend', datas.map(cardHTML).join(''));
  shown += slice.length;
  updateMore();
}

// Counts are stable per query regardless of the active type filter:
// pagefind exposes them as totalFilters (when a filter is applied) or
// filters (when none is). "All Items" uses the query's unfiltered total.
function updateFilters(counts, total) {
  filtersEl.hidden = false;
  filtersEl.querySelectorAll('li').forEach((li) => {
    const t = li.getAttribute('data-type');
    const n = t === '' ? total : (counts[t] || 0);
    const cnt = li.querySelector('.cnt');
    if (cnt) cnt.textContent = '(' + n + ')';
    li.classList.toggle('current', t === curType);
  });
}

function syncURL() {
  const url = new URL(window.location);
  url.searchParams.set('q', curQuery.trim());
  const slug = TYPE_TO_SLUG[curType];
  if (slug) url.searchParams.set('type', slug);
  else url.searchParams.delete('type');
  window.history.replaceState(null, '', url);
}

async function doSearch() {
  resultsEl.innerHTML = '';
  moreEl.innerHTML = '';
  results = [];
  shown = 0;
  const q = curQuery.trim();
  if (!q) { statusEl.textContent = ''; filtersEl.hidden = true; return; }

  statusEl.textContent = 'Searching…';
  let pf;
  try {
    pf = await ensurePagefind();
  } catch (e) {
    statusEl.textContent = 'Search is unavailable on this build.';
    return;
  }
  const search = await pf.search(q, curType ? { filters: { type: curType } } : {});
  results = search.results;
  const counts =
    (search.totalFilters && search.totalFilters.type) ||
    (search.filters && search.filters.type) || {};
  updateFilters(counts, search.unfilteredResultCount);

  const n = results.length;
  statusEl.textContent = n + ' result' + (n === 1 ? '' : 's') + ' for “' + q + '”';
  await renderMore();
}

filtersEl.addEventListener('click', (e) => {
  const a = e.target.closest('a');
  if (!a) return;
  e.preventDefault();
  const t = a.closest('li').getAttribute('data-type');
  if (t === curType) return;
  curType = t;
  syncURL();
  doSearch();
});

document.getElementById('page-search-form').addEventListener('submit', (e) => {
  e.preventDefault();
  curQuery = input.value;
  syncURL();
  doSearch();
});

const params = new URLSearchParams(window.location.search);
curQuery = params.get('q') || '';
curType = SLUG_TO_TYPE[params.get('type')] || '';
input.value = curQuery;
if (curQuery) doSearch();
