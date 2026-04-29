# Adding Pagination to Static Search Results
This guide will detail the changes made to a static site search to allow for results to be paginated. Not all websites will need this, but pagination is recommended for larger websites with the potential for hundreds of results. All of this will be done in the `search/index.html` file. 

## HTML
Add `<div id="pagination"></div>` to the `<div class=entry-content>`. Place it below the `<div class=loading-text>`, or wherever works best for your webpage. 

## CSS
Most former CMS will have styling for buttons within their stylesheets. If not, add this to `<style>` within the site header and customize for your site:
``` css
#pagination {
}
```

## JavaScript

### Global Variables
We need to add a few global variables for our pagination. These will be in the `document.addEventListener('DOMContentLoaded', function () {})` but before the `fetch` function. Because MiniSearch returns the search results in an array, the basis of our pagination will be subdividing this array. To do this, it needs to be stored as a global variable so all functions can access it. 
``` js
//pagination 
let allResults = []; // store all search results here
let currentPage = 1;
const resultsPerPage = 25; // adjust for your needs
const paginationContainer = document.getElementById('pagination')
```

### Storing Search Results
A small change needs to be made in the `performSearch` function. 
```js
// Function to perform the search
function performSearch(query) {
    loadingText.style.display = 'block';

    // Search after a short delay
    setTimeout(() => {
        const results = miniSearch.search(query);
        allResults = results
        //displayResults(results, query);
        if (results.length === 0) {
            noResults(query)
        }
        renderPage(1)
        loadingText.style.display = 'none';

        // Only focus on results when explicitly requested (Enter key pressed)
        if (focusOnResults && results.length > 0) {
            searchResults.tabIndex = -1;
            searchResults.focus();
            searchResults.scrollIntoView({ behavior: 'smooth' });
                focusOnResults = false; // Reset the flag
        }
    }, 300);
}
```
### Remove DisplayResults
We will not need the `displayResults` function because we will not be displayed all the results at once. Instead, we will adapt it to suit out pagination needs. For now, comment out or delete the function.

### New Functions
These functions can be placed after the fetch function. 
#### noResults()
This function handles when a query does not yield any search results. It is called in the above performSearch function if the results list's length is equal to 0. 
```js
function noResults(query) {
    if (allResults.length === 0) {
        searchResults.innerHTML = '<p>No results found for "' + query + '"</p>';
        searchAnnouncement.textContent = 'No results found for "' + query + '"';
        return;
    }
};
```

#### renderPage()
This function renders the search results and pagination on the webpage.
```js
function renderPage(page) {
    const searchResults = document.getElementById('search-results');

    // Create a map to deduplicate results by URL
    const uniqueResults = new Map();

    // Keep only the first occurrence of each URL, normalizing URLs to handle both with and without index.html
    allResults.forEach(result => {
        // Normalize the URL by removing index.html from the end
        const normalizedUrl = result.url.replace(/\/index\.html$/, '/');
        if (!uniqueResults.has(normalizedUrl)) {
            uniqueResults.set(normalizedUrl, result);
        }
    });

    let html = '';

    // Calculate slice indexes
    const startIndex = (page - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;

    const pageResults = allResults.slice(startIndex, endIndex);

    pageResults.forEach(result => {
        let tagsHtml = '';
        if (result.tags && result.tags.length > 0) {
            tagsHtml = `<div class="result-tags">Tags: ${result.tags.join(', ')}</div>`;
        }

        html += `
            <div class="result-item">
                <div class="result-title"><a href="${result.url}">${result.title}</a></div>
                <div class="result-url">${result.url}</div>
                ${tagsHtml}
            </div>
        `;
    });

    searchResults.innerHTML = html;
    renderPagination();
};
```

#### changePage() function
This function re-renders the page when a pagination button is clicked by the user.
```js
function changePage(page) {
    const totalPages = Math.ceil(allResults.length / resultsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderPage(currentPage);
    }
};
```

#### renderPagination()
This function creates the pagination buttons, and updates them as users move through the results. The buttons are highly customizable. For example, "first" and "last" buttons may be a usefull addition, or changing the button range.  
```js
function renderPagination() {
    const totalPages = Math.max(1, Math.ceil(allResults.length / resultsPerPage));
    // limit visible page buttons for long lists
    const range = 3;
    const start = Math.max(1, currentPage - range);
    const end = Math.min(totalPages, currentPage + range);

    let html = `<button class="page-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? 'style="display: none;"' : ''}>Prev</button>`;
    for (let i = start; i <= end; i++) {
        html += `<button class="page-btn ${i === currentPage ? 'active ' : ''}" data-page="${i}" ${i === currentPage ? 'aria-current="page" disabled ' : ''}>${i}</button>`;
    }
    html += `<button class="page-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'style="display: none;"' : ''}>Next</button>`;

    paginationContainer.innerHTML = html;
};
```

#### Event Listener
This will recognize when a user clicks a button, and susequently change the page and re-render results. 
```js
paginationContainer.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-page]');
    if (!btn || btn.disabled) return;
        const page = Number(btn.dataset.page);
        changePage(page);
});
```

## Troubleshooting
Common issues:
- `<button>` and `<div>` id and class misspellings
- using the original results and not allResults