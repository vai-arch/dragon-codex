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

import sys
import traceback
from collections import defaultdict
from datetime import datetime

from tqdm import tqdm

from src.utils.paths import get_paths
from src.utils.util_files_functions import find_files_in_folder, save_json_to_file
from src.utils.util_statistics import total_statistics_logging
from src.utils.wiki_constants import (
    check_fist_level_key_in_json,
    extract_categories,
    extract_page_name,
)

in_wiki_path = None
in_file_redirect_mapping = None
out_metadata_wiki_path = None
out_file_filename_to_categories = None
out_file_category_to_files = None


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

    txt_files = find_files_in_folder(in_wiki_path, ".txt", recursive=False)

    # set_global_log_level("WARNING")

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
            isRedirected = check_fist_level_key_in_json(in_file_redirect_mapping, page_name)
            if isRedirected:
                files_with_unknown_redirection += 1
                category_to_files["unknown_redirection"].append(filename)
            else:
                files_without_categories += 1
                category_to_files["unknown_category"].append(filename)

    statistics = {
        "name": "category_analysis",
        "metrics": {
            "files_with_categories": files_with_categories,
            "files_without_categories": files_without_categories,
            "files_with_unknown_redirection": files_with_unknown_redirection,
            "total_unique_categories": len(category_to_files),
        },
    }

    return filename_to_categories, dict(category_to_files), statistics


def main():
    start_time = datetime.now()

    filename_to_categories, category_to_files, statistics = analyze_wiki_categories(in_wiki_path)

    if not filename_to_categories:
        raise ValueError("\n⚠️  No data to save. Exiting.")

    # Save results
    save_json_to_file(filename_to_categories, out_file_filename_to_categories, indent=2)

    # Save category → files mapping (with counts)
    category_counts = {
        category: {
            "count": len(files),
            "files": sorted(files),  # Sort for easier reading
        }
        for category, files in category_to_files.items()
    }

    save_json_to_file(category_counts, out_file_category_to_files, indent=2)

    total_time = datetime.now() - start_time

    total_statistics_logging(total_time=total_time, log_name="prc_04_analyze_wiki_categories", statistics=statistics, title="CATEGORY ANALYSIS")


if __name__ == "__main__":
    paths = get_paths()

    in_wiki_path = paths.WIKI_PATH
    in_file_redirect_mapping = paths.FILE_REDIRECT_MAPPING
    out_metadata_wiki_path = paths.METADATA_WIKI_PATH
    out_file_filename_to_categories = paths.FILE_FILENAME_TO_CATEGORIES
    out_file_category_to_files = paths.FILE_CATEGORY_TO_FILES

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
