import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://911digitalarchive.org"
BROWSE_URL = f"{BASE_URL}/items/browse"
START_PAGE = 1
MAX_PAGES = 4000  # Increase if needed
OUTPUT_FILE = "item_urls.txt"

found_urls = set()

for page in range(START_PAGE, MAX_PAGES + 1):
    print(f"Checking page {page}...")
    response = requests.get(f"{BROWSE_URL}?page={page}")

    if response.status_code != 200:
        print(f"Stopped at page {page}, status code {response.status_code}")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    item_links = soup.select('a[href*="/items/show/"]')

    if not item_links:
        print(f"No items found on page {page}, stopping.")
        break

    for link in item_links:
        href = link.get("href")
        if href and "/items/show/" in href:
            full_url = urljoin(BASE_URL, href)
            found_urls.add(full_url)

print(f"Found {len(found_urls)} unique item URLs.")

with open(OUTPUT_FILE, "w") as f:
    for url in sorted(found_urls):
        f.write(url + "\n")

print(f"URLs saved to {OUTPUT_FILE}")
