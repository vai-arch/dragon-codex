"""
Dragon's Codex - Wiki Category Analyzer
Extracts categories from all wiki files and creates mappings.

This script:
1. Scans all wiki .txt files
2. Extracts categories from <!-- Categories: ... --> metadata
3. Creates filename → categories mapping
4. Creates category → files mapping
5. Generates analysis summary
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from src.utils.config import Config
from tqdm import tqdm

CATEGORY_OVERRIDES = {
    'Elayne_Trakand_Chronology.txt': ['Character_Chronologies'],
    'Egwene_al\'Vere_Chronology.txt': ['Character_Chronologies'],
    # Add any future overrides here
}

def extract_categories_from_file(filepath, overrides=None):
    """
    Extract categories from a wiki file.
    
    Categories are in format:
    <!-- Categories: Cat1, Cat2, Cat3 -->
    
    Args:
        filepath: Path to wiki .txt file
        
    Returns:
        list: List of category names (empty list if no categories found)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for <!-- Categories: ... --> pattern
        # Pattern explanation:
        # <!--\s*Categories:\s* - matches "<!-- Categories:" with optional whitespace
        # (.*?) - captures everything (non-greedy) as the categories
        # \s*--> - matches "-->" with optional whitespace before it
        pattern = r'<!--\s*Categories:\s*(.*?)\s*-->'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            categories_str = match.group(1)
            # Split by comma and strip whitespace
            categories = [cat.strip() for cat in categories_str.split(',')]
            # Filter out empty strings
            categories = [cat for cat in categories if cat]

            # Apply overrides if they exist for this file
            if overrides and filepath.name in overrides:
                categories.extend(overrides[filepath.name])
                categories = list(set(categories))  # Deduplicate
            
            return categories
        
        return []
        
    except Exception as e:
        print(f"Error reading {filepath.name}: {e}")
        return []


def analyze_wiki_categories(wiki_dir):
    """
    Scan all wiki files and build category mappings.
    
    Args:
        wiki_dir: Path to directory containing wiki .txt files
        
    Returns:
        tuple: (filename_to_categories, category_to_files)
            - filename_to_categories: dict {filename: [categories]}
            - category_to_files: dict {category: [filenames]}
    """
    wiki_path = Path(wiki_dir)
    
    if not wiki_path.exists():
        raise FileNotFoundError(f"Wiki directory not found: {wiki_path}")
    
    # Get all .txt files
    txt_files = list(wiki_path.glob('*.txt'))
    
    print(f"\n🔍 Found {len(txt_files)} wiki files to analyze")
    
    if len(txt_files) == 0:
        print("⚠️  WARNING: No .txt files found in wiki directory!")
        return {}, {}
    
    # Initialize mappings
    filename_to_categories = {}
    category_to_files = defaultdict(list)
    filenames_with_no_categories = defaultdict(list)
    
    # Track statistics
    files_with_categories = 0
    files_without_categories = 0
    
    # Process each file with progress bar
    print("\n📊 Extracting categories from wiki files...")
    for filepath in tqdm(txt_files, desc="Processing", unit="file"):
        filename = filepath.name
        categories = extract_categories_from_file(filepath, CATEGORY_OVERRIDES)
        
        # Store filename → categories mapping
        filename_to_categories[filename] = categories
        
        # Build category → files mapping
        if categories:
            files_with_categories += 1
            for category in categories:
                category_to_files[category].append(filename)
        else:
            files_without_categories += 1
            # category_to_files["unknown_category"].append(filename)
    
    print(f"\n✅ Analysis complete!")
    print(f"   Files with categories: {files_with_categories}")
    print(f"   Files without categories: {files_without_categories}")
    print(f"   Total unique categories: {len(category_to_files)}")
    
    return filename_to_categories, dict(category_to_files)


