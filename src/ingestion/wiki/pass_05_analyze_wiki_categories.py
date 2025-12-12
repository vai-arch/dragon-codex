"""
Dragon's Codex - Wiki Category Analyzer
Extracts categories from all wiki files and creates mappings.

This script:
1. Scans all wiki .txt files
2. Extracts categories from <!-- Categories: ... --> metadata
3. Creates filename → categories mapping
4. Creates category → files mapping
5. Generates analysis summary

Input: data/raw/wiki/*.txt
Output:
    - data/metadata/wiki/filename_to_categories.json
    - data/metadata/wiki/category_to_files.json 
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from src.utils.config import Config
from tqdm import tqdm

import sys

from src.utils.config import Config
from src.utils.logger import get_logger, set_global_log_level
from src.utils.util_files_functions import load_json_from_file, save_json_to_file, find_files_in_folder
from src.utils.wiki_constants import CATEGORY_OVERRIDES, extract_categories, check_fist_level_key_in_json, extract_page_name

wiki_path = Config().WIKI_PATH
output_dir = Config().METADATA_WIKI_PATH
filename_to_categories_path = Config().FILE_FILENAME_TO_CATEGORIES
category_to_files_path = Config().FILE_CATEGORY_TO_FILES
summary_path = Config().FILE_CATEGORY_ANALYSIS_SUMMARY
redirect_mapping_path = Config().FILE_REDIRECT_MAPPING


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
    
    txt_files = find_files_in_folder(wiki_path, ".txt", recursive=False )
    
    set_global_log_level('WARNING')
    
    # Initialize mappings
    filename_to_categories = {}
    category_to_files = defaultdict(list)
    
    # Track statistics
    files_with_categories = 0
    files_without_categories = 0
    files_with_unknown_redirection = 0
    
    # Process each file with progress bar
    print("\n📊 Extracting categories from wiki files...")
    for filepath in tqdm(txt_files, desc="Processing", unit="file"):
        filename = filepath.name
        categories = extract_categories(filepath, None)
        
        # Store filename → categories mapping
        filename_to_categories[filename] = categories
        
        # Build category → files mapping
        if categories:
            files_with_categories += 1
            for category in categories:
                category_to_files[category].append(filename)
        else:
            page_name = extract_page_name(filepath)
            isRedirected = check_fist_level_key_in_json(redirect_mapping_path, page_name)
            if(isRedirected):
                files_with_unknown_redirection += 1
                category_to_files["unknown_redirection"].append(filename)
            else:
                files_without_categories += 1
                category_to_files["unknown_category"].append(filename)
    
    print(f"\n✅ Analysis complete!")
    print(f"   Files with categories: {files_with_categories}")
    print(f"   Files with unknown redirections: {files_with_unknown_redirection}")
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

    save_json_to_file(filename_to_categories, filename_to_categories_path, indent=2)

    # Save category → files mapping (with counts)
    category_counts = {
        category: {
            'count': len(files),
            'files': sorted(files)  # Sort for easier reading
        }
        for category, files in category_to_files.items()
    }
    
    save_json_to_file(category_counts, category_to_files_path, indent=2)  

def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("DRAGON'S CODEX - WIKI CATEGORY ANALYZER")
    print("=" * 80)
    
    # Run analysis
    filename_to_categories, category_to_files = analyze_wiki_categories(wiki_path)
    
    if not filename_to_categories:
        raise ValueError("\n⚠️  No data to save. Exiting.")
    
    # Save results
    save_results(filename_to_categories, category_to_files, output_dir)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Examine category_to_files.json for patterns")
    print("2. Check filename_to_categories.json for specific files")
    print("\n")


if __name__ == "__main__":
    main()