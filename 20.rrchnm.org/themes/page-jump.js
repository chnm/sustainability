/* Make the browse pages' "Page [ N ] of M" box actually paginate.
 *
 * Omeka emitted `<form action="browse.html" method="get">` with a `page` input,
 * which on the live site produced /items/browse?page=5. In the archive the
 * pages are files whose names have the query string baked in --
 * `browse%3Fpage=5.html`, `items%3Fpage=5.html`,
 * `browse%3Fcollection=1&page=5.html` -- and a static server ignores a query
 * string, so submitting the form silently reloaded page 1. A control that
 * looks like it works and does not is worse than one that is obviously broken.
 *
 * Rather than hard-code the filename patterns, derive the template from a link
 * the page already carries: the prev/next anchors point at exactly the right
 * filenames, so swapping their page number for the requested one gives the
 * correct target for every variant (plain, collection-filtered, by-type).
 *
 * Progressive enhancement -- with JS off the form behaves exactly as it did.
 */
(function () {
    'use strict';

    function template(scope) {
        // Any prev/next link in the same pagination block is a worked example.
        var link = scope.querySelector('a[rel="next"], a[rel="prev"]') ||
                   document.querySelector('.pagination a[rel="next"], .pagination a[rel="prev"]');
        if (!link) {
            return null;
        }
        var href = link.getAttribute('href');
        // ...page=<digits>.html  ->  ...page={n}.html
        return /page=\d+\.html$/.test(href)
            ? href.replace(/page=\d+\.html$/, 'page={n}.html')
            : null;
    }

    function wire(form) {
        var input = form.querySelector('input[name="page"]');
        if (!input) {
            return;
        }
        form.addEventListener('submit', function (event) {
            var n = parseInt(input.value, 10);
            if (!n || n < 1) {
                return;               // let the browser do its usual thing
            }
            var tpl = template(form.parentNode || document);
            if (!tpl) {
                return;
            }
            event.preventDefault();
            // Page 1 of the plain listing is the unsuffixed file; every other
            // page, and every filtered listing, uses the templated name.
            window.location.href = tpl.replace('{n}', String(n));
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var forms = document.querySelectorAll('form[accept-charset="utf-8"]');
        for (var i = 0; i < forms.length; i++) {
            wire(forms[i]);
        }
    });
})();
