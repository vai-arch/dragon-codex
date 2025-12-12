"""
Batch Scraper for All WoT Characters using the results of download_all_wiki_page_titles.py

Uses the enhanced scraper from the script wiki_scraper.py to get all character data with infoboxes

This script will scrape all characters from a list and save enhanced markdown files.

Input: data/raw/wiki_all_page_titles.json
Output: - data/raw/wiki/*.txt
        - data/raw/wiki_original/*.txt

"""

import json
from pathlib import Path
import sys
from src.utils.config import Config
from src.utils.util_files_functions import copy_files
from src.utils.util_files_functions import load_json_from_file, remove_file, save_json_to_file
from src.ingestion.wiki.pass_02_uses_this_wiki_scraper import WoTWikiScraper

wiki_all_pages_titles_file = Config().FILE_WIKI_ALL_PAGE_TITLES
output_dir = Config().WIKI_ORIGINAL_PATH
final_dir = Config().WIKI_PATH
wiki_glossary_dir = Config().WIKI_GLOSSARY_PATH

def scrape_all_characters(wiki_all_pages_titles_file, output_dir, delay=1.0, resume_from=None):
    """
    Scrape all pages from a list file
    
    Args:
        character_list_file: Path to JSON or TXT file with page names
        output_dir: Directory to save markdown files
        delay: Seconds between requests (default 1.0)
        resume_from: Page name to resume from (for interrupted scrapes)
    """
    # Load page list

    pages = load_json_from_file(wiki_all_pages_titles_file)
    
    print(f"✓ Loaded {len(pages)} pages\n")
    
    # Create scraper
    scraper = WoTWikiScraper(base_url=Config().WIKI_BASE_URL)
    
    # Scrape all pages
    stats = scraper.scrape_character_list(
        character_names=pages,
        output_dir=output_dir,
        delay=delay
    )
    
    # Print summary
    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"\nTotal pages: {stats['total']}")
    print(f"Successfully scraped: {stats['success']}")
    print(f"Failed: {stats['failed']}")

    print(f"\n✓ Enhanced markdown files saved to: {output_dir}")
    
    return stats

def main():
    """
    Main function with example usage
    """
    print("="*60)
    print("WoT Character Batch Scraper")
    print("="*60)
    print()
    
    scrape_all_characters(
        wiki_all_pages_titles_file=wiki_all_pages_titles_file,
        output_dir=output_dir,
        delay=1.0
    )
    
    # After scraping, copy files to final directory
    copy_files(output_dir, final_dir, extension=".txt")
    copy_files(wiki_glossary_dir, final_dir, extension=".txt")

    print("\n✓ Done!")

if __name__ == "__main__":
    main()