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
- Saves to `data/auxiliary/wiki/wiki_all_page_titles.json`
- You'll get ~15,000 page titles (not just 6,000 characters!)

**Output you'll see:**
```
Total Pages: 15,234
✓ Saved to: data/auxiliary/wiki/wiki_all_page_titles.json
"""

import requests
import json
import time
from pathlib import Path
from tqdm import tqdm


class WikiPageListDownloader:
    """
    Downloads complete list of all pages from a MediaWiki wiki
    """
    
    def __init__(self, base_url="https://wot.fandom.com"):
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
        
        print(f"\n✓ Downloaded {len(all_pages)} pages from namespace {namespace}")
        return all_pages
    
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
        
        print(f"\n✓ Downloaded {len(all_categories)} categories")
        return all_categories
    
    def get_category_members(self, category_name, delay=0.5):
        """
        Get all pages in a specific category
        
        Args:
            category_name: Name of category (with or without "Category:" prefix)
            delay: Seconds between requests
        
        Returns:
            list of page titles in the category
        """
        # Ensure category name has proper prefix
        if not category_name.startswith('Category:'):
            category_name = f'Category:{category_name}'
        
        members = []
        continue_token = None
        
        print(f"Fetching members of: {category_name}")
        
        with tqdm(desc="Downloading members", unit=" pages") as pbar:
            while True:
                params = {
                    'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': category_name,
                    'cmlimit': 500,
                    'format': 'json'
                }
                
                if continue_token:
                    params.update(continue_token)
                
                try:
                    response = self.session.get(self.api_url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                except Exception as e:
                    print(f"\n✗ Error: {e}")
                    break
                
                if 'query' in data and 'categorymembers' in data['query']:
                    pages = data['query']['categorymembers']
                    
                    for page in pages:
                        members.append({
                            'title': page['title'],
                            'pageid': page['pageid'],
                            'category': category_name
                        })
                    
                    pbar.update(len(pages))
                
                if 'continue' in data:
                    continue_token = data['continue']
                    time.sleep(delay)
                else:
                    break
        
        print(f"✓ Found {len(members)} members")
        return members
    
    def download_complete_wiki(self, output_dir='data/auxiliary/wiki'):
        """
        Download complete page list from wiki
        
        Downloads:
        1. All main namespace pages (articles)
        2. All categories
        3. Category memberships for major categories
        
        Args:
            output_dir: Where to save the JSON files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            'all_pages': [],
            'categories': [],
            'category_members': {},
            'statistics': {}
        }
        
        print("="*60)
        print("WoT Wiki Complete Download")
        print("="*60)
        print()
        
        # 1. Get all main namespace pages (articles)
        print("STEP 1: Getting all article pages...")
        print("-"*60)
        results['all_pages'] = self.get_all_pages(namespace=0)
        
        # Save immediately
        pages_file = output_dir / 'wiki_all_pages.json'
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(results['all_pages'], f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to: {pages_file}\n")
        
        # 2. Get all categories
        print("STEP 2: Getting all categories...")
        print("-"*60)
        results['categories'] = self.get_all_categories()
        
        # Save
        cats_file = output_dir / 'wiki_all_categories.json'
        with open(cats_file, 'w', encoding='utf-8') as f:
            json.dump(results['categories'], f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to: {cats_file}\n")
        
        # 3. Get members of major categories
        print("STEP 3: Getting category memberships...")
        print("-"*60)
        
        major_categories = [
            'Characters',
            'Locations',
            'Objects',
            'Events',
            'Organizations',
            'Books',
            'Aes Sedai',
            'Prophecies'
        ]
        
        for cat_name in major_categories:
            print(f"\n{cat_name}:")
            members = self.get_category_members(cat_name)
            results['category_members'][cat_name] = members
        
        # Save category members
        cat_members_file = output_dir / 'wiki_category_members.json'
        with open(cat_members_file, 'w', encoding='utf-8') as f:
            json.dump(results['category_members'], f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved to: {cat_members_file}\n")
        
        # 4. Calculate statistics
        print("="*60)
        print("STATISTICS")
        print("="*60)
        
        results['statistics'] = {
            'total_pages': len(results['all_pages']),
            'total_categories': len(results['categories']),
            'category_breakdown': {}
        }
        
        for cat_name, members in results['category_members'].items():
            results['statistics']['category_breakdown'][cat_name] = len(members)
        
        print(f"\nTotal Pages: {results['statistics']['total_pages']:,}")
        print(f"Total Categories: {results['statistics']['total_categories']:,}")
        print("\nMajor Categories:")
        for cat_name, count in results['statistics']['category_breakdown'].items():
            print(f"  {cat_name:.<30} {count:>6,} pages")
        
        # Save complete results
        complete_file = output_dir / 'wiki_complete_index.json'
        with open(complete_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Complete index saved to: {complete_file}")
        
        # Create simple page title list for batch scraper
        page_titles = [page['title'] for page in results['all_pages']]
        titles_file = output_dir / 'wiki_all_page_titles.json'
        with open(titles_file, 'w', encoding='utf-8') as f:
            json.dump(page_titles, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Page titles list saved to: {titles_file}")
        
        print("\n" + "="*60)
        print("DOWNLOAD COMPLETE!")
        print("="*60)
        print(f"\nFiles created in {output_dir}:")
        print(f"  1. wiki_all_pages.json - Complete page list with IDs")
        print(f"  2. wiki_all_categories.json - All category names")
        print(f"  3. wiki_category_members.json - Major category memberships")
        print(f"  4. wiki_complete_index.json - Everything combined")
        print(f"  5. wiki_all_page_titles.json - Simple title list for scraping")
        print()
        print("Next step: Use wiki_all_page_titles.json with batch_scraper.py")
        print(f"to scrape all {results['statistics']['total_pages']:,} pages!")
        
        return results


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
    print()
    print("What you'll get:")
    print("  • All article pages (10,000-20,000 pages)")
    print("  • All categories")
    print("  • Category memberships for major categories")
    print()
    print("Time: ~2-5 minutes")
    print("Output: JSON files in data/ directory")
    print()
    
    response = input("Continue? (y/n): ").strip().lower()
    
    if response != 'y':
        print("\nCancelled.")
        return
    
    print()
    
    # Create downloader
    downloader = WikiPageListDownloader()
    
    # Download everything
    results = downloader.download_complete_wiki()
    
    print("\n✓ SUCCESS!")
    print(f"\nYou now have the complete wiki index with {results['statistics']['total_pages']:,} pages.")
    print("\nTo scrape all pages with enhanced data:")
    print("  python scripts/batch_scraper.py")
    print()
    print("When prompted:")
    print("  • Choose option 2 (custom list)")
    print("  • List file: data/wiki_all_page_titles.json")
    print("  • Output: data/raw/wiki_complete")
    print()


if __name__ == "__main__":
    main()