// MiniSearch implementation for History Matters

const miniSearch = new MiniSearch({
  fields: ['title', 'content'],
  storeFields: ['title', 'url', 'section'],
  tokenize: (string) => string.toLowerCase().split(/[\s\-\.,:;()\[\]{}'"]+/),
  searchOptions: {
    boost: { title: 2 },
    fuzzy: 0.2,
    prefix: true
  }
});

async function fetchAndIndexDocuments() {
  try {
    const response = await fetch('/js/search-documents.json');
    if (!response.ok) {
      throw new Error(`Failed to fetch search index: ${response.status}`);
    }
    const documents = await response.json();
    miniSearch.addAll(documents);
    return documents;
  } catch (error) {
    console.error('Error loading search index:', error);
    return [];
  }
}

function performSearch(query) {
  if (!query || query.trim() === '') return [];
  return miniSearch.search(query, {
    boost: { title: 2 },
    fuzzy: 0.2,
    prefix: true
  });
}

function displaySearchResults(results) {
  const container = document.getElementById('search-results');
  if (results.length === 0) {
    container.innerHTML = '<p>No results found.</p>';
    return;
  }

  container.innerHTML = `
    <h2>Results (${results.length})</h2>
    <ul class="results-list">
      ${results.map(result => `
        <li class="result-item">
          <a href="/${result.url}" class="result-title">${result.title}</a>
          ${result.section ? `<span class="result-section">${result.section}</span>` : ''}
        </li>
      `).join('')}
    </ul>
  `;
}

function getQueryParam(param) {
  return new URLSearchParams(window.location.search).get(param);
}

document.addEventListener('DOMContentLoaded', function() {
  fetchAndIndexDocuments().then(function() {
    const searchResults = document.getElementById('search-results');
    const searchInput = document.getElementById('search-input');
    const searchForm = document.getElementById('search-form');

    if (!searchForm) return;

    // Clear loading message
    searchResults.innerHTML = '';

    // Check for query parameter
    const queryParam = getQueryParam('q');
    if (queryParam) {
      searchInput.value = queryParam;
      const results = performSearch(queryParam);
      displaySearchResults(results);
    }

    searchForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const query = searchInput.value;
      const url = new URL(window.location);
      url.searchParams.set('q', query);
      window.history.pushState({}, '', url);
      const results = performSearch(query);
      displaySearchResults(results);
    });
  });
});
