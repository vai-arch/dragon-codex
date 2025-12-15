"""
Dragon's Codex - Batch Wiki Processor
Processes all wiki files and organizes by page type.

Processes ~6,000 wiki files and saves to:
- wiki_chronology.json (5 files)
- wiki_character.json (~2,451 files)
- wiki_chapter_summary.json (714 files)
- wiki_concept.json (~2,867 files)

Input:  - filename_to_categories.json
        - all .txt wiki files in WIKI_PATH
"""

import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from src.utils.logger import set_global_log_level
from src.utils.paths import get_paths
from src.utils.util_files_functions import (
    find_files_in_folder,
    load_json_from_file,
    save_json_to_file,
)

# Import our parser
from src.utils.util_markdown_wiki_parser import classify_page_type, parse_wiki_file
from src.utils.util_statistics import total_statistics_logging

in_wiki_path = None
in_file_filename_to_categories = None
in_file_redirect_aliases_mapping = None

out_processed_wiki_path = None
out_file_wiki_chronology = None
out_file_wiki_character = None
out_file_wiki_chapter_summary = None
out_file_wiki_prophecies = None
out_file_wiki_magic = None
out_file_wiki_concept = None

out_filename_map = None


def group_files_by_type(wiki_path, filename_to_categories_file):
    """
    Group wiki files by page type.

    Args:
        wiki_dir: Path to wiki directory
        category_mappings: Filename to categories mapping

    Returns:
        dict: {page_type: [filepaths]}
    """

    txt_files = find_files_in_folder(wiki_path, extension=".txt")

    # Group by type
    files_by_type = defaultdict(list)

    print("\n📊 Classifying files by type...")
    for filepath in tqdm(txt_files, desc="Classifying", unit="file"):
        filename = filepath.name
        categories = filename_to_categories_file.get(filename, [])

        page_type = classify_page_type(filename, categories)
        files_by_type[page_type].append(filepath)

    # Print distribution
    print("\n📋 File Distribution:")
    print(f"   SKIP:            {len(files_by_type['SKIP']):5,} files (redirects, empty)")
    print(f"   CHRONOLOGY:      {len(files_by_type['CHRONOLOGY']):5,} files")
    print(f"   CHARACTER:       {len(files_by_type['CHARACTER']):5,} files")
    print(f"   CHAPTER_SUMMARY: {len(files_by_type['CHAPTER_SUMMARY']):5,} files")
    print(f"   PROPHECIES:      {len(files_by_type['PROPHECIES']):5,} files")
    print(f"   MAGIC:           {len(files_by_type['MAGIC']):5,} files")
    print(f"   CONCEPT:         {len(files_by_type['CONCEPT']):5,} files")

    parseable = (
        len(files_by_type["CHRONOLOGY"])
        + len(files_by_type["CHARACTER"])
        + len(files_by_type["CHAPTER_SUMMARY"])
        + len(files_by_type["PROPHECIES"])
        + len(files_by_type["MAGIC"])
        + len(files_by_type["CONCEPT"])
    )
    print(f"\n   Total parseable: {parseable:5,} files")
    print(f"   Total skipped:   {len(files_by_type['SKIP']):5,} files")

    return files_by_type


def process_page_type(page_type, filepaths, category_mappings):
    """
    Process all files of a specific page type.

    Args:
        page_type: Type of pages to process
        filepaths: List of file paths
        category_mappings: Category mappings for lookup

    Returns:
        tuple: (parsed_pages, errors, skipped)
    """
    parsed_pages = {}
    errors = []
    skipped = []

    redirect_aliases = load_json_from_file(in_file_redirect_aliases_mapping)

    print(f"\n{'=' * 80}")
    print(f"Processing {page_type} pages ({len(filepaths)} files)")
    print(f"{'=' * 80}")

    for filepath in tqdm(filepaths, desc=f"Parsing {page_type}", unit="file"):
        filename = filepath.name
        categories = category_mappings.get(filename, [])

        try:
            result = parse_wiki_file(filepath, categories)

            result["aliases"] = redirect_aliases.get(result["page_name"], [])  # Placeholder for actual alias extraction logic

            if result:
                parsed_pages[filename] = result
            else:
                # File was skipped by parser
                skipped.append({"filename": filename, "reason": "Parser returned None", "categories": categories})

        except Exception as e:
            # Parsing error
            errors.append({"filename": filename, "error": str(e), "type": "parse_error"})

    success_count = len(parsed_pages)
    error_count = len(errors)
    skip_count = len(skipped)
    success_rate = (success_count / len(filepaths) * 100) if filepaths else 0

    print(f"\n✅ Successfully parsed: {success_count:,} files ({success_rate:.1f}%)")
    if error_count > 0:
        print(f"⚠️  Errors encountered: {error_count:,} files")
    if skip_count > 0:
        print(f"⏭️  Skipped: {skip_count:,} files")

    return parsed_pages, errors, skipped


