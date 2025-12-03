"""
Dragon's Codex - Batch Wiki Processor
Processes all wiki files and organizes by page type.

Processes ~6,000 wiki files and saves to:
- wiki_chronology.json (5 files)
- wiki_character.json (~2,451 files)
- wiki_chapter_summary.json (714 files)
- wiki_concept.json (~2,867 files)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime

# Import our parser
from src.ingestion.wiki.pass_06_uses_this_markdown_wiki_parser import parse_wiki_file, classify_page_type


def load_category_mappings(category_file):
    """
    Load filename to categories mapping.
    
    Args:
        category_file: Path to filename_to_categories.json
        
    Returns:
        dict: {filename: [categories]}
    """
    print(f"\n📂 Loading category mappings from: {category_file}")
    
    with open(category_file, 'r', encoding='utf-8') as f:
        mappings = json.load(f)
    
    print(f"   ✓ Loaded mappings for {len(mappings)} files")
    return mappings


def group_files_by_type(wiki_dir, category_mappings):
    """
    Group wiki files by page type.
    
    Args:
        wiki_dir: Path to wiki directory
        category_mappings: Filename to categories mapping
        
    Returns:
        dict: {page_type: [filepaths]}
    """
    print(f"\n🔍 Scanning wiki directory: {wiki_dir}")
    
    wiki_path = Path(wiki_dir)
    txt_files = list(wiki_path.glob('*.txt'))
    
    print(f"   Found {len(txt_files)} .txt files")
    
    # Group by type
    files_by_type = defaultdict(list)
    
    print("\n📊 Classifying files by type...")
    for filepath in tqdm(txt_files, desc="Classifying", unit="file"):
        filename = filepath.name
        categories = category_mappings.get(filename, [])
        
        page_type = classify_page_type(filename, categories)
        files_by_type[page_type].append(filepath)
    
    # Print distribution
    print(f"\n📋 File Distribution:")
    print(f"   SKIP:            {len(files_by_type['SKIP']):5,} files (redirects, empty)")
    print(f"   CHRONOLOGY:      {len(files_by_type['CHRONOLOGY']):5,} files")
    print(f"   CHARACTER:       {len(files_by_type['CHARACTER']):5,} files")
    print(f"   CHAPTER_SUMMARY: {len(files_by_type['CHAPTER_SUMMARY']):5,} files")
    print(f"   CONCEPT:         {len(files_by_type['CONCEPT']):5,} files")
    
    parseable = (len(files_by_type['CHRONOLOGY']) + 
                 len(files_by_type['CHARACTER']) + 
                 len(files_by_type['CHAPTER_SUMMARY']) + 
                 len(files_by_type['CONCEPT']))
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
    
    print(f"\n{'='*80}")
    print(f"Processing {page_type} pages ({len(filepaths)} files)")
    print(f"{'='*80}")
    
    for filepath in tqdm(filepaths, desc=f"Parsing {page_type}", unit="file"):
        filename = filepath.name
        categories = category_mappings.get(filename, [])
        
        try:
            result = parse_wiki_file(filepath, categories)
            
            if result:
                parsed_pages[filename] = result
            else:
                # File was skipped by parser
                skipped.append({
                    'filename': filename,
                    'reason': 'Parser returned None',
                    'categories': categories
                })
        
        except Exception as e:
            # Parsing error
            errors.append({
                'filename': filename,
                'error': str(e),
                'type': 'parse_error'
            })
    
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


def save_results(page_type, parsed_pages, output_dir):
    """
    Save parsed pages to JSON file.
    
    Args:
        page_type: Type of pages
        parsed_pages: Dictionary of parsed page data
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename_map = {
        'CHRONOLOGY': 'wiki_chronology.json',
        'CHARACTER': 'wiki_character.json',
        'CHAPTER_SUMMARY': 'wiki_chapter_summary.json',
        'CONCEPT': 'wiki_concept.json'
    }
    
    output_file = output_path / filename_map[page_type]
    
    print(f"\n💾 Saving {len(parsed_pages)} pages to: {output_file.name}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_pages, f, indent=2, ensure_ascii=False)
    
    # Get file size
    file_size = output_file.stat().st_size
    size_mb = file_size / (1024 * 1024)
    
    print(f"   ✓ Saved {size_mb:.2f} MB")
    
    return output_file


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
    error_file = output_path / 'wiki_parsing_errors.log'
    
    print(f"\n📝 Saving error log to: {error_file.name}")
    
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("WIKI PARSING ERROR LOG\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total errors: {len(all_errors)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Group by page type
        errors_by_type = defaultdict(list)
        for error in all_errors:
            errors_by_type[error['page_type']].append(error)
        
        for page_type, errors in errors_by_type.items():
            f.write("="*80 + "\n")
            f.write(f"{page_type} ERRORS ({len(errors)} files)\n")
            f.write("="*80 + "\n\n")
            
            for error in errors:
                f.write(f"File: {error['filename']}\n")
                f.write(f"Type: {error['type']}\n")
                f.write(f"Error: {error['error']}\n")
                f.write("-"*80 + "\n")
    
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
    skip_file = output_path / 'wiki_skipped_files.log'
    
    print(f"\n📝 Saving skip log to: {skip_file.name}")
    
    # Get all SKIP files from classification
    skip_files = files_by_type.get('SKIP', [])
    
    with open(skip_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("WIKI SKIPPED FILES LOG\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Section 1: Files classified as SKIP (redirects, no categories)
        f.write("="*80 + "\n")
        f.write(f"FILES CLASSIFIED AS SKIP ({len(skip_files)} files)\n")
        f.write("="*80 + "\n\n")
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
        f.write("\n" + "="*80 + "\n")
        f.write(f"FILES SKIPPED DURING PARSING ({len(all_skipped)} files)\n")
        f.write("="*80 + "\n\n")
        f.write("These files were classified as parseable but returned None:\n\n")
        
        # Group by page type
        skipped_by_type = defaultdict(list)
        for skip in all_skipped:
            skipped_by_type[skip.get('page_type', 'UNKNOWN')].append(skip)
        
        for page_type, skipped in skipped_by_type.items():
            f.write(f"\n{page_type} ({len(skipped)} files):\n")
            f.write("-" * 80 + "\n")
            for skip in skipped:
                f.write(f"  File: {skip['filename']}\n")
                f.write(f"  Reason: {skip['reason']}\n")
                categories = skip.get('categories', [])
                if categories:
                    f.write(f"  Categories: {', '.join(categories[:5])}")
                    if len(categories) > 5:
                        f.write(f" (+ {len(categories)-5} more)")
                    f.write("\n")
                f.write("\n")
        
        # Summary statistics
        f.write("\n" + "="*80 + "\n")
        f.write("SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Files classified as SKIP:    {len(skip_files):5,}\n")
        f.write(f"Files skipped during parse:  {len(all_skipped):5,}\n")
        f.write(f"Total files not parsed:      {len(skip_files) + len(all_skipped):5,}\n")
    
    print(f"   ✓ Logged {len(skip_files) + len(all_skipped):,} skipped files")


def save_missing_concept_files(category_mappings, parsed_concept_files, output_dir):
    """
    Find and save a list of CONCEPT files that should exist but weren't parsed.
    
    Args:
        category_mappings: All file categories
        parsed_concept_files: List of successfully parsed concept filenames
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    missing_file = output_path / 'missing_concept_files.txt'
    
    print(f"\n🔍 Finding missing CONCEPT files...")
    
    # Determine which files SHOULD be CONCEPT
    expected_concept_files = []
    
    for filename, categories in category_mappings.items():
        if not categories:
            continue
        
        # Check classification logic (same as classify_page_type)
        is_chronology = 'Character_Chronologies' in categories
        is_character = 'Men' in categories or 'Women' in categories
        is_chapter_summary = any('chapter_summaries' in cat.lower() for cat in categories)
        is_redirect = any('redirect' in cat.lower() or 'disambiguation' in cat.lower() 
                         for cat in categories)
        
        # If none of the above, should be CONCEPT
        if not (is_chronology or is_character or is_chapter_summary or is_redirect):
            expected_concept_files.append(filename)
    
    # Find missing files
    parsed_set = set(parsed_concept_files)
    missing_files = [f for f in expected_concept_files if f not in parsed_set]
    
    print(f"   Expected CONCEPT files: {len(expected_concept_files):,}")
    print(f"   Successfully parsed:    {len(parsed_concept_files):,}")
    print(f"   Missing:                {len(missing_files):,}")
    
    # Save to file
    with open(missing_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("MISSING CONCEPT FILES\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"These files were classified as CONCEPT but were not parsed:\n\n")
        f.write(f"Total missing: {len(missing_files)}\n\n")
        f.write("="*80 + "\n")
        f.write("FILENAME LIST (for manual checking)\n")
        f.write("="*80 + "\n\n")
        
        for i, filename in enumerate(sorted(missing_files), 1):
            f.write(f"{i:4d}. {filename}\n")
            
            # Add categories for context
            cats = category_mappings.get(filename, [])
            if cats and i <= 50:  # Show categories for first 50
                f.write(f"       Categories: {', '.join(cats[:3])}")
                if len(cats) > 3:
                    f.write(f" (+ {len(cats)-3} more)")
                f.write("\n")
    
    print(f"   ✓ Saved {len(missing_files)} missing filenames to: {missing_file.name}")
    
    return missing_files


def generate_statistics(all_parsed_data, output_dir):
    """
    Generate comprehensive statistics report.
    
    Args:
        all_parsed_data: Dict of {page_type: parsed_pages}
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    stats_file = output_path / 'wiki_parsing_stats.txt'
    
    print(f"\n📊 Generating statistics report: {stats_file.name}")
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("WIKI PARSING STATISTICS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall summary
        total_pages = sum(len(pages) for pages in all_parsed_data.values())
        f.write(f"Total pages parsed: {total_pages:,}\n\n")
        
        # By page type
        f.write("="*80 + "\n")
        f.write("PAGES BY TYPE\n")
        f.write("="*80 + "\n\n")
        
        for page_type, pages in all_parsed_data.items():
            f.write(f"{page_type:20s}: {len(pages):5,} pages\n")
        
        # Detailed statistics per type
        for page_type, pages in all_parsed_data.items():
            f.write("\n" + "="*80 + "\n")
            f.write(f"{page_type} DETAILED STATISTICS\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Total pages: {len(pages):,}\n\n")
            
            # Temporal sections statistics
            temporal_counts = []
            non_temporal_counts = []
            
            for filename, page_data in pages.items():
                temporal = len(page_data.get('temporal_sections', []))
                non_temporal = len(page_data.get('non_temporal_sections', []))
                
                temporal_counts.append(temporal)
                non_temporal_counts.append(non_temporal)
            
            if temporal_counts:
                avg_temporal = sum(temporal_counts) / len(temporal_counts)
                f.write(f"Average temporal sections per page: {avg_temporal:.1f}\n")
                f.write(f"Pages with temporal sections: {sum(1 for c in temporal_counts if c > 0):,}\n")
            
            if non_temporal_counts:
                avg_non_temporal = sum(non_temporal_counts) / len(non_temporal_counts)
                f.write(f"Average non-temporal sections per page: {avg_non_temporal:.1f}\n")
            
            # Book coverage (for temporal sections)
            if page_type in ['CHRONOLOGY', 'CHARACTER']:
                book_coverage = defaultdict(int)
                
                for page_data in pages.values():
                    for section in page_data.get('temporal_sections', []):
                        book_num = section.get('book_number')
                        if book_num is not None:
                            book_coverage[book_num] += 1
                
                if book_coverage:
                    f.write(f"\nBook coverage (temporal sections):\n")
                    for book_num in sorted(book_coverage.keys()):
                        count = book_coverage[book_num]
                        f.write(f"  Book {book_num:2d}: {count:4,} sections\n")
            
            # Sample filenames
            f.write(f"\nSample files (first 10):\n")
            for i, filename in enumerate(list(pages.keys())[:10], 1):
                f.write(f"  {i:2d}. {filename}\n")
        
        # Content statistics
        f.write("\n" + "="*80 + "\n")
        f.write("CONTENT STATISTICS\n")
        f.write("="*80 + "\n\n")
        
        total_sections = 0
        total_content_length = 0
        
        for pages in all_parsed_data.values():
            for page_data in pages.values():
                # Count temporal sections
                for section in page_data.get('temporal_sections', []):
                    total_sections += 1
                    content = section.get('content', '')
                    total_content_length += len(content)
                
                # Count non-temporal sections
                for section in page_data.get('non_temporal_sections', []):
                    total_sections += 1
                    content = section.get('content', '')
                    total_content_length += len(content)
                
                # Count sections in concept pages
                for section in page_data.get('sections', []):
                    total_sections += 1
                    content = section.get('content', '')
                    total_content_length += len(content)
        
        f.write(f"Total sections across all pages: {total_sections:,}\n")
        f.write(f"Total content length: {total_content_length:,} characters\n")
        if total_sections > 0:
            avg_content = total_content_length / total_sections
            f.write(f"Average content per section: {avg_content:.0f} characters\n")
    
    print(f"   ✓ Statistics report generated")


def validate_parsed_data(all_parsed_data):
    """
    Validate parsed data quality.
    
    Args:
        all_parsed_data: Dict of {page_type: parsed_pages}
        
    Returns:
        dict: Validation results
    """
    print(f"\n🔍 Validating parsed data quality...")
    
    validation = {
        'total_pages': 0,
        'pages_with_temporal': 0,
        'pages_with_content': 0,
        'empty_content_sections': 0,
        'invalid_book_numbers': 0,
        'valid': True
    }
    
    valid_book_numbers = set(range(0, 15))  # 0-14 for books
    
    for page_type, pages in all_parsed_data.items():
        validation['total_pages'] += len(pages)
        
        for filename, page_data in pages.items():
            # Check temporal sections
            temporal_sections = page_data.get('temporal_sections', [])
            if temporal_sections:
                validation['pages_with_temporal'] += 1
                
                # Validate book numbers
                for section in temporal_sections:
                    book_num = section.get('book_number')
                    if book_num is not None and book_num not in valid_book_numbers:
                        validation['invalid_book_numbers'] += 1
                        validation['valid'] = False
                    
                    # Check for empty content
                    content = section.get('content', '').strip()
                    if not content:
                        validation['empty_content_sections'] += 1
            
            # Check non-temporal sections
            non_temporal = page_data.get('non_temporal_sections', [])
            for section in non_temporal:
                content = section.get('content', '').strip()
                if content:
                    validation['pages_with_content'] += 1
                    break  # Count once per page
            
            # Check concept sections
            sections = page_data.get('sections', [])
            for section in sections:
                content = section.get('content', '').strip()
                if content:
                    validation['pages_with_content'] += 1
                    break  # Count once per page
    
    # Print validation results
    print(f"\n   Total pages validated: {validation['total_pages']:,}")
    print(f"   Pages with temporal sections: {validation['pages_with_temporal']:,}")
    print(f"   Pages with content: {validation['pages_with_content']:,}")
    
    if validation['empty_content_sections'] > 0:
        print(f"   ⚠️  Empty content sections: {validation['empty_content_sections']:,}")
    
    if validation['invalid_book_numbers'] > 0:
        print(f"   ⚠️  Invalid book numbers: {validation['invalid_book_numbers']:,}")
        validation['valid'] = False
    
    if validation['valid']:
        print(f"\n   ✅ Validation PASSED")
    else:
        print(f"\n   ⚠️  Validation FAILED - review warnings above")
    
    return validation


def main():
    """Main batch processing function."""
    print("\n" + "="*80)
    print("DRAGON'S CODEX - BATCH WIKI PROCESSOR")
    print("="*80)
    
    from src.utils.config import Config
    from src.utils.logger import get_logger
    
    wiki_dir = Config().WIKI_PATH
    categories_file = Config().FILE_FILENAME_TO_CATEGORIES
    output_dir = Config().PROCESSED_WIKI_PATH

    print(f"\n📂 Configuration:")
    print(f"   Wiki directory:     {wiki_dir}")
    print(f"   Categories file:    {categories_file}")
    print(f"   Output directory:   {output_dir}")
    
    start_time = datetime.now()
    
    # Step 1: Load category mappings
    category_mappings = load_category_mappings(categories_file)
    
    # Step 2: Group files by type
    files_by_type = group_files_by_type(wiki_dir, category_mappings)
    
    # Step 3: Process each page type
    all_parsed_data = {}
    all_errors = []
    all_skipped = []
    
    page_types_to_process = ['CHRONOLOGY', 'CHARACTER', 'CHAPTER_SUMMARY', 'CONCEPT']
    
    for page_type in page_types_to_process:
        if page_type not in files_by_type or not files_by_type[page_type]:
            print(f"\n⏭️  Skipping {page_type} (no files)")
            continue
        
        parsed_pages, errors, skipped = process_page_type(
            page_type, 
            files_by_type[page_type], 
            category_mappings
        )
        
        if parsed_pages:
            all_parsed_data[page_type] = parsed_pages
            save_results(page_type, parsed_pages, output_dir)
        
        # Track errors with page type
        for error in errors:
            error['page_type'] = page_type
        all_errors.extend(errors)
        
        # Track skipped files with page type
        for skip in skipped:
            skip['page_type'] = page_type
        all_skipped.extend(skipped)
    
    # Step 4: Save error log
    if all_errors:
        save_error_log(all_errors, output_dir)
    
    # Step 5: Save skip log
    save_skip_log(files_by_type, all_skipped, output_dir)
    
    # Step 5b: Find and save missing CONCEPT files
    parsed_concept_files = list(all_parsed_data.get('CONCEPT', {}).keys())
    missing_concept_files = save_missing_concept_files(
        category_mappings, 
        parsed_concept_files, 
        output_dir
    )
    
    # Step 6: Generate statistics
    generate_statistics(all_parsed_data, output_dir)
    
    # Step 7: Validate data
    validation = validate_parsed_data(all_parsed_data)
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*80)
    print("PROCESSING COMPLETE!")
    print("="*80)
    print(f"\n⏱️  Total time: {duration}")
    print(f"📊 Total pages parsed: {validation['total_pages']:,}")
    print(f"⚠️  Total errors: {len(all_errors):,}")
    
    print(f"\n📁 Output files in: {output_dir}")
    print(f"   • wiki_chronology.json")
    print(f"   • wiki_character.json")
    print(f"   • wiki_chapter_summary.json")
    print(f"   • wiki_concept.json")
    print(f"   • wiki_parsing_stats.txt")
    print(f"   • wiki_skipped_files.log")
    if missing_concept_files:
        print(f"   • missing_concept_files.txt ({len(missing_concept_files)} files)")
    if all_errors:
        print(f"   • wiki_parsing_errors.log")
    
    print("\n✅ Week 3 Goal 2: COMPLETE!\n")


if __name__ == "__main__":
    main()
