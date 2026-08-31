// Pagefind-based search for Papers of the War Department.
// Preserves the MiniSearch UI contract: Documents / Guides & News radio,
// ?q= and ?type= URL params, 25-per-page pagination, .search-result-* classes.
// Requires the Pagefind index at /pagefind/ (built post-Hugo: `just build`).
(function () {
    var resultsPerPage = 25;
    var pagefind = null;
    var lastSearch = null; // pagefind search response (results are lazy)
    var currentPage = 1;

    function filtersFor(type) {
        return type === 'documents'
            ? { type: 'Document' }
            : { type: { any: ['Guide', 'News'] } };
    }

    function escapeHtml(s) {
        var div = document.createElement('div');
        div.textContent = s == null ? '' : String(s);
        return div.innerHTML;
    }

    function selectedType() {
        var el = document.querySelector('input[name="search-type"]:checked');
        return el ? el.value : 'documents';
    }

    function setStatus(msg) {
        var el = document.getElementById('search-status');
        if (el) el.textContent = msg || '';
    }

    function renderPage(page) {
        var container = document.getElementById('search-results');
        var results = lastSearch ? lastSearch.results : [];
        if (!results.length) {
            container.innerHTML = '<p class="search-no-results">No results found.</p>';
            return;
        }
        currentPage = page;
        var totalPages = Math.ceil(results.length / resultsPerPage);
        var slice = results.slice((page - 1) * resultsPerPage, page * resultsPerPage);

        // Fetch fragment data only for the visible page (Pagefind loads lazily).
        Promise.all(slice.map(function (r) { return r.data(); })).then(function (docs) {
            var html = '<p class="search-result-count">' + results.length +
                ' result' + (results.length !== 1 ? 's' : '') + '</p>';
            html += '<ul class="search-result-list">';
            docs.forEach(function (d) {
                html += '<li class="search-result-item">';
                html += '<a href="' + d.url + '" class="search-result-title">' +
                    escapeHtml(d.meta && d.meta.title ? d.meta.title : d.url) + '</a>';
                // Pagefind excerpts arrive pre-highlighted with <mark>.
                html += '<p class="search-result-desc">' + d.excerpt + '</p>';
                html += '</li>';
            });
            html += '</ul>';
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
        });
    }

    function runSearch(query) {
        if (!query) {
            document.getElementById('search-results').innerHTML = '';
            setStatus('');
            return;
        }
        setStatus('Searching...');
        loadPagefind().then(function (pf) {
            return pf.search(query, { filters: filtersFor(selectedType()) });
        }).then(function (search) {
            lastSearch = search;
            setStatus('');
            renderPage(1);
        }).catch(function (err) {
            setStatus('Search is unavailable. (Pagefind index missing? Run `just build`.)');
            console.error('Pagefind error:', err);
        });
    }

    function loadPagefind() {
        if (pagefind) return Promise.resolve(pagefind);
        return import('/pagefind/pagefind.js').then(function (mod) {
            pagefind = mod;
            pagefind.init();
            return pagefind;
        });
    }

    function updateUrl(query) {
        var url = new URL(window.location);
        if (query) url.searchParams.set('q', query); else url.searchParams.delete('q');
        url.searchParams.set('type', selectedType());
        window.history.replaceState({}, '', url);
    }

    document.addEventListener('DOMContentLoaded', function () {
        var form = document.getElementById('search-form');
        var input = document.getElementById('search-input');

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            updateUrl(input.value.trim());
            runSearch(input.value.trim());
        });

        document.querySelectorAll('input[name="search-type"]').forEach(function (radio) {
            radio.addEventListener('change', function () {
                updateUrl(input.value.trim());
                runSearch(input.value.trim());
            });
        });

        document.getElementById('search-results').addEventListener('click', function (e) {
            var link = e.target.closest('.search-page-link');
            if (!link) return;
            e.preventDefault();
            renderPage(parseInt(link.dataset.page, 10));
        });

        // Restore state from URL (?q=...&type=...)
        var params = new URLSearchParams(window.location.search);
        var q = params.get('q');
        var type = params.get('type');
        if (type === 'pages') {
            var radio = document.querySelector('input[name="search-type"][value="pages"]');
            if (radio) radio.checked = true;
        }
        if (q) {
            input.value = q;
            runSearch(q);
        }
    });
})();
