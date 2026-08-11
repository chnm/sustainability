/* Randomized "Featured Item" for the homepage.
 *
 * Omeka's default theme called random_featured_items(), so this block showed a
 * different featured item on every request. The wget crawl captured one render
 * and froze it on item 614.
 *
 * The five entries below are the site's real featured set, harvested from
 * https://thanksroy.org/items/browse?featured=1 while the origin was still up
 * and cross-checked against repeated fetches of the live homepage. Regenerate
 * with tools/featured_items.py.
 *
 * Deliberately vanilla JS with no jQuery dependency: jQuery loads from a CDN
 * that is blocked on some networks, and the featured item should not go down
 * with it. The script tag sits directly after #featured-item rather than
 * waiting for DOMContentLoaded, so the swap happens as the element is parsed
 * and there is no visible flash of the frozen item.
 *
 * If scripting is off, the server-rendered item stays exactly as it is -- the
 * block degrades to the behaviour it has today.
 */
(function () {
    'use strict';

    var FEATURED = [
        { id: 606, title: 'fashion sense',                        thumb: 'a1b4f626d9303fac6c065e7ae7f39d29.jpg' },
        { id: 608, title: 'CHNM running group',                   thumb: 'e725892ca13c4e1a3511116ebfd9a170.jpg' },
        { id: 609, title: 'Roy, with Larry and Cornelia Levine',  thumb: '5ddc51a50b2e246ca627cb0fb323258c.jpg' },
        { id: 614, title: 'For Roy – Multitasker Extraordinaire', thumb: 'fb80474be58c87e07a2b3e316f69c1bc.jpg' },
        { id: 626, title: 'Roy in a Who Built America" T-Shirt"', thumb: 'd8b481878d60dfb9fa1d5d99125662d8.jpg' }
    ];

    var FILES_BASE = 'https://thanksroy.org/files/square_thumbnails/';

    var container = document.getElementById('featured-item');
    if (!container) {
        return;
    }

    var record = container.querySelector('.item.record');
    if (!record) {
        return;
    }

    var item = FEATURED[Math.floor(Math.random() * FEATURED.length)];
    var href = 'items/show/' + item.id + '.html';

    // Rebuild the theme's markup shape (.item.record > h3 > a, then a.image >
    // img) so style.css:1271 and the rest of the theme keep applying. Built via
    // the DOM rather than innerHTML so titles carrying quotes -- item 626's
    // does -- cannot break out of an attribute.
    var heading = document.createElement('h3');
    var titleLink = document.createElement('a');
    titleLink.setAttribute('href', href);
    titleLink.appendChild(document.createTextNode(item.title));
    heading.appendChild(titleLink);

    var imageLink = document.createElement('a');
    imageLink.setAttribute('href', href);
    imageLink.className = 'image';

    var img = document.createElement('img');
    img.setAttribute('src', FILES_BASE + item.thumb);
    // The image link points at the same item as the heading link above it, so
    // naming it with the item's title gives two same-purpose links a matching
    // accessible name. alt="" would instead leave a link with no name at all.
    img.setAttribute('alt', item.title);
    imageLink.appendChild(img);

    record.innerHTML = '';
    record.appendChild(heading);
    record.appendChild(imageLink);
})();
