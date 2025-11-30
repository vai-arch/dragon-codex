"""

RUN ORDER -> 02
Batch Scraper for All WoT Characters
Uses the enhanced scraper to get all character data with infoboxes

This script will scrape all characters from a list and save enhanced markdown files.
"""

import json
from pathlib import Path
import sys

# Import the scraper (make sure enhanced_wiki_scraper.py is in same directory or Python path)
try:
    from wiki_scraper import WoTWikiScraper
except ImportError:
    print("Error: Cannot import wiki_scraper.py")
    print("Make sure both scripts are in the same directory!")
    sys.exit(1)


def load_character_list(file_path):
    """
    Load character list from file
    
    Supports:
    - JSON file with array of names or objects
    - Text file with one name per line
    
    Args:
        file_path: Path to character list file
    
    Returns:
        list of character names
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return []
    
    # Try JSON first
    if file_path.suffix.lower() == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'characters' in data:
                return data['characters']
            else:
                print("Error: JSON file format not recognized")
                return []
    
    # Try text file (one name per line)
    elif file_path.suffix.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f if line.strip()]
            return names
    
    else:
        print(f"Error: Unsupported file format: {file_path.suffix}")
        return []


def create_sample_character_list(output_path):
    """
    Create a sample character list file for testing
    
    Args:
        output_path: Where to save the sample list
    """
    # Major WoT characters for testing
    sample_characters = [
        "Rand al'Thor",
        "Egwene al'Vere",
        "Perrin Aybara",
        "Matrim Cauthon",
        "Nynaeve al'Meara",
        "Moiraine Damodred",
        "Lan Mandragoran",
        "Elayne Trakand",
        "Aviendha",
        "Min Farshaw",
        "Thom Merrilin",
        "Loial",
        "Faile Bashere",
        "Siuan Sanche",
        "Gawyn Trakand",
        "Galad Damodred",
        "Tuon Athaem Kore Paendrag",
        "Birgitte Silverbow",
        "Cadsuane Melaidhrin",
        "Logain Ablar"
    ]
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_characters, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created sample character list: {output_path}")
    print(f"  Contains {len(sample_characters)} major characters")
    
    return sample_characters


def scrape_all_characters(character_list_file, output_dir, delay=1.0, resume_from=None):
    """
    Scrape all pages from a list file
    
    Args:
        character_list_file: Path to JSON or TXT file with page names
        output_dir: Directory to save markdown files
        delay: Seconds between requests (default 1.0)
        resume_from: Page name to resume from (for interrupted scrapes)
    """
    # Load page list
    print(f"Loading page list from: {character_list_file}")
    pages = load_character_list(character_list_file)
    
    if not pages:
        print("Error: No pages loaded!")
        return
    
    print(f"✓ Loaded {len(pages)} pages\n")
    
    # Handle resume
    if resume_from:
        try:
            resume_index = pages.index(resume_from)
            pages = pages[resume_index:]
            print(f"✓ Resuming from page {resume_index + 1}: {resume_from}\n")
        except ValueError:
            print(f"⚠ Resume page '{resume_from}' not found, starting from beginning\n")
    
    # Check what's already done
    output_path = Path(output_dir)
    if output_path.exists():
        existing_files = set(f.stem for f in output_path.glob('*.txt'))
        if existing_files:
            print(f"✓ Found {len(existing_files)} already scraped files")
            print(f"  Will skip existing files and only scrape new ones\n")
    
    # Create scraper
    scraper = WoTWikiScraper()
    
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
    
    # Estimate time
    if stats['success'] > 0:
        avg_time = stats['total'] * delay
        print(f"\nTotal time: ~{avg_time/60:.1f} minutes")
    
    if stats['errors']:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats['errors'][:10]:  # Show first 10
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")
        
        # Save error log
        error_log = Path(output_dir) / 'scraping_errors.txt'
        with open(error_log, 'w', encoding='utf-8') as f:
            for error in stats['errors']:
                f.write(f"{error}\n")
        print(f"\n✓ Error log saved to: {error_log}")
    
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
    
    # Example 1: Create and use sample list
    print("OPTION 1: Test with sample character list")
    print("-" * 60)
    
    sample_list = Path("sample_characters.json")
    output_dir_sample = Path("data/test_wiki_enhanced")
    
    print(f"This will:")
    print(f"  1. Create sample list: {sample_list}")
    print(f"  2. Scrape ~20 major characters")
    print(f"  3. Save to: {output_dir_sample}")
    print()
    
    response = input("Run sample scrape? (y/n): ").strip().lower()
    
    if response == 'y':
        # Create sample list
        create_sample_character_list(sample_list)
        
        # Scrape sample characters
        scrape_all_characters(
            character_list_file=sample_list,
            output_dir=output_dir_sample,
            delay=1.0
        )
    
    print("\n" + "="*60)
    print("OPTION 2: Scrape from your own character list")
    print("-" * 60)
    print()
    print("To scrape your full character list:")
    print("  1. Create a file with character names (JSON or TXT)")
    print("  2. Run this script with your file")
    print()
    print("Example usage:")
    print("  python batch_scraper.py")
    print()
    print("Then when prompted, choose option 2 and provide:")
    print("  - Path to your character list file")
    print("  - Output directory for enhanced markdown files")
    print()
    
    response = input("Scrape from custom list? (y/n): ").strip().lower()
    
    if response == 'y':
        # list_file = input("Path to character list file: ").strip()
        list_file = "data/auxiliary/wiki/wiki_all_page_titles.json"
        # output_dir = input("Output directory: ").strip()
        output_dir = "data/raw/wiki_original"
        
        if list_file and output_dir:
            scrape_all_characters(
                character_list_file=list_file,
                output_dir=output_dir,
                delay=1.0
            )
    
    print("\n✓ Done!")


if __name__ == "__main__":
    main()