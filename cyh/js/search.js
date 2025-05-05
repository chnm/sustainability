// MiniSearch implementation for CYH website

// Initialize MiniSearch instance
const miniSearch = new MiniSearch({
  fields: ['title', 'content'], // fields to index for full-text search
  storeFields: ['title', 'url', 'tags', 'contentType'], // fields to return with search results (added contentType)
  // Enhanced tokenizer to handle more languages and special characters
  tokenize: (string) => string.toLowerCase().split(/[\s\-\.,:;()\[\]{}'"„"]+/),
  // Add search options for better results
  searchOptions: {
    boost: { title: 2 }, // boost title matches
    fuzzy: 0.2, // enable fuzzy search (for typos)
    prefix: true // match by prefix
  }
});

// Function to fetch and index document data
async function fetchAndIndexDocuments() {
  try {
    console.log('Fetching search index...');
    const response = await fetch('js/search-documents.json');
    if (!response.ok) {
      throw new Error(`Failed to fetch search index: ${response.status} ${response.statusText}`);
    }
    
    const documents = await response.json();
    console.log(`Found ${documents.length} documents in search index`);
    
    // Index the documents
    miniSearch.addAll(documents);
    console.log('Documents indexed successfully');
    return documents;
  } catch (error) {
    console.error('Error in fetchAndIndexDocuments:', error);
    return [];
  }
}

// Function to get static tags
function getCommonTags() {
  return [
    // Time periods
    "1000 BCE-300 CE",
    "300-1000 CE",
    "1000-1500 CE",
    "1500-1800 CE",
    "1750-1914",
    "1900-1945",
    "1945-present",
    
    // Regions
    "Africa",
    "East Asia",
    "Europe",
    "Latin America",
    "Middle East",
    "North America",
    "South Asia",
    
    // Topics
    "Children",
    "Boys",
    "Girls",
    "Family",
    "Education",
    "Orphans",
    "Adoption",
    "Child Labor",
    "Literature",
    "Games",
    "Toys",
    "Health",
    "Religion",
    "Government Documents",
    "Official Documents"
  ];
}

// Function to perform a search with optional tag and content type filtering
function performSearch(query, selectedTags = [], selectedContentTypes = [], allDocuments = []) {
  if (!query && (!selectedTags || selectedTags.length === 0) && (!selectedContentTypes || selectedContentTypes.length === 0)) {
    return [];
  }
  
  let results = [];
  
  if (query && query.trim() !== '') {
    // Perform search with query
    results = miniSearch.search(query, {
      boost: { title: 2 }, // boost title matches
      fuzzy: 0.2, // enable fuzzy search (for typos)
      prefix: true // match by prefix (e.g. "hist" matches "history")
    });
  } else if (allDocuments && allDocuments.length > 0) {
    // If no query but tags or content types are selected, use all documents
    results = allDocuments.map(doc => ({
      id: doc.id,
      title: doc.title,
      url: doc.url,
      tags: doc.tags || [],
      contentType: doc.contentType || 'Other',
      score: 1
    }));
  }
  
  // Filter by selected tags if any
  if (selectedTags && selectedTags.length > 0 && results.length > 0) {
    results = results.filter(result => {
      // Try to get tags from the result object first
      let docTags = result.tags || [];
      
      // If no tags in result, try to find the document in allDocuments
      if (docTags.length === 0 && allDocuments && allDocuments.length > 0) {
        const doc = allDocuments.find(d => d.id === result.id);
        if (doc) {
          docTags = doc.tags || [];
        }
      }
      
      // Check if document has all selected tags
      // Make tag matching case-insensitive
      const lowerDocTags = docTags.map(tag => tag.toLowerCase());
      return selectedTags.every(tag => {
        // Try exact match first
        if (docTags.includes(tag)) return true;
        
        // Try case-insensitive match
        return lowerDocTags.includes(tag.toLowerCase());
      });
    });
  }
  
  // Filter by selected content types if any
  if (selectedContentTypes && selectedContentTypes.length > 0 && results.length > 0) {
    results = results.filter(result => {
      // Get the content type from the result or from allDocuments
      let contentType = result.contentType || 'Other';
      
      // If contentType not in result, try to find it in allDocuments
      if (!contentType && allDocuments && allDocuments.length > 0) {
        const doc = allDocuments.find(d => d.id === result.id);
        if (doc) {
          contentType = doc.contentType || 'Other';
        }
      }
      
      // Check if document's content type matches any of the selected content types
      return selectedContentTypes.includes(contentType);
    });
  }
  
  return results;
}

// Function to display search results
function displaySearchResults(results, allDocuments = []) {
  const resultsContainer = document.getElementById('search-results');
  
  // Clear previous results
  resultsContainer.innerHTML = '';
  
  if (results.length === 0) {
    resultsContainer.innerHTML = '<p>No results found</p>';
    return;
  }
  
  // Create results HTML
  const resultsHtml = `
    <h2>Search Results (${results.length})</h2>
    <ul class="results-list">
      ${results.map(result => {
        // Get tags from result or from allDocuments
        let docTags = result.tags || [];
        if (docTags.length === 0 && allDocuments && allDocuments.length > 0) {
          const doc = allDocuments.find(d => d.id === result.id);
          if (doc && doc.tags) {
            docTags = doc.tags;
          }
        }
        
        return `
          <li class="result-item">
            <a href="${result.url}" class="result-title">${result.title}</a>
            ${result.contentType ? `<div class="result-content-type" data-type="${result.contentType}">${result.contentType}</div>` : ''}
            ${docTags.length > 0 ? `<div class="result-tags">Tags: ${docTags.join(', ')}</div>` : ''}
          </li>
        `;
      }).join('')}
    </ul>
  `;
  
  // Set the results HTML to the results container only
  resultsContainer.innerHTML = resultsHtml;
}

// Function to handle the URL parameters for search
function getQueryParam(param) {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get(param);
}

// Static tag filters based on common categories
function getStaticTagFilters() {
  return `
    <div class="tag-filters">
      <div class="tag-group">
        <h4>Content Type</h4>
        <div class="tag-checkbox">
          <input type="checkbox" id="contentType-Primary-Source" name="contentType" value="Primary Source">
          <label for="contentType-Primary-Source">Primary Source</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="contentType-Case-Study" name="contentType" value="Case Study">
          <label for="contentType-Case-Study">Case Study</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="contentType-Teaching-Module" name="contentType" value="Teaching Module">
          <label for="contentType-Teaching-Module">Teaching Module</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="contentType-Website-Review" name="contentType" value="Website Review">
          <label for="contentType-Website-Review">Website Review</label>
        </div>

        <div class="tag-checkbox">
          <input type="checkbox" id="contentType-Other" name="contentType" value="Other">
          <label for="contentType-Other">Other</label>
        </div>
      </div>
      
      <div class="tag-group">
        <h4>Time Periods</h4>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-1000-BCE-300-CE" name="tags" value="1000 BCE-300 CE">
          <label for="tag-1000-BCE-300-CE">1000 BCE-300 CE</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-300-1000-CE" name="tags" value="300-1000 CE">
          <label for="tag-300-1000-CE">300-1000 CE</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-1000-1500-CE" name="tags" value="1000-1500 CE">
          <label for="tag-1000-1500-CE">1000-1500 CE</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-1500-1800-CE" name="tags" value="1500-1800 CE">
          <label for="tag-1500-1800-CE">1500-1800 CE</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-1750-1914" name="tags" value="1750-1914">
          <label for="tag-1750-1914">1750-1914</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-1900-1945" name="tags" value="1900-1945">
          <label for="tag-1900-1945">1900-1945</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-1945-present" name="tags" value="1945-present">
          <label for="tag-1945-present">1945-present</label>
        </div>
      </div>
      
      <div class="tag-group">
        <h4>Regions</h4>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Africa" name="tags" value="Africa">
          <label for="tag-Africa">Africa</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-East-Asia" name="tags" value="East Asia">
          <label for="tag-East-Asia">East Asia</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Europe" name="tags" value="Europe">
          <label for="tag-Europe">Europe</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Latin-America" name="tags" value="Latin America">
          <label for="tag-Latin-America">Latin America</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Middle-East" name="tags" value="Middle East">
          <label for="tag-Middle-East">Middle East</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-North-America" name="tags" value="North America">
          <label for="tag-North-America">North America</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-South-Asia" name="tags" value="South Asia">
          <label for="tag-South-Asia">South Asia</label>
        </div>
      </div>
      
      <div class="tag-group">
        <h4>Topics</h4>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Children" name="tags" value="Children">
          <label for="tag-Children">Children</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Boys" name="tags" value="Boys">
          <label for="tag-Boys">Boys</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Girls" name="tags" value="Girls">
          <label for="tag-Girls">Girls</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Family" name="tags" value="Family">
          <label for="tag-Family">Family</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Education" name="tags" value="Education">
          <label for="tag-Education">Education</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Orphans" name="tags" value="Orphans">
          <label for="tag-Orphans">Orphans</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Adoption" name="tags" value="Adoption">
          <label for="tag-Adoption">Adoption</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Child-Labor" name="tags" value="Child Labor">
          <label for="tag-Child-Labor">Child Labor</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Literature" name="tags" value="Literature">
          <label for="tag-Literature">Literature</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Games" name="tags" value="Games">
          <label for="tag-Games">Games</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Toys" name="tags" value="Toys">
          <label for="tag-Toys">Toys</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Health" name="tags" value="Health">
          <label for="tag-Health">Health</label>
        </div>
        <div class="tag-checkbox">
          <input type="checkbox" id="tag-Religion" name="tags" value="Religion">
          <label for="tag-Religion">Religion</label>
        </div>
      </div>
    </div>
  `;
}

// Initialize the search functionality when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Index the documents
  fetchAndIndexDocuments().then((documents) => {
    // Store documents for later use
    const allDocuments = documents || [];
    
    // Check if we're on the search page
    const searchContainer = document.getElementById('staticSearch');
    
    if (searchContainer) {
      // Add search form to the page
      searchContainer.innerHTML = `
        <div class="search-container">
          <h2>Search</h2>
          <form id="search-form" class="search-form">
            <div class="search-bar">
              <input type="text" id="search-input" placeholder="Enter search terms..." aria-label="Search term">
              <button type="submit">Search</button>
            </div>
            <div class="filters-container">
              <h3>Filter by Tags</h3>
              <div id="tag-filters">
                ${getStaticTagFilters()}
              </div>
            </div>
          </form>
          <div id="search-results"></div>
        </div>
      `;
      
      // Add event listener for the search form
      const searchForm = document.getElementById('search-form');
      const searchInput = document.getElementById('search-input');
      
      // Check if there's a query parameter from the URL
      const queryParam = getQueryParam('q');
      const tagParams = getQueryParam('tags') ? getQueryParam('tags').split(',') : [];
      const contentTypeParams = getQueryParam('contentTypes') ? getQueryParam('contentTypes').split(',') : [];
      
      // Check tag checkboxes from URL parameters
      if (tagParams.length > 0) {
        tagParams.forEach(tag => {
          // Normalize the tag ID for matching
          const normalizedTagId = tag
            .replace(/\s+/g, '-')
            .replace(/[^\w-]/g, '')
            .replace(/^-+|-+$/g, '');
          
          const checkbox = document.getElementById(`tag-${normalizedTagId}`);
          if (checkbox) checkbox.checked = true;
        });
      }
      
      // Check content type checkboxes from URL parameters
      if (contentTypeParams.length > 0) {
        contentTypeParams.forEach(contentType => {
          // Normalize the content type ID for matching
          const normalizedContentTypeId = contentType
            .replace(/\s+/g, '-')
            .replace(/[^\w-]/g, '')
            .replace(/^-+|-+$/g, '');
          
          const checkbox = document.getElementById(`contentType-${normalizedContentTypeId}`);
          if (checkbox) checkbox.checked = true;
        });
      }
      
      // Perform initial search if there are query, tag, or content type parameters
      if (queryParam || tagParams.length > 0 || contentTypeParams.length > 0) {
        if (queryParam) searchInput.value = queryParam;
        
        // Get selected tags
        const selectedTags = Array.from(document.querySelectorAll('input[name="tags"]:checked'))
          .map(checkbox => checkbox.value);
        
        // Get selected content types
        const selectedContentTypes = Array.from(document.querySelectorAll('input[name="contentType"]:checked'))
          .map(checkbox => checkbox.value);
        
        const results = performSearch(queryParam, selectedTags, selectedContentTypes, allDocuments);
        displaySearchResults(results, allDocuments);
      }
      
      // Add event listener for form submission
      searchForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const query = searchInput.value;
        
        // Get all selected tags
        const selectedTags = Array.from(document.querySelectorAll('input[name="tags"]:checked'))
          .map(checkbox => checkbox.value);
        
        // Get all selected content types
        const selectedContentTypes = Array.from(document.querySelectorAll('input[name="contentType"]:checked'))
          .map(checkbox => checkbox.value);
        
        // Update URL with search query, tags, and content types
        const url = new URL(window.location);
        url.searchParams.set('q', query);
        
        if (selectedTags.length > 0) {
          url.searchParams.set('tags', selectedTags.join(','));
        } else {
          url.searchParams.delete('tags');
        }
        
        if (selectedContentTypes.length > 0) {
          url.searchParams.set('contentTypes', selectedContentTypes.join(','));
        } else {
          url.searchParams.delete('contentTypes');
        }
        
        window.history.pushState({}, '', url);
        
        // Perform search with query, selected tags, and selected content types
        const results = performSearch(query, selectedTags, selectedContentTypes, allDocuments);
        displaySearchResults(results, allDocuments);
      });
      
      // Add event listeners for tag and content type checkboxes
      document.querySelectorAll('input[name="tags"], input[name="contentType"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
          // Instead of submitting the form, directly perform the search
          const query = searchInput.value;
          
          // Get all selected tags
          const selectedTags = Array.from(document.querySelectorAll('input[name="tags"]:checked'))
            .map(checkbox => checkbox.value);
          
          // Get all selected content types
          const selectedContentTypes = Array.from(document.querySelectorAll('input[name="contentType"]:checked'))
            .map(checkbox => checkbox.value);
          
          // Update URL with search query, tags, and content types
          const url = new URL(window.location);
          url.searchParams.set('q', query);
          
          if (selectedTags.length > 0) {
            url.searchParams.set('tags', selectedTags.join(','));
          } else {
            url.searchParams.delete('tags');
          }
          
          if (selectedContentTypes.length > 0) {
            url.searchParams.set('contentTypes', selectedContentTypes.join(','));
          } else {
            url.searchParams.delete('contentTypes');
          }
          
          // Use replaceState instead of pushState to avoid adding to browser history
          window.history.replaceState({}, '', url);
          
          // Perform search with query, selected tags, and selected content types
          const results = performSearch(query, selectedTags, selectedContentTypes, allDocuments);
          displaySearchResults(results, allDocuments);
        });
      });
      
      // Add toggle functionality for the tag filters
      const filtersContainer = document.querySelector('.filters-container');
      const filtersHeading = filtersContainer.querySelector('h3');
      
      filtersHeading.addEventListener('click', function() {
        filtersContainer.classList.toggle('collapsed');
        
        // Store the preference in local storage
        if (filtersContainer.classList.contains('collapsed')) {
          localStorage.setItem('tag-filters-collapsed', 'true');
        } else {
          localStorage.setItem('tag-filters-collapsed', 'false');
        }
      });
      
      // Check if filters were previously collapsed
      if (localStorage.getItem('tag-filters-collapsed') === 'true') {
        filtersContainer.classList.add('collapsed');
      }
    }
  });
  
  // Link the header search box with the search page
  const headerSearchBox = document.getElementById('simple-search');
  
  if (headerSearchBox) {
    // Override the Meilisearch behavior for the simple-search input
    headerSearchBox.addEventListener('keypress', function(event) {
      if (event.key === 'Enter') {
        event.preventDefault();
        const query = headerSearchBox.value.trim();
        if (query) {
          // Redirect to the search page with the query parameter
          window.location.href = `search.html?q=${encodeURIComponent(query)}`;
        }
      }
    });
  }
});
