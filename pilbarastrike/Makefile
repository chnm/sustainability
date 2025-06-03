.PHONY: tidy search-index preview all

all: 
	@echo "Available commands:"
	@echo "  make tidy         - Run HTML Tidy on files"
	@echo "  make search-index - Build the search index for minisearch"
	@echo "  make preview      - Start a local web server to preview the site"

# run HTML Tidy
tidy: 
	cd static-search && sh tidy.sh

# build the search index for minisearch
search-index: 
	sh update_search.sh

preview : 
	npx http-server