def save_results(filename_to_categories, category_to_files, output_dir):
    """
    Save analysis results to JSON files and generate summary.
    
    Args:
        filename_to_categories: dict {filename: [categories]}
        category_to_files: dict {category: [filenames]}
        output_dir: Path to output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving results to {output_path}")
    
    # Save filename → categories mapping
    filename_cats_path = Config().FILE_FILENAME_TO_CATEGORIES

    with open(filename_cats_path, 'w', encoding='utf-8') as f:
        json.dump(filename_to_categories, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Saved {filename_cats_path.name}")
    
    # Save category → files mapping (with counts)
    category_counts = {
        category: {
            'count': len(files),
            'files': sorted(files)  # Sort for easier reading
        }
        for category, files in category_to_files.items()
    }
    
    category_counts_path = output_path / 'category_to_files.json'
    with open(category_counts_path, 'w', encoding='utf-8') as f:
        json.dump(category_counts, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Saved {category_counts_path.name}")
    
    # Generate and save summary
    summary_path = output_path / 'category_analysis_summary.txt'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("WIKI CATEGORY ANALYSIS SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        # Overall statistics
        total_files = len(filename_to_categories)
        files_with_cats = sum(1 for cats in filename_to_categories.values() if cats)
        files_without_cats = total_files - files_with_cats
        total_categories = len(category_to_files)
        
        f.write(f"Total wiki files analyzed: {total_files}\n")
        f.write(f"Files with categories: {files_with_cats}\n")
        f.write(f"Files without categories: {files_without_cats}\n")
        f.write(f"Total unique categories: {total_categories}\n\n")
        
        # Top categories by file count
        f.write("=" * 80 + "\n")
        f.write("TOP 50 CATEGORIES BY FILE COUNT\n")
        f.write("=" * 80 + "\n\n")
        
        sorted_categories = sorted(
            category_to_files.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for i, (category, files) in enumerate(sorted_categories[:50], 1):
            f.write(f"{i:3d}. {category:40s} : {len(files):5d} files\n")
        
        # Character-related categories analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("CHARACTER-RELATED CATEGORIES\n")
        f.write("=" * 80 + "\n\n")
        
        character_indicators = [
            'Men', 'Women', 'Character_Chronologies', 
            'POV_character', 'Deceased', 'Living_as_of_AMOL'
        ]
        
        for category in character_indicators:
            if category in category_to_files:
                count = len(category_to_files[category])
                f.write(f"{category:30s} : {count:5d} files\n")
        
        # Concept-related categories
        f.write("\n" + "=" * 80 + "\n")
        f.write("CONCEPT/PLACE/EVENT CATEGORIES (Sample)\n")
        f.write("=" * 80 + "\n\n")
        
        concept_indicators = [
            'Wars', 'Battles', 'Geographical_regions', 'Cities',
            'Organizations', 'One_Power', 'Prophecies', 'Ajah'
        ]
        
        for category in concept_indicators:
            if category in category_to_files:
                count = len(category_to_files[category])
                f.write(f"{category:30s} : {count:5d} files\n")
        
        # All categories alphabetically
        f.write("\n" + "=" * 80 + "\n")
        f.write("ALL CATEGORIES (ALPHABETICAL)\n")
        f.write("=" * 80 + "\n\n")
        
        for category in sorted(category_to_files.keys()):
            count = len(category_to_files[category])
            f.write(f"{category:50s} : {count:5d} files\n")
    
    print(f"   ✓ Saved {summary_path.name}")
    print(f"\n✅ All results saved to: {output_path}")


def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("DRAGON'S CODEX - WIKI CATEGORY ANALYZER")
    print("=" * 80)
    
    # Note: We'll pass paths as arguments since we're not using config yet
    # This makes the script more flexible for testing
    
    import sys
    
    from src.utils.config import Config
    from src.utils.logger import get_logger

    wiki_dir = Config().WIKI_PATH
    output_dir = Config().METADATA_WIKI_PATH
    
    print(f"\n📂 Wiki directory: {wiki_dir}")
    print(f"📁 Output directory: {output_dir}")
    
    # Run analysis
    filename_to_categories, category_to_files = analyze_wiki_categories(wiki_dir)
    
    if not filename_to_categories:
        print("\n⚠️  No data to save. Exiting.")
        sys.exit(1)
    
    # Save results
    save_results(filename_to_categories, category_to_files, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review category_analysis_summary.txt")
    print("2. Examine category_to_files.json for patterns")
    print("3. Check filename_to_categories.json for specific files")
    print("\n")


if __name__ == "__main__":
    main()