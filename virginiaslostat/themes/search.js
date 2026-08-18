/* Client-side search for the virginiaslostat.org archive.
 *
 * Replaces two dead Omeka endpoints:
 *
 *   - https://virginiaslostat.org/search, which the theme never linked from
 *     anywhere (Omeka rendered nothing into .top-bar-right's two empty <li>, so
 *     the site shipped with no search box at all);
 *   - items/search.html, the advanced item search, whose form was worse than
 *     dead: `wget --convert-links` rewrote its action to `browse.html`, so
 *     submitting it silently reloaded an unfiltered browse listing. Every field
 *     the visitor filled in was discarded without a word.
 *
 * Built on Pagefind's CORE API rather than its Default UI, for two reasons. The
 * Default UI renders its own search input, which would be a second box on a
 * page whose header already has one -- the sibling archives work around that by
 * hiding Pagefind's input and driving it from the header, leaving an invisible
 * control in the DOM. And the Default UI only draws its filter panel once a
 * keyword has been typed, which would leave an advanced-search page blank on
 * arrival; the core API takes search(null, {filters}), so filters alone are a
 * valid query.
 *
 * Two modes, set by data-search-mode on #search-app:
 *   "site"   search.html        -- everything, no facets
 *   "items"  items/search.html  -- Record=Item, with Format/Creator/Tag facets
 */
