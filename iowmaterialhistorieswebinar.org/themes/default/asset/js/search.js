/* Client-side search for the iowmaterialhistorieswebinar.org archive.
 *
 * Omeka S served search from /s/Material-Histories/index/search, a database
 * query. A static archive has no database, so the header form on all 72 pages
 * pointed at an endpoint that no longer exists. This drives Pagefind's
 * prebuilt index instead, from /pagefind/, which is committed to the
 * repository so the deploy stays a plain file copy.
 *
 * Pagefind's Default UI is not used: it renders its own search box, which
 * would be a second one on a page whose header already has the site-wide form.
 * The core API takes the query straight from the URL.
 *
 * The query parameter is `fulltext_search` -- the name Omeka S itself used --
 * so links of that shape, including anything already indexed or bookmarked,
 * still land on a real result set. `q` and `query` are accepted too.
 */

const form = document.getElementById("pagefind-form");
const input = document.getElementById("pagefind-input");
const status = document.getElementById("search-status");
const results = document.getElementById("search-results");

const MAX = 50;

let pagefind = null;

async function library() {
  if (!pagefind) {
    pagefind = await import("/pagefind/pagefind.js");
    await pagefind.init();
  }
  return pagefind;
}

function queryFromUrl() {
  const p = new URLSearchParams(window.location.search);
  return (p.get("fulltext_search") || p.get("q") || p.get("query") || "").trim();
}

function titleOf(data) {
  const t = (data.meta && data.meta.title) || data.url;
  // Every page's <title> ends in the site and seminar names; in a list of
  // results from one archive that is noise on every row.
  return t.split(" · ")[0];
}

function render(query, hits) {
  results.replaceChildren();
  if (!hits.length) {
    status.textContent = `No results for “${query}”.`;
    return;
  }
  status.textContent =
    hits.length === 1 ? `1 result for “${query}”.`
                      : `${hits.length} results for “${query}”.`;
  const ol = document.createElement("ol");
  for (const hit of hits) {
    const li = document.createElement("li");
    const h2 = document.createElement("h2");
    h2.className = "search-result-title";
    const a = document.createElement("a");
    a.href = hit.url;
    a.textContent = titleOf(hit);
    h2.append(a);
    const p = document.createElement("p");
    p.className = "search-result-excerpt";
    p.innerHTML = hit.excerpt;   // Pagefind's own <mark>-wrapped, escaped text
    li.append(h2, p);
    ol.append(li);
  }
  results.append(ol);
}

async function run(query) {
  if (!query) {
    results.replaceChildren();
    status.textContent = "Enter a word or phrase to search the archive.";
    return;
  }
  status.textContent = `Searching for “${query}”…`;
  try {
    const pf = await library();
    const search = await pf.search(query);
    const hits = await Promise.all(search.results.slice(0, MAX).map((r) => r.data()));
    render(query, hits);
  } catch (e) {
    status.textContent = "The search index could not be loaded.";
    console.error(e);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = input.value.trim();
  const url = new URL(window.location.href);
  url.search = query ? `?fulltext_search=${encodeURIComponent(query)}` : "";
  history.replaceState(null, "", url);
  run(query);
});

const initial = queryFromUrl();
input.value = initial;
run(initial);
