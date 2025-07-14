# Generating Static Search 

This guide documents the process to add a static search function to HTML sites for the sustainability initiative. Let's work from the `digitalcampus` directory since it's the cleanest and simplest version.

## Setup

If you want to work from individual folders, you can use sparse checkout: `git sparse-checkout digitalcampus`

## Dependencies

Before starting, ensure you have:

1. Node.js installed (v12+)
2. [npx](https://docs.npmjs.com/cli/v8/commands/npx)
3. [HTML Tidy](https://www.html-tidy.org/) (optional, for cleaning HTML files)

## Project Structure

Essential files and directories:

- `search/` - Contains the search page template
- `static-search/` - Contains utility files like stopwords and the tidy script
- `update_search.sh` - Bash script to orchestrate the search index generation
- `update_search_index.js` - Node.js script that processes HTML files to create the search index
- `Makefile` - Contains shortcuts for common operations

## Implementation Process

1. Copy over contents of the `search` directory to the root of the project
2. Copy over contents of the `static-search` directory to the root of the project
3. Copy over `update_search.sh`, `update_search_index.js`, and the `Makefile` to the root of the project
4. Open a root `index.html` file, copy all of its content, and paste into the `search/index.html` file we copied over from `digitalcampus`

## Search Page Configuration

There are three key elements needed for the search page:

1. Include the MiniSearch CDN in the `<header>` of the page:
   ```html
   <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/minisearch@7.1.2/dist/umd/index.min.js"></script>
   ```

2. Add CSS styling for search results in the `<header>` of the search page:
   ```html
   <style type="text/css">
      #search-box {
         margin-bottom: 20px;
      }
      #search-input {
         width: 100%;
         padding: 10px;
         font-size: 16px;
         border: 1px solid #ccc;
         box-sizing: border-box;
      }
      #search-results {
         margin-top: 20px;
      }
      .result-item {
         margin-bottom: 20px;
         padding-bottom: 20px;
         border-bottom: 1px dotted #ccc;
      }
      .result-title {
         font-size: 18px;
         font-weight: bold;
         margin-bottom: 5px;
      }
      .result-url {
         color: #43829f;
         margin-bottom: 5px;
      }
      .result-tags {
         font-size: 13px;
         color: #666;
         margin-top: 3px;
      }
      .loading-text {
         display: none;
         font-size: 16px;
         margin: 20px 0;
         font-style: italic;
      }
      .sr-only {
         position: absolute;
         width: 1px;
         height: 1px;
         padding: 0;
         margin: -1px;
         overflow: hidden;
         clip: rect(0, 0, 0, 0);
         white-space: nowrap;
         border: 0;
      }
   </style>
   ```

3. Create the search area with the following HTML. Replace the main content you copied over from the `index.html` into the new `search/index.html` with the following div:
   ```html
   <div class="entry-content">
      <div id="search-box">
         <input type="text" id="search-input" placeholder="Search for podcasts and posts...">
      </div>
      <div class="loading-text">Searching...</div>
      <div id="search-results" aria-live="polite"></div>
      <div id="search-announcement" class="sr-only" aria-live="assertive"></div>
   </div>
   ```

4. Add the JavaScript that powers the search functionality at the bottom of the page before the closing `</body>` tag:
   ```html
   <script>
      document.addEventListener('DOMContentLoaded', function() {
         const searchInput = document.getElementById('search-input');
         const searchResults = document.getElementById('search-results');
         const loadingText = document.querySelector('.loading-text');
         const searchAnnouncement = document.getElementById('search-announcement');
         let miniSearch;
         let documents = [];
         let focusOnResults = false; // Flag to control when to focus on results
         
         // Load the JSON documents
         fetch('/js/search-documents.json')
            .then(response => response.json())
            .then(data => {
               documents = data;
               
               // Initialize MiniSearch
               miniSearch = new MiniSearch({
                  fields: ['title', 'content'],
                  storeFields: ['title', 'url', 'content', 'tags'],
                  searchOptions: {
                     boost: { title: 2 },
                     fuzzy: 0.2
                  }
               });
               
               // Add documents to the index
               miniSearch.addAll(documents);
               
               // Add event listener for Enter key press to trigger focusing on results
               searchInput.addEventListener('keydown', function(e) {
                  if (e.key === 'Enter') {
                     e.preventDefault();
                     const query = this.value.trim();
                     if (query.length >= 3) {
                        focusOnResults = true;
                        performSearch(query);
                     }
                  }
               });
               
               // Function to perform the search
               function performSearch(query) {
                  loadingText.style.display = 'block';
                  
                  // Search after a short delay
                  setTimeout(() => {
                     const results = miniSearch.search(query);
                     displayResults(results, query);
                     loadingText.style.display = 'none';
                     
                     // Only focus on results when explicitly requested (Enter key pressed)
                     if (focusOnResults && results.length > 0) {
                        searchResults.tabIndex = -1;
                        searchResults.focus();
                        searchResults.scrollIntoView({behavior: 'smooth'});
                        focusOnResults = false; // Reset the flag
                     }
                  }, 300);
               }
               
               // Add event listener for search input
               searchInput.addEventListener('input', function() {
                  const query = this.value.trim();
                  
                  if (query.length < 3) {
                     searchResults.innerHTML = '';
                     return;
                  }
                  
                  // During typing, don't focus on results
                  focusOnResults = false;
                  
                  // Use the performSearch function
                  performSearch(query);
               });
            })
            .catch(error => {
               console.error('Error loading search data:', error);
               searchResults.innerHTML = '<p>Error loading search data. Please try again later.</p>';
            });
         
         // Function to display search results
         function displayResults(results, query) {
            if (results.length === 0) {
               searchResults.innerHTML = '<p>No results found for "' + query + '"</p>';
               searchAnnouncement.textContent = 'No results found for "' + query + '"';
               return;
            }
            
            // Create a map to deduplicate results by URL
            const uniqueResults = new Map();
            
            // Keep only the first occurrence of each URL, normalizing URLs to handle both with and without index.html
            results.forEach(result => {
               // Normalize the URL by removing index.html from the end
               const normalizedUrl = result.url.replace(/\/index\.html$/, '/');
               if (!uniqueResults.has(normalizedUrl)) {
                  uniqueResults.set(normalizedUrl, result);
               }
            });
            
            let html = '';
            
            // Display only unique results
            uniqueResults.forEach(result => {
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
            
            // Announce the number of results for screen readers
            const resultsCount = uniqueResults.size;
            searchAnnouncement.textContent = `Found ${resultsCount} result${resultsCount !== 1 ? 's' : ''} for "${query}"`;
         }
      });
   </script>
   ```

5. When adding the search page to the navigation, the easiest way to do this is to open VSCode and use Find and Replace in Files. Copy the current navigation elements, paste into the find field, paste again into the replace field, add the new search URL to the nav element, and then replace all across files. 

## Search Index Generation

The search index is generated by processing all HTML files in the site:

1. `update_search_index.js` is the main script that:
   - Scans for all HTML files in the project
   - Extracts titles, content, and tags from each file
   - Removes stopwords to improve search quality
   - Deduplicates content when the same page appears with different URLs
   - Creates a JSON file with all indexed content

2. Indexing behavior can be customized in the configuration section of `update_search_index.js`:
   - Configure content selectors to extract text from specific elements
   - Set directories or patterns to exclude from indexing
   - Map content types based on directory patterns
   - Define title extraction strategies

3. Stopwords are defined in `static-search/stopwords.txt` and are common words like "the", "and", "or" that are filtered out during indexing to improve search relevance.

## Running the Build Process

1. To generate the search index, run:
   ```bash
   make search-index
   ```
   Or manually:
   ```bash
   sh update_search.sh
   ```
   Or directly:
   ```bash
   node update_search_index.js
   ```

2. This will generate a `search-documents.json` file inside a `js` directory, which MiniSearch will load for the search function.

3. For HTML cleanup (helpful if your HTML has errors or inconsistencies):
   ```bash
   make tidy
   ```
   This runs the `tidy.sh` script which processes all HTML files and logs errors to `errors.log`.

4. To preview the site locally:
   ```bash
   make preview
   ```
   Or manually:
   ```bash
   npx http-server
   ```

## Testing and Deployment

1. Test your search thoroughly, using:
   - Common search terms relevant to the content
   - Partial word searches to test fuzzy matching

2. When creating branches for individual projects, work in the separate branch and deploy to a static dev URL for testing.

3. Commits to `main` branch will deploy to the live site.

## Troubleshooting

- If search shows no results, check:
  - Browser console for JavaScript errors
  - That `search-documents.json` exists and is not empty
  - That file paths in the search results match the actual site structure
  - Sometimes other JavaScript libraries can interfere with MiniSearch without producing an error in the browser console. Try commenting out other JavaScript files (often found in the `<head>` tag) and running the search again. 

- If content is missing from search, check:
  - The selectors in the config object match your HTML structure
  - That files aren't being excluded by the exclusion patterns
  - The search index file is being properly generated

- For HTML parsing issues:
  - Run `make tidy` to identify and log HTML problems
  - Fix structural issues in the source HTML before re-indexing
