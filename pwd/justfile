# Papers of the War Department — build commands

# List available commands
default:
    @just --list

# Run all API fetch scripts
fetch: fetch-pages fetch-items

# Fetch editorial pages from Omeka API
fetch-pages:
    python3 scripts/fetch_pages.py

# Fetch all items from Omeka API
fetch-items:
    python3 scripts/fetch_items.py

# Download media files from Omeka API
fetch-media:
    python3 scripts/fetch_media.py

# Extract news posts from wget HTML
extract-news:
    python3 scripts/extract_news.py

# Build the Hugo site
build:
    ulimit -n 65536 && hugo --minify
    npx pagefind --site public

# Build Pagefind search index
index:
    npx pagefind --site public

# Start Hugo development server
serve:
    hugo server --bind 0.0.0.0 --poll 1s

# Serve built site with search
serve-search:
    cd public && python3 -m http.server 1313

# Remove generated files
clean:
    rm -rf public/
