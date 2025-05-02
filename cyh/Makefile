.PHONY: tidy search-index all

all: 
	echo "Please choose a command; options are `tidy` or `index`."

# run HTML Tidy
tidy: 
	
	cd search && sh tidy.sh

# build the search index for minisearch
search-index: 
	sh update_search.sh