def save_error_log(all_errors, output_dir):
    """
    Save error log to file.

    Args:
        all_errors: List of all errors from processing
        output_dir: Output directory path
    """
    if not all_errors:
        return

    output_path = Path(output_dir)
    error_file = output_path / "wiki_parsing_errors.log"

    print(f"\n📝 Saving error log to: {error_file.name}")

    with open(error_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("WIKI PARSING ERROR LOG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total errors: {len(all_errors)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Group by page type
        errors_by_type = defaultdict(list)
        for error in all_errors:
            errors_by_type[error["page_type"]].append(error)

        for page_type, errors in errors_by_type.items():
            f.write("=" * 80 + "\n")
            f.write(f"{page_type} ERRORS ({len(errors)} files)\n")
            f.write("=" * 80 + "\n\n")

            for error in errors:
                f.write(f"File: {error['filename']}\n")
                f.write(f"Type: {error['type']}\n")
                f.write(f"Error: {error['error']}\n")
                f.write("-" * 80 + "\n")

    print(f"   ✓ Logged {len(all_errors)} errors")


def save_skip_log(files_by_type, all_skipped, output_dir):
    """
    Save detailed skip log showing all files that were not parsed and why.

    Args:
        files_by_type: Dict of files grouped by type from classification
        all_skipped: List of files skipped during parsing
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    skip_file = output_path / "wiki_skipped_files.log"

    print(f"\n📝 Saving skip log to: {skip_file.name}")

    # Get all SKIP files from classification
    skip_files = files_by_type.get("SKIP", [])

    with open(skip_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("WIKI SKIPPED FILES LOG\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Section 1: Files classified as SKIP (redirects, no categories)
        f.write("=" * 80 + "\n")
        f.write(f"FILES CLASSIFIED AS SKIP ({len(skip_files)} files)\n")
        f.write("=" * 80 + "\n\n")
        f.write("These files were skipped during classification:\n")
        f.write("- Redirects (various types)\n")
        f.write("- Files with no categories\n")
        f.write("- Disambiguation pages\n\n")

        f.write("First 50 skipped files:\n")
        for i, filepath in enumerate(skip_files[:50], 1):
            f.write(f"  {i:3d}. {filepath.name}\n")

        if len(skip_files) > 50:
            f.write(f"\n  ... and {len(skip_files) - 50} more files\n")

        # Section 2: Files that returned None during parsing
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"FILES SKIPPED DURING PARSING ({len(all_skipped)} files)\n")
        f.write("=" * 80 + "\n\n")
        f.write("These files were classified as parseable but returned None:\n\n")

        # Group by page type
        skipped_by_type = defaultdict(list)
        for skip in all_skipped:
            skipped_by_type[skip.get("page_type", "UNKNOWN")].append(skip)

        for page_type, skipped in skipped_by_type.items():
            f.write(f"\n{page_type} ({len(skipped)} files):\n")
            f.write("-" * 80 + "\n")
            for skip in skipped:
                f.write(f"  File: {skip['filename']}\n")
                f.write(f"  Reason: {skip['reason']}\n")
                categories = skip.get("categories", [])
                if categories:
                    f.write(f"  Categories: {', '.join(categories[:5])}")
                    if len(categories) > 5:
                        f.write(f" (+ {len(categories) - 5} more)")
                    f.write("\n")
                f.write("\n")

        # Summary statistics
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Files classified as SKIP:    {len(skip_files):5,}\n")
        f.write(f"Files skipped during parse:  {len(all_skipped):5,}\n")
        f.write(f"Total files not parsed:      {len(skip_files) + len(all_skipped):5,}\n")

    print(f"   ✓ Logged {len(skip_files) + len(all_skipped):,} skipped files")


def validate_parsed_data(all_parsed_data):
    """
    Validate parsed data quality.

    Args:
        all_parsed_data: Dict of {page_type: parsed_pages}

    Returns:
        dict: Validation results
    """
    print("\n🔍 Validating parsed data quality...")

    validation = {
        "total_pages": 0,
        "pages_with_temporal": 0,
        "pages_with_content": 0,
        "empty_content_sections": 0,
        "invalid_book_numbers": 0,
        "valid": True,
    }

    valid_book_numbers = set(range(0, 15))  # 0-14 for books

    for page_type, pages in all_parsed_data.items():
        validation["total_pages"] += len(pages)

        for filename, page_data in pages.items():
            # Check temporal sections
            temporal_sections = page_data.get("temporal_sections", [])
            if temporal_sections:
                validation["pages_with_temporal"] += 1

                # Validate book numbers
                for section in temporal_sections:
                    book_num = section.get("book_number")
                    if book_num is not None and book_num not in valid_book_numbers:
                        validation["invalid_book_numbers"] += 1
                        validation["valid"] = False

                    # Check for empty content
                    content = section.get("content", "").strip()
                    if not content:
                        validation["empty_content_sections"] += 1

            # Check non-temporal sections
            non_temporal = page_data.get("non_temporal_sections", [])
            for section in non_temporal:
                content = section.get("content", "").strip()
                if content:
                    validation["pages_with_content"] += 1
                    break  # Count once per page

            # Check concept sections
            sections = page_data.get("sections", [])
            for section in sections:
                content = section.get("content", "").strip()
                if content:
                    validation["pages_with_content"] += 1
                    break  # Count once per page

    # Print validation results
    print(f"\n   Total pages validated: {validation['total_pages']:,}")
    print(f"   Pages with temporal sections: {validation['pages_with_temporal']:,}")
    print(f"   Pages with content: {validation['pages_with_content']:,}")

    if validation["empty_content_sections"] > 0:
        print(f"   ⚠️  Empty content sections: {validation['empty_content_sections']:,}")

    if validation["invalid_book_numbers"] > 0:
        print(f"   ⚠️  Invalid book numbers: {validation['invalid_book_numbers']:,}")
        validation["valid"] = False

    if validation["valid"]:
        print("\n   ✅ Validation PASSED")
    else:
        print("\n   ⚠️  Validation FAILED - review warnings above")

    return validation


def generate_statistics(all_parsed_data, output_dir):
    pages_by_type = {}
    per_type_stats = {}

    # ---------- Per-type statistics ----------
    for page_type, pages in all_parsed_data.items():
        pages_by_type[page_type] = len(pages)

        temporal_counts = []
        non_temporal_counts = []

        for page_data in pages.values():
            temporal_counts.append(len(page_data.get("temporal_sections", [])))
            non_temporal_counts.append(len(page_data.get("non_temporal_sections", [])))

        type_stats = {}

        if temporal_counts:
            type_stats["avg_temporal_sections"] = sum(temporal_counts) / len(temporal_counts)
            type_stats["pages_with_temporal_sections"] = sum(1 for c in temporal_counts if c > 0)

        if non_temporal_counts:
            type_stats["avg_non_temporal_sections"] = sum(non_temporal_counts) / len(non_temporal_counts)

        # Book coverage (only numeric)
        if page_type in ["CHRONOLOGY", "CHARACTER"]:
            book_coverage = defaultdict(int)

            for page_data in pages.values():
                for section in page_data.get("temporal_sections", []):
                    book_num = section.get("book_number")
                    if book_num is not None:
                        book_coverage[book_num] += 1

            if book_coverage:
                type_stats["book_coverage"] = dict(book_coverage)

        per_type_stats[page_type] = type_stats

    # ---------- Global content statistics ----------
    total_sections = 0
    total_content_length = 0

    for pages in all_parsed_data.values():
        for page_data in pages.values():
            for section in page_data.get("temporal_sections", []):
                total_sections += 1
                total_content_length += len(section.get("content", ""))

            for section in page_data.get("non_temporal_sections", []):
                total_sections += 1
                total_content_length += len(section.get("content", ""))

            for section in page_data.get("sections", []):
                total_sections += 1
                total_content_length += len(section.get("content", ""))

    content_stats = {
        "total_sections": total_sections,
        "total_content_length": total_content_length,
    }

    if total_sections > 0:
        content_stats["avg_content_per_section"] = total_content_length / total_sections

    # ---------- Final statistics object ----------
    statistics = {
        "name": "wiki_organization",
        "metrics": {
            "total_pages": sum(pages_by_type.values()),
            "pages_by_type": pages_by_type,
            "per_type_statistics": per_type_stats,
            "content_statistics": content_stats,
        },
    }

    return statistics


def main():
    start_time = datetime.now()

    set_global_log_level("WARNING")  # Reduce logging verbosity for batch processing

    # Step 1: Load category mappings
    category_mappings = load_json_from_file(in_file_filename_to_categories)

    # Step 2: Group files by type
    files_by_type = group_files_by_type(in_wiki_path, category_mappings)

    # Step 3: Process each page type
    all_parsed_data = {}
    all_errors = []
    all_skipped = []

    page_types_to_process = ["CHRONOLOGY", "CHARACTER", "CHAPTER_SUMMARY", "PROPHECIES", "MAGIC", "CONCEPT"]

    for page_type in page_types_to_process:
        if page_type not in files_by_type or not files_by_type[page_type]:
            print(f"\n⏭️  Skipping {page_type} (no files)")
            continue

        parsed_pages, errors, skipped = process_page_type(page_type, files_by_type[page_type], category_mappings)

        if parsed_pages:
            all_parsed_data[page_type] = parsed_pages
            output_file = out_filename_map[page_type]
            save_json_to_file(parsed_pages, output_file, indent=2)

        # Track errors with page type
        for error in errors:
            error["page_type"] = page_type
        all_errors.extend(errors)

        # Track skipped files with page type
        for skip in skipped:
            skip["page_type"] = page_type
        all_skipped.extend(skipped)

    # Step 4: Save error log
    if all_errors:
        save_error_log(all_errors, out_processed_wiki_path)

    # Step 5: Save skip log
    save_skip_log(files_by_type, all_skipped, out_processed_wiki_path)

    # Step 6: Generate statistics
    statistics = generate_statistics(all_parsed_data, out_processed_wiki_path)

    # Step 7: Validate data
    validation = validate_parsed_data(all_parsed_data)

    statistics["metrics"]["validation"] = validation

    # Final summary
    end_time = datetime.now()
    total_time = end_time - start_time

    total_statistics_logging(total_time=total_time, log_name="prc_05_organize_wiki_by_type", statistics=statistics, title="WIKI ORGANIZATION", tables=False)


if __name__ == "__main__":
    paths = get_paths()

    in_wiki_path = paths.WIKI_PATH
    in_file_filename_to_categories = paths.FILE_FILENAME_TO_CATEGORIES
    in_file_redirect_aliases_mapping = paths.FILE_REDIRECT_ALIASES_MAPPING

    out_processed_wiki_path = paths.PROCESSED_WIKI_PATH

    out_file_wiki_chronology = paths.FILE_WIKI_CHRONOLOGY
    out_file_wiki_character = paths.FILE_WIKI_CHARACTER
    out_file_wiki_chapter_summary = paths.FILE_WIKI_CHAPTER_SUMMARY
    out_file_wiki_prophecies = paths.FILE_WIKI_PROPHECIES
    out_file_wiki_magic = paths.FILE_WIKI_MAGIC
    out_file_wiki_concept = paths.FILE_WIKI_CONCEPT

    out_filename_map = {
        "CHRONOLOGY": out_file_wiki_chronology,
        "CHARACTER": out_file_wiki_character,
        "CHAPTER_SUMMARY": out_file_wiki_chapter_summary,
        "PROPHECIES": out_file_wiki_prophecies,
        "MAGIC": out_file_wiki_magic,
        "CONCEPT": out_file_wiki_concept,
    }

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
