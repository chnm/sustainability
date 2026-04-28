// MiniSearch-based search for Papers of the War Department
(function() {
    var searchIndex = null;
    var allDocs = null;
    var currentType = 'documents'; // 'documents' or 'pages'
    var resultsPerPage = 25;
    var currentPage = 1;
    var lastResults = [];

    // Field mappings for compact JSON keys
    // Documents: id, t=title, u=url, y=year, a=authors, r=recipients, d=doc_type, s=description, c=transcription content
    // Pages: id, t=title, u=url, T=type(P/N), a=author

    function initMiniSearch(type) {
        if (type === 'documents') {
            return new MiniSearch({
                fields: ['t', 'a', 'r', 's', 'c'],
                storeFields: ['t', 'u', 'y', 'a', 'd', 's'],
                searchOptions: {
                    boost: { t: 3, a: 2, c: 1 },
                    fuzzy: 0.2,
                    prefix: true,
                    combineWith: 'AND'
                }
            });
        } else {
            return new MiniSearch({
                fields: ['t', 'a'],
                storeFields: ['t', 'u', 'T', 'a'],
                searchOptions: {
                    boost: { t: 2 },
                    fuzzy: 0.2,
                    prefix: true,
                    combineWith: 'AND'
                }
            });
        }
    }

    function loadIndex(type) {
        var file = type === 'documents' ? 'search-documents.json' : 'search-pages.json';
        var statusEl = document.getElementById('search-status');
        if (statusEl) statusEl.textContent = 'Loading search index...';

        return fetch('/js/' + file)
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                allDocs = data;
                searchIndex = initMiniSearch(type);
                searchIndex.addAll(data);
                if (statusEl) statusEl.textContent = '';
                return data;
            })
            .catch(function(err) {
                if (statusEl) statusEl.textContent = 'Error loading search index.';
                console.error('Search index load error:', err);
            });
    }

    function typeLabel(code) {
        if (code === 'P') return 'Page';
        if (code === 'N') return 'News';
        return '';
    }

    function renderResults(results, page) {
        var container = document.getElementById('search-results');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = '<p class="search-no-results">No results found.</p>';
            return;
        }

        var totalPages = Math.ceil(results.length / resultsPerPage);
        var start = (page - 1) * resultsPerPage;
        var end = Math.min(start + resultsPerPage, results.length);
        var pageResults = results.slice(start, end);

        var html = '<p class="search-result-count">' + results.length + ' result' + (results.length !== 1 ? 's' : '') + '</p>';
        html += '<ul class="search-result-list">';

        for (var i = 0; i < pageResults.length; i++) {
            var r = pageResults[i];
            html += '<li class="search-result-item">';
            html += '<a href="' + r.u + '" class="search-result-title">' + escapeHtml(r.t) + '</a>';

            var meta = [];
            if (r.y) meta.push(r.y);
            if (r.a) meta.push(escapeHtml(r.a));
            if (r.d) meta.push('<em>' + escapeHtml(r.d) + '</em>');
            if (r.T) meta.push(typeLabel(r.T));

            if (meta.length > 0) {
                html += '<div class="search-result-meta">' + meta.join(' &middot; ') + '</div>';
            }
            if (r.s) {
                html += '<p class="search-result-desc">' + escapeHtml(r.s) + '</p>';
            }
            html += '</li>';
        }

        html += '</ul>';

        // Pagination
        if (totalPages > 1) {
            html += '<div class="search-pagination">';
            if (page > 1) {
                html += '<a href="#" class="search-page-link" data-page="' + (page - 1) + '">&laquo; Previous</a> ';
            }
            html += '<span class="search-page-info">Page ' + page + ' of ' + totalPages + '</span>';
            if (page < totalPages) {
                html += ' <a href="#" class="search-page-link" data-page="' + (page + 1) + '">Next &raquo;</a>';
            }
            html += '</div>';
        }

        container.innerHTML = html;

        // Bind pagination clicks
        var pageLinks = container.querySelectorAll('.search-page-link');
        for (var j = 0; j < pageLinks.length; j++) {
            pageLinks[j].addEventListener('click', function(e) {
                e.preventDefault();
                currentPage = parseInt(this.getAttribute('data-page'));
                renderResults(lastResults, currentPage);
                container.scrollIntoView({ behavior: 'smooth' });
            });
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function doSearch() {
        var query = document.getElementById('search-input').value.trim();
        if (!query || !searchIndex) {
            document.getElementById('search-results').innerHTML = '';
            return;
        }

        var results = searchIndex.search(query);
        currentPage = 1;
        lastResults = results;
        renderResults(results, 1);

        // Update URL
        var url = new URL(window.location);
        url.searchParams.set('q', query);
        url.searchParams.set('type', currentType);
        window.history.replaceState({}, '', url);
    }

    document.addEventListener('DOMContentLoaded', function() {
        var form = document.getElementById('search-form');
        var input = document.getElementById('search-input');
        var radios = document.querySelectorAll('input[name="search-type"]');
        if (!form || !input) return;

        // Get params from URL
        var params = new URLSearchParams(window.location.search);
        var initialQuery = params.get('q') || '';
        var initialType = params.get('type') || 'documents';

        input.value = initialQuery;
        currentType = initialType;

        // Set radio button
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].value === initialType) radios[i].checked = true;
        }

        // Load initial index
        loadIndex(currentType).then(function() {
            if (initialQuery) doSearch();
        });

        // Form submit
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            doSearch();
        });

        // Radio button change — reload index
        for (var j = 0; j < radios.length; j++) {
            radios[j].addEventListener('change', function() {
                currentType = this.value;
                document.getElementById('search-results').innerHTML = '';
                var statusEl = document.getElementById('search-status');
                if (statusEl) statusEl.textContent = 'Switching...';
                loadIndex(currentType).then(function() {
                    if (input.value.trim()) doSearch();
                });
            });
        }
    });
})();
