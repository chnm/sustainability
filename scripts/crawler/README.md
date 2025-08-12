# 9/11 Digital Archive Crawler

A Python script to crawl and extract item URLs from the 9/11 Digital Archive website.

## Purpose

This crawler systematically browses through the 9/11 Digital Archive's item pages to collect URLs for individual items. It's designed to discover and catalog all available items in the archive for further research or analysis.

## How it works

1. Starts from the browse page at `https://911digitalarchive.org/items/browse`
2. Iterates through pages (up to 4,000 pages by default)
3. Extracts all links containing `/items/show/` from each page
4. Collects unique URLs and saves them to `item_urls.txt`
5. Stops when no more items are found or HTTP errors occur

## Requirements

- Python 3.12+
- Dependencies managed with Poetry

## Installation

```bash
poetry install
```

## Usage

```bash
python main.py
```

The script will output its progress and save all discovered URLs to `item_urls.txt`.

## Configuration

You can modify these constants in `main.py`:

- `MAX_PAGES`: Maximum number of pages to crawl (default: 4000)
- `OUTPUT_FILE`: Name of the output file (default: "item_urls.txt")
- `START_PAGE`: Starting page number (default: 1)

## Output

The script generates `item_urls.txt` containing one URL per line, sorted alphabetically.
