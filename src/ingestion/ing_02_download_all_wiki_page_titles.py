"""

RUN ORDER-> 01

WoT Wiki Complete Page List Downloader
Uses MediaWiki API to get ALL pages from the WoT Fandom wiki

This script fetches every single page title from the wiki, including:
- Characters, Locations, Objects, Concepts, Events, Organizations
- Books, Chapters, Prophecies, Terminology
- Everything!

Author: Dragon's Codex Project

**Press `y` when asked**

**What it does:**
- Gets ALL page titles from WoT wiki via API

Input: None
Output: - 'wiki_all_pages.json'
        - 'wiki_all_categories.json'
        - 'wiki_all_page_titles.json'
"""

import sys
import time
import traceback
from datetime import datetime

import requests
from tqdm import tqdm

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import save_json_to_file
from src.utils.util_statistics import total_statistics_logging

cfg_wiki_base_url = None
out_file_wiki_all_pages = None
out_file_wiki_all_page_titles = None
out_file_wiki_all_categories = None


class WikiPageListDownloader:
    """
    Downloads complete list of all pages from a MediaWiki wiki
    """

    def __init__(self, cfg_wiki_base_url, out_file_wiki_all_pages, out_file_wiki_all_page_titles, out_file_wiki_all_categories):
        self.base_url = cfg_wiki_base_url
        self.api_url = f"{cfg_wiki_base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DragonCodex/1.0 (Educational RAG Project)"})

        self.file_wiki_all_pages = out_file_wiki_all_pages
        self.file_wiki_all_page_titles = out_file_wiki_all_page_titles
        self.file_wiki_all_categories = out_file_wiki_all_categories

    def get_all_pages(self, namespace=0, delay=0.5):
        """
        Get all pages from the wiki using allpages API

        Args:
            namespace: 0 = main namespace (articles), 14 = categories
            delay: Seconds to wait between requests

        Returns:
            list of page titles
        """
        all_pages = []
        continue_token = None

        print(f"Fetching all pages from namespace {namespace}...")
        print(f"API: {self.api_url}")
        print()

        with tqdm(desc="Downloading pages", unit=" pages") as pbar:
            while True:
                # Build parameters
                params = {
                    "action": "query",
                    "list": "allpages",
                    "apnamespace": namespace,
                    "aplimit": 500,  # Max per request
                    "format": "json",
                }

                # Add continuation token if we have one
                if continue_token:
                    params.update(continue_token)

                # Make request
                try:
                    response = self.session.get(self.api_url, params=params)
                    response.raise_for_status()
                    data = response.json()

                except Exception as e:
                    print(f"\n✗ Error fetching pages: {e}")
                    break

                # Extract pages
                if "query" in data and "allpages" in data["query"]:
                    pages = data["query"]["allpages"]

                    for page in pages:
                        all_pages.append({"title": page["title"], "pageid": page["pageid"], "namespace": namespace})

                    pbar.update(len(pages))

                # Check for continuation
                if "continue" in data:
                    continue_token = data["continue"]
                    time.sleep(delay)  # Be nice to the server
                else:
                    # No more pages
                    break

        if len(all_pages) == 0:
            raise ValueError(f"No pages were downloaded from namespace {namespace}.")

        print(f"\n✓ Downloaded {len(all_pages)} pages from namespace {namespace}")

        save_json_to_file(all_pages, self.file_wiki_all_pages, 2)

        # Create simple page title list for batch scraper
        page_titles = [page["title"] for page in all_pages]
        save_json_to_file(page_titles, self.file_wiki_all_page_titles, 2)

        return all_pages

    def get_all_categories(self, delay=0.5):
        """
        Get all categories from the wiki

        Returns:
            list of category names
        """
        all_categories = []
        continue_token = None

        print("Fetching all categories...")
        print()

        with tqdm(desc="Downloading categories", unit=" cats") as pbar:
            while True:
                params = {"action": "query", "list": "allcategories", "aclimit": 500, "format": "json"}

                if continue_token:
                    params.update(continue_token)

                try:
                    response = self.session.get(self.api_url, params=params)
                    response.raise_for_status()
                    data = response.json()

                except Exception as e:
                    print(f"\n✗ Error fetching categories: {e}")
                    break

                if "query" in data and "allcategories" in data["query"]:
                    categories = data["query"]["allcategories"]

                    for cat in categories:
                        all_categories.append(cat["*"])

                    pbar.update(len(categories))

                if "continue" in data:
                    continue_token = data["continue"]
                    time.sleep(delay)
                else:
                    break

        if len(all_categories) == 0:
            raise ValueError("No categories were downloaded.")

        print(f"\n✓ Downloaded {len(all_categories)} categories")

        save_json_to_file(all_categories, self.file_wiki_all_categories, 2)

        return all_categories


def main():
    start_time = datetime.now()

    # Create downloader
    downloader = WikiPageListDownloader(cfg_wiki_base_url, out_file_wiki_all_pages, out_file_wiki_all_page_titles, out_file_wiki_all_categories)

    # Download everything
    all_pages = downloader.get_all_pages()

    all_categories = downloader.get_all_categories()

    statistics = {"name": "wiki_iniventory", "metrics": {"number_of_pages": len(all_pages), "number_of_categories": len(all_categories)}}

    total_time = datetime.now() - start_time
    total_statistics_logging(log_name="ing_02_download_all_wiki_page_titles", statistics=statistics, title="WIKI INVENTORY", total_time=total_time)

    print("\n✓ SUCCESS!")


if __name__ == "__main__":
    config = get_config()
    paths = get_paths()

    cfg_wiki_base_url = config.WIKI_BASE_URL
    out_file_wiki_all_pages = paths.FILE_WIKI_ALL_PAGES
    out_file_wiki_all_page_titles = paths.FILE_WIKI_ALL_PAGE_TITLES
    out_file_wiki_all_categories = paths.FILE_WIKI_ALL_CATEGORIES

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
