#!/bin/bash

# Make sure Node.js and required packages are installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js to run this script."
    exit 1
fi

# Install required packages if they don't exist
if [ ! -d "node_modules/cheerio" ]; then
    echo "Installing required packages..."
    npm install cheerio
fi

# Run the Node.js script to update the search index
echo "Updating search index..."
node update_search_index.js

echo "Search index update complete!"