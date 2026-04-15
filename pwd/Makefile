.PHONY: all fetch fetch-pages fetch-items fetch-media extract-news dashboard build index serve clean

all:
	@echo "Available commands:"
	@echo "  make fetch          - Run all API fetch scripts"
	@echo "  make fetch-pages    - Fetch editorial pages from Omeka API"
	@echo "  make fetch-items    - Fetch all items from Omeka API"
	@echo "  make fetch-media    - Download media files from Omeka API"
	@echo "  make extract-news   - Extract news posts from wget HTML"
	@echo "  make build          - Build the Hugo site"
	@echo "  make serve          - Start Hugo development server"
	@echo "  make clean          - Remove generated files"

fetch: fetch-pages fetch-items

fetch-pages:
	python3 scripts/fetch_pages.py

fetch-items:
	python3 scripts/fetch_items.py

fetch-media:
	python3 scripts/fetch_media.py

extract-news:
	python3 scripts/extract_news.py

dashboard:
	python3 scripts/build_transcription_dashboard.py

build:
	ulimit -n 65536 && hugo --minify
	npx pagefind --site public

index:
	npx pagefind --site public

serve:
	hugo server --bind 0.0.0.0 --poll 1s

serve-search:
	@echo "Serving built site with search at http://localhost:1313"
	cd public && python3 -m http.server 1313

clean:
	rm -rf public/
