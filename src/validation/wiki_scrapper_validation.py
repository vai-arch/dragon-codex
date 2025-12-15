"""
Enhanced WoT Wiki Scraper using MediaWiki API
Gets complete information including infoboxes, categories, and full content

This script uses the Fandom MediaWiki API to extract:
- Main article content (HTML and wikitext)
- Infobox data (biographical, physical, chronological)
- Categories
- All sections and subsections
- Templates used

Author: Dragon's Codex Project
Date: Week 1 Session 2
"""

from pathlib import Path

from src.ingestion.ing_03_wiki_scrapper import WoTWikiScraper


def main():
    """
    Main function - test scraper with example character
    """
    scraper = WoTWikiScraper()

    # Test with Ailil Riatin (the problematic example)
    print("=" * 60)
    print("Testing Enhanced WoT Wiki Scraper")
    print("=" * 60)

    test_character = "Karaethon_Cycle"

    # Get data
    data = scraper.get_page_data(test_character)

    if data:
        print("\n" + "=" * 60)
        print("EXTRACTION RESULTS")
        print("=" * 60)

        print(f"\nTitle: {data['title']}")
        print(f"Page ID: {data.get('pageid')}")

        print(f"\nCategories ({len(data['categories'])}):")
        for cat in data["categories"][:10]:  # First 10
            print(f"  - {cat}")
        if len(data["categories"]) > 10:
            print(f"  ... and {len(data['categories']) - 10} more")

        print("\nInfobox Data:")
        for section_name, section_data in data["infobox"].items():
            if section_data:
                print(f"\n  {section_name.title()} ({len(section_data)} fields):")
                for key, value in list(section_data.items())[:5]:  # First 5
                    print(f"    {key}: {value}")
                if len(section_data) > 5:
                    print(f"    ... and {len(section_data) - 5} more fields")

        print(f"\nContent Sections ({len(data['structured_content'])}):")
        for section in data["structured_content"].keys():
            print(f"  - {section}")

        # Save example
        output_path = Path("test_rand.txt")
        scraper.save_as_markdown(data, output_path)
        print(f"\n✓ Saved enhanced markdown to: {output_path}")

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print("\nThe enhanced scraper is working correctly.")
        print("You can now use it to scrape all your characters.")

    else:
        print("\n✗ Failed to get data")


if __name__ == "__main__":
    main()