(function () {
  'use strict';

  var app = document.getElementById('search-app');
  if (!app) { return; }

  var MODE = app.getAttribute('data-search-mode') || 'site';
  var BASE = app.getAttribute('data-pagefind-base') || '/pagefind/';
  var PAGE_SIZE = 20;

  var form = document.getElementById('search-form');
  var input = document.getElementById('search-query');
  var statusEl = document.getElementById('search-status');
  var resultsEl = document.getElementById('search-results');
  var facetsEl = document.getElementById('search-facets');
  var moreWrap = document.getElementById('search-more');

  /* Facet name -> query-string key. `tag` also answers to `tags`, the field
     name the Omeka advanced form used, so an old link still filters. */
  var FACETS = [
    { name: 'Format', param: 'format', phrase: 'in format' },
    { name: 'Creator', param: 'creator', phrase: 'created by' },
    { name: 'Tag', param: 'tag', alias: 'tags', phrase: 'tagged' }
  ];

  var pagefind = null;
  var allResults = [];
  var shown = 0;
  var seq = 0;

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function selectedFor(param, alias) {
    var p = params();
    var out = p.getAll(param);
    if (!out.length && alias) { out = p.getAll(alias); }
    return out;
  }

  function checkedValues(name) {
    var boxes = facetsEl
      ? facetsEl.querySelectorAll('input[data-facet="' + name + '"]:checked')
      : [];
    return Array.prototype.map.call(boxes, function (b) { return b.value; });
  }

  function activeFilters() {
    var filters = {};
    if (MODE === 'items') { filters.Record = ['Item']; }
    FACETS.forEach(function (f) {
      var vals = facetsEl ? checkedValues(f.name) : [];
      if (vals.length) {
        // A bare array means AND in Pagefind; these are alternatives.
        filters[f.name] = { any: vals };
      }
    });
    return filters;
  }

  function syncUrl(query) {
    var url = new URL(window.location);
    var p = url.searchParams;
    ['query', 'q'].forEach(function (k) { p.delete(k); });
    FACETS.forEach(function (f) {
      p.delete(f.param);
      if (f.alias) { p.delete(f.alias); }
    });
    if (query) { p.set('query', query); }
    FACETS.forEach(function (f) {
      checkedValues(f.name).forEach(function (v) { p.append(f.param, v); });
    });
    window.history.replaceState(null, '', url);
  }

  function text(el, value) { el.textContent = value; }

  function describe(count, query, filters) {
    var bits = [];
    if (query) { bits.push('matching “' + query + '”'); }
    FACETS.forEach(function (f) {
      var vals = filters[f.name] && filters[f.name].any;
      if (vals && vals.length) {
        bits.push(f.phrase + ' ' +
          vals.map(function (v) { return '“' + v + '”'; }).join(' or '));
      }
    });
    var noun = MODE === 'items' ? 'item' : 'page';
    var head = count + ' ' + noun + (count === 1 ? '' : 's');
    if (!bits.length) {
      return MODE === 'items'
        ? head + ' in the archive'
        : 'Type in the box above to search this archive.';
    }
    return head + ' ' + bits.join(', ');
  }

  function render(reset) {
    if (reset) {
      resultsEl.innerHTML = '';
      shown = 0;
    }
    var list = resultsEl.querySelector('ol');
    if (!list) {
      list = document.createElement('ol');
      list.className = 'search-result-list';
      resultsEl.appendChild(list);
    }
    var slice = allResults.slice(shown, shown + PAGE_SIZE);
    slice.forEach(function (r) {
      var li = document.createElement('li');
      li.className = 'search-result';

      var h = document.createElement('h2');
      var a = document.createElement('a');
      a.href = r.url;
      a.textContent = (r.meta && r.meta.title) || r.url;
      h.appendChild(a);
      li.appendChild(h);

      if (r.excerpt) {
        var p = document.createElement('p');
        p.className = 'search-excerpt';
        // Pagefind's excerpt contains only <mark> around the matched terms.
        p.innerHTML = r.excerpt;
        li.appendChild(p);
      }

      var meta = [];
      ['Record', 'Format', 'Creator'].forEach(function (k) {
        if (r.filters && r.filters[k] && r.filters[k].length) {
          meta.push(r.filters[k].join(', '));
        }
      });
      if (meta.length) {
        var m = document.createElement('p');
        m.className = 'search-meta';
        m.textContent = meta.join(' · ');
        li.appendChild(m);
      }
      list.appendChild(li);
    });
    shown += slice.length;

    moreWrap.innerHTML = '';
    if (shown < allResults.length) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'search-more-button';
      btn.textContent = 'Show ' +
        Math.min(PAGE_SIZE, allResults.length - shown) + ' more (' +
        (allResults.length - shown) + ' remaining)';
      btn.addEventListener('click', function () {
        var first = shown;
        render(false);
        // Move focus to the first newly added heading, so a keyboard user is
        // not dropped back at the top of a list that just grew.
        var headings = resultsEl.querySelectorAll('.search-result h2 a');
        if (headings[first]) {
          headings[first].setAttribute('tabindex', '-1');
          headings[first].focus();
        }
      });
      moreWrap.appendChild(btn);
    }
  }

  function run(query, opts) {
    opts = opts || {};
    var filters = activeFilters();
    var mine = ++seq;
    var hasFilters = Object.keys(filters).some(function (k) {
      return k !== 'Record';
    });
    // Nothing asked for on the site-wide page: show the prompt, not everything.
    if (MODE === 'site' && !query && !hasFilters) {
      allResults = [];
      resultsEl.innerHTML = '';
      moreWrap.innerHTML = '';
      text(statusEl, describe(0, '', filters));
      if (opts.pushUrl !== false) { syncUrl(query); }
      return Promise.resolve();
    }
    text(statusEl, 'Searching…');
    return pagefind.search(query || null, { filters: filters })
      .then(function (search) {
        if (mine !== seq) { return; }   // a later keystroke already won
        return Promise.all(search.results.map(function (r) { return r.data(); }))
          .then(function (data) {
            if (mine !== seq) { return; }
            allResults = data;
            text(statusEl, describe(data.length, query, filters));
            render(true);
            updateFacetCounts(search.filters);
            if (opts.pushUrl !== false) { syncUrl(query); }
          });
      });
  }

  /* value -> the <span> holding its live result count, so the counts can be
     refreshed after each search without rebuilding the checkboxes (which would
     throw away focus and, on a slow index, the click that caused the search). */
  var countSpans = {};

  function buildFacets(available) {
    if (!facetsEl) { return; }
    facetsEl.innerHTML = '';
    countSpans = {};
    FACETS.forEach(function (f) {
      var values = available[f.name] || {};
      var names = Object.keys(values).filter(function (v) {
        return values[v] > 0;
      }).sort(function (a, b) { return a.localeCompare(b); });
      if (!names.length) { return; }
      var fs = document.createElement('fieldset');
      var lg = document.createElement('legend');
      lg.textContent = f.name;
      fs.appendChild(lg);
      var preselected = selectedFor(f.param, f.alias);
      names.forEach(function (v, i) {
        var id = 'facet-' + f.param + '-' + i;
        var label = document.createElement('label');
        label.htmlFor = id;
        var box = document.createElement('input');
        box.type = 'checkbox';
        box.id = id;
        box.value = v;
        box.setAttribute('data-facet', f.name);
        if (preselected.indexOf(v) !== -1) { box.checked = true; }
        box.addEventListener('change', function () {
          run(input.value.trim());
        });
        var count = document.createElement('span');
        count.className = 'facet-count';
        count.textContent = '(' + values[v] + ')';
        countSpans[f.name + ' ' + v] = count;
        label.appendChild(box);
        label.appendChild(document.createTextNode(' ' + v + ' '));
        label.appendChild(count);
        fs.appendChild(label);
      });
      facetsEl.appendChild(fs);
    });
  }

  function updateFacetCounts(filters) {
    if (!filters) { return; }
    FACETS.forEach(function (f) {
      var values = filters[f.name] || {};
      Object.keys(countSpans).forEach(function (key) {
        if (key.indexOf(f.name + ' ') !== 0) { return; }
        var value = key.slice(f.name.length + 1);
        var span = countSpans[key];
        var n = values[value] || 0;
        span.textContent = '(' + n + ')';
        // A value that would return nothing is dimmed, not removed: removing it
        // would move every checkbox under the pointer mid-click.
        span.parentNode.classList.toggle(
          'facet-empty',
          n === 0 && !span.parentNode.querySelector('input').checked);
      });
    });
  }

  function start() {
    var initial = params().get('query') || params().get('q') || '';
    if (input) { input.value = initial; }

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        run(input.value.trim());
      });
    }
    if (input) {
      var timer;
      input.addEventListener('input', function () {
        clearTimeout(timer);
        var v = input.value.trim();
        timer = setTimeout(function () { run(v); }, 200);
      });
    }

    // Pagefind ships as an ES module; the dynamic import keeps this file a
    // plain script that older parsers can still read past.
    import(BASE + 'pagefind.js').then(function (pf) {
      pagefind = pf;
      return pf.options({ basePath: BASE }).then(function () {
        return pf.init();
      });
    }).then(function () {
      if (MODE !== 'items') { return null; }
      /* filters() first, and not only for its return value: Pagefind loads its
         filter index in chunks on demand, and a scoped search asked before
         anything has primed it comes back knowing only the filter it was given
         -- search(null, {filters:{Record:['Item']}}) returns counts for Record
         and nothing else. With the chunks loaded, the same call reports all
         four groups, scoped to the 76 item pages, which is what the facet
         counts should show. */
      return pagefind.filters().then(function (all) {
        return pagefind.search(null, { filters: { Record: ['Item'] } })
          .then(function (search) {
            buildFacets(search.filters || all || {});
          });
      });
    }).then(function () {
      return run(initial, { pushUrl: false });
    }).catch(function (err) {
      text(statusEl, 'The search index could not be loaded.');
      if (window.console) { console.error('pagefind:', err); }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
