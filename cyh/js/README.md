# MiniSearch Implementation for CYH

This directory contains the implementation of MiniSearch for the Children & Youth in History website.

## Files

- `minisearch.js` - The MiniSearch library (v6.2.0)
- `search-implementation.js` - Custom implementation for the search functionality
- `search-documents.json` - JSON file containing the indexed documents for search
- `create-search-index.js` - Node.js script to generate the search index from HTML files

## How it Works

1. The MiniSearch library provides client-side full-text search capabilities.
2. The `search-implementation.js` file initializes MiniSearch, loads the document index, and handles user interactions.
3. When a user performs a search, MiniSearch queries the indexed documents and returns relevant results.
4. Results are displayed in the UI with titles, URLs, and tags.

## Generating the Search Index

The `create-search-index.js` script can be used to generate the search index from the website's HTML files. To use it:

1. Install Node.js if not already installed
2. Install required dependencies:
   ```
   npm install jsdom node-fetch fs-extra
   ```
3. Run the script:
   ```
   node create-search-index.js
   ```

This will crawl the specified HTML files, extract content, and generate the `search-documents.json` file.

## Customization

To customize the search functionality:

1. Modify the `search-implementation.js` file to change search behavior or UI.
2. Update the `create-search-index.js` script to include additional files or extract content differently.
3. Adjust the styling in `search.html` to match your website's design.

## Advanced Features

MiniSearch supports several advanced features that can be enabled:

- Fuzzy search for typo tolerance
- Prefix search for autocomplete
- Boosting fields for relevance
- Customized tokenization and term processing

These can be configured in the `search-implementation.js` file.