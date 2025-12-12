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

import requests
import json
import time
from pathlib import Path
from tqdm import tqdm
from src.utils.config import Config
from src.utils.util_files_functions import load_json_from_file, remove_file, save_json_to_file

class WikiPageListDownloader:
    """
    Downloads complete list of all pages from a MediaWiki wiki
    """
    
    def __init__(self, base_url=Config().WIKI_BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DragonCodex/1.0 (Educational RAG Project)'
        })
    
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
                    'action': 'query',
                    'list': 'allpages',
                    'apnamespace': namespace,
                    'aplimit': 500,  # Max per request
                    'format': 'json'
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
                if 'query' in data and 'allpages' in data['query']:
                    pages = data['query']['allpages']
                    
                    for page in pages:
                        all_pages.append({
                            'title': page['title'],
                            'pageid': page['pageid'],
                            'namespace': namespace
                        })
                    
                    pbar.update(len(pages))
                
                # Check for continuation
                if 'continue' in data:
                    continue_token = data['continue']
                    time.sleep(delay)  # Be nice to the server
                else:
                    # No more pages
                    break
        
        if(len(all_pages) == 0):
            raise ValueError(f"No pages were downloaded from namespace {namespace}.")

        print(f"\n✓ Downloaded {len(all_pages)} pages from namespace {namespace}")

        save_json_to_file(all_pages, Config().FILE_WIKI_ALL_PAGES, 2)

        # Create simple page title list for batch scraper
        page_titles = [page['title'] for page in all_pages]
        save_json_to_file(page_titles, Config().FILE_WIKI_ALL_PAGE_TITLES, 2)  
    
    def get_all_categories(self, delay=0.5):
        """
        Get all categories from the wiki
        
        Returns:
            list of category names
        """
        all_categories = []
        continue_token = None
        
        print(f"Fetching all categories...")
        print()
        
        with tqdm(desc="Downloading categories", unit=" cats") as pbar:
            while True:
                params = {
                    'action': 'query',
                    'list': 'allcategories',
                    'aclimit': 500,
                    'format': 'json'
                }
                
                if continue_token:
                    params.update(continue_token)
                
                try:
                    response = self.session.get(self.api_url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                except Exception as e:
                    print(f"\n✗ Error fetching categories: {e}")
                    break
                
                if 'query' in data and 'allcategories' in data['query']:
                    categories = data['query']['allcategories']
                    
                    for cat in categories:
                        all_categories.append(cat['*'])
                    
                    pbar.update(len(categories))
                
                if 'continue' in data:
                    continue_token = data['continue']
                    time.sleep(delay)
                else:
                    break
        
        if(len(all_categories) == 0):
            raise ValueError(f"No categories were downloaded.")

        print(f"\n✓ Downloaded {len(all_categories)} categories")

        save_json_to_file(all_categories, Config().FILE_WIKI_ALL_CATEGORIES, 2)

        return all_categories

def main():
    """
    Main function
    """
    print("\n")
    print("="*60)
    print("WoT Wiki - Complete Page List Downloader")
    print("="*60)
    print()
    print("This will download the complete list of ALL pages from the")
    print("Wheel of Time Fandom wiki using the MediaWiki API.")
    print("Time: ~2-5 minutes")
    print("Output: JSON files in data/ directory")
    print()
    
    # Create downloader
    downloader = WikiPageListDownloader()
    
    # Download everything
    downloader.get_all_pages()
        
    downloader.get_all_categories()
    
    print("\n✓ SUCCESS!")


if __name__ == "__main__":
    main()