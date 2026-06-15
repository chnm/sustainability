// Static keyword search over the pagefind index (/pagefind/pagefind.js),
// built from the item pages in the Docker image. Renders results as the same
// thumbnail+title cards the browse pages use, paged with a "show more" button
// to keep large result sets cheap to render — mirroring the legacy Omeka
// /items/browse?search= behaviour.

const PAGE_SIZE = 50;

const input = document.getElementById('search-q');
const statusEl = document.getElementById('search-status');
const resultsEl = document.getElementById('items-primary');
const moreEl = document.getElementById('search-more');

let pagefind = null;
let results = [];
let shown = 0;

async function ensurePagefind() {
  if (!pagefind) {
    // Absolute path: the site is served from the domain root.
    pagefind = await import('/pagefind/pagefind.js');
    await pagefind.options({ excerptLength: 25 });
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

async function doSearch(q) {
  resultsEl.innerHTML = '';
  moreEl.innerHTML = '';
  results = [];
  shown = 0;
  q = (q || '').trim();
  if (!q) { statusEl.textContent = ''; return; }

  statusEl.textContent = 'Searching…';
  let pf;
  try {
    pf = await ensurePagefind();
  } catch (e) {
    statusEl.textContent = 'Search is unavailable on this build.';
    return;
  }
  const search = await pf.search(q);
  results = search.results;
  const n = results.length;
  statusEl.textContent = n + ' result' + (n === 1 ? '' : 's') + ' for “' + q + '”';
  await renderMore();
}

function queryFromURL() {
  return new URLSearchParams(window.location.search).get('q') || '';
}

document.getElementById('page-search-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const q = input.value;
  const url = new URL(window.location);
  url.searchParams.set('q', q.trim());
  window.history.replaceState(null, '', url);
  doSearch(q);
});

const initial = queryFromURL();
input.value = initial;
if (initial) doSearch(initial);
