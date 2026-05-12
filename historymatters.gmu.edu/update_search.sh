#!/bin/bash

if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js to run this script."
    exit 1
fi

if [ ! -d "node_modules/cheerio" ]; then
    echo "Installing required packages..."
    npm install cheerio
fi

echo "Updating search index..."
node update_search_index.js
echo "Search index update complete!"
