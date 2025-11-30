"""
Complete Book Processing Pipeline
Parses raw TXT books to JSON, then creates structured output with metadata

This replaces parse_all_books.py - handles everything in one script:
1. Parse raw TXT files to JSON (saves to data/raw/books/)
2. Load JSON and add metadata
3. Save structured output to data/processed/

Usage:
    python src\ingestion\save_parsed_books.py
    python src\ingestion\save_parsed_books.py --skip-txt-parsing  # Only process existing JSON

# Should see:
# STEP 1: Parsing raw TXT books to JSON
# STEP 2: Processing JSON to structured output
# FINAL SUMMARY
```

## 📊 What Gets Created
```
data/
├── raw/
│   └── books/
│       ├── 00-New_Spring.json          # ← Created from TXT
│       ├── 01-The_Eye_of_the_World.json
│       └── ...
├── processed/
│   ├── book_00_parsed.json             # ← With metadata
│   ├── book_01_parsed.json
│   ├── ...
│   ├── books_all_parsed.json           # ← All books combined
│   └── all_chapters.json               # ← All chapters flat
└── metadata/
    └── unified_glossary.json           # ← Unique terms
"""

import json
import re
import glob
import argparse
from pathlib import Path
from src.ingestion.books.book_parser import BookParser
from src.utils.config import Config
from src.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def parse_txt_to_json(books_path: Path) -> int:
    """
    Parse all raw TXT book files to JSON format
    
    This is the functionality from parse_all_books.py
    
    Args:
        books_path: Path to books directory
    
    Returns:
        Number of books processed
    """
    logger.info("="*70)
    logger.info("STEP 1: Parsing raw TXT books to JSON")
    logger.info("="*70)
    
    filenames = sorted(glob.glob(str(books_path / '*.txt')))
    
    if not filenames:
        logger.warning(f"No TXT files found in {books_path}")
        return 0
    
    logger.info(f"Found {len(filenames)} TXT files")
    
    books_processed = 0
    
    for filename in filenames:
        # Get basename to handle paths
        filename_base = Path(filename).name

        # Parse book number and name from filename
        book_parts = filename_base.split('-', 1)
        book_number = book_parts[0].strip()
        if len(book_parts) > 1:
            book_name = book_parts[1].rstrip('.txt').strip()
        else:
            book_name = ''

        logger.info(f"Processing: {filename_base}")

        # Read the file
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Initialize structures
        data = {
            "book_number": book_number,
            "book_name": book_name,
            "chapters": [],
            "glossary": []
        }

        current_section = None
        current_chapter = None
        chapter_content = []
        glossary_lines = []
        max_chapter_num = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip().rstrip("\\")

            if stripped == "PROLOGUE":
                current_section = "chapter"
                chapter_num = 0
                current_chapter = {"number": chapter_num, "type":"prologue", "title": "", "content": ""}
                i += 1
                # Skip blank lines to title
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    current_chapter["title"] = lines[i].strip().strip('*').strip()
                i += 1
                # Skip blank lines to content
                while i < len(lines) and not lines[i].strip():
                    i += 1
                continue

            elif stripped == "CHAPTER":
                if current_section == "chapter" and current_chapter:
                    current_chapter["content"] = ''.join(chapter_content).strip()
                    data["chapters"].append(current_chapter)
                    chapter_content = []

                i += 1
                # Skip blank lines to number
                while i < len(lines) and not lines[i].strip():
                    i += 1
                chapter_num = 0
                if i < len(lines):
                    try:
                        chapter_num = int(lines[i].strip())
                        max_chapter_num = max(max_chapter_num, chapter_num)
                    except ValueError:
                        pass
                current_chapter = {"number": chapter_num, "type":"chapter", "title": "", "content": ""}
                i += 1
                # Skip blank lines to title
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    current_chapter["title"] = lines[i].strip().strip('*').strip()
                i += 1
                # Skip blank lines to content
                while i < len(lines) and not lines[i].strip():
                    i += 1
                current_section = "chapter"
                continue

            elif stripped == "EPILOGUE":
                if current_section == "chapter" and current_chapter:
                    current_chapter["content"] = ''.join(chapter_content).strip()
                    data["chapters"].append(current_chapter)
                    chapter_content = []

                chapter_num = max_chapter_num + 1
                current_chapter = {"number": chapter_num, "type":"epilogue", "title": "", "content": ""}
                i += 1
                # Skip blank lines to title
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    current_chapter["title"] = lines[i].strip().strip('*').strip()
                i += 1
                # Skip blank lines to content
                while i < len(lines) and not lines[i].strip():
                    i += 1
                current_section = "chapter"
                continue

            elif stripped == "GLOSSARY":
                if current_section == "chapter" and current_chapter:
                    current_chapter["content"] = ''.join(chapter_content).strip()
                    data["chapters"].append(current_chapter)
                    chapter_content = []
                current_section = "glossary"
                i += 1
                continue

            if current_section == "chapter":
                chapter_content.append(line)
            elif current_section == "glossary":
                glossary_lines.append(line)

            i += 1

        # Append the last section
        if current_section == "chapter" and current_chapter:
            current_chapter["content"] = ''.join(chapter_content).strip()
            data["chapters"].append(current_chapter)
        elif current_section == "glossary":
            current_term = None
            term_description = []

            for line in glossary_lines:
                if line.strip().startswith("> "):
                    # Save previous term
                    if current_term:
                        current_term["description"] = ''.join(term_description).strip()
                        data["glossary"].append(current_term)
                        term_description = []

                    raw = line.strip()[2:].strip()

                    # Step 1: Extract bold term, optional colon after bold
                    term_match = re.match(r'^\*\*(.+?)\*\*\s*:?\s*(.*)', raw)
                    if term_match:
                        term_name = term_match.group(1).strip()
                        rest = term_match.group(2).strip()
                    else:
                        term_name = None
                        rest = raw

                    # Step 2: Check for pronunciation (parentheses)
                    pron_match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*[:\-]?\s*(.*)$', rest)
                    if pron_match:
                        base_term = pron_match.group(1).strip()
                        pronunciation = pron_match.group(2).strip().rstrip("\\")
                        description = pron_match.group(3).strip()
                    else:
                        pronunciation = ""
                        description = rest

                    final_term = term_name or base_term or rest

                    current_term = {
                        "term": final_term,
                        "pronunciation": pronunciation
                    }

                    if description:
                        term_description.append(description + "\n")
                else:
                    # Continuation line
                    if current_term:
                        term_description.append(line.strip() + "\n")

            # Save the last term
            if current_term:
                current_term["description"] = ''.join(term_description).strip()
                data["glossary"].append(current_term)

        # Write to JSON (same location as TXT, different extension)
        output_filename = filename.replace('.txt', '.json')
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"  ✓ Created: {Path(output_filename).name} "
                   f"({len(data['chapters'])} chapters, {len(data['glossary'])} glossary entries)")
        
        books_processed += 1

    logger.info(f"\n✓ Parsed {books_processed} TXT files to JSON")
    return books_processed


def save_all_parsed_books(skip_txt_parsing=False):
    """
    Complete pipeline: Parse TXT to JSON, then create structured output
    
    Args:
        skip_txt_parsing: If True, skip TXT→JSON step (use existing JSON)
    """
    
    setup_logging()
    logger.info("\n")
    logger.info("="*70)
    logger.info("COMPLETE BOOK PROCESSING PIPELINE")
    logger.info("="*70)
    
    config = Config()
    books_path = Path(config.BOOKS_PATH)
    
    # Step 1: Parse TXT to JSON (unless skipped)
    if not skip_txt_parsing:
        books_processed = parse_txt_to_json(books_path)
        if books_processed == 0:
            logger.warning("No books parsed from TXT. Continuing with existing JSON...")
    else:
        logger.info("Skipping TXT→JSON parsing (using existing JSON files)")
    
    # Step 2: Process JSON to structured output
    logger.info("\n" + "="*70)
    logger.info("STEP 2: Processing JSON to structured output")
    logger.info("="*70)
    
    parser = BookParser(config)
    
    # Parse all books
    all_books = parser.parse_all_books()
    
    if not all_books:
        logger.error("No books found to process!")
        return
    
    # Save individual books
    output_dir = Path(config.get_processed_file('books_structured'))
    output_dir = output_dir.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\nSaving individual book files to: {output_dir}")
    
    for book in all_books:
        meta = book['book_metadata']
        book_num = meta['book_number']
        
        # Save individual book
        filename = f"book_{book_num:02d}_parsed.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(book, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Saved: {filename} ({meta['total_chapters']} chapters)")
    
    # Save combined file
    combined_file = config.get_processed_file('books_all_parsed.json')
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_books, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Saved combined file: {combined_file}")
    
    # Save all chapters flat
    all_chapters = parser.get_all_chapters_flat()
    chapters_file = config.get_processed_file('all_chapters.json')
    
    with open(chapters_file, 'w', encoding='utf-8') as f:
        json.dump(all_chapters, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Saved all chapters: {chapters_file} ({len(all_chapters)} chapters)")
    
    # Save unified glossary
    unified_glossary = parser.build_unified_glossary()
    glossary_file = Path(config.METADATA_PATH) / 'unified_glossary.json'
    glossary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(glossary_file, 'w', encoding='utf-8') as f:
        json.dump(unified_glossary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✓ Saved unified glossary: {glossary_file} ({len(unified_glossary)} terms)")
    
    # Summary
    total_chapters = sum(book['book_metadata']['total_chapters'] for book in all_books)
    total_glossary = sum(book['book_metadata']['glossary_entries'] for book in all_books)
    
    logger.info("\n" + "="*70)
    logger.info("FINAL SUMMARY")
    logger.info("="*70)
    logger.info(f"Books processed: {len(all_books)}")
    logger.info(f"Total chapters: {total_chapters}")
    logger.info(f"Total glossary entries: {total_glossary}")
    logger.info(f"Unique glossary terms: {len(unified_glossary)}")
    logger.info("\nOutput files:")
    logger.info(f"  - {len(all_books)} individual book JSONs in data/raw/books/")
    logger.info(f"  - {len(all_books)} parsed books in data/processed/")
    logger.info(f"  - 1 combined file: books_all_parsed.json")
    logger.info(f"  - 1 all chapters file: all_chapters.json")
    logger.info(f"  - 1 unified glossary: unified_glossary.json")
    logger.info("="*70)


def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(
        description="Complete book processing pipeline: TXT → JSON → Structured output"
    )
    parser.add_argument(
        '--skip-txt-parsing',
        action='store_true',
        help='Skip TXT→JSON step, only process existing JSON files'
    )
    
    args = parser.parse_args()
    
    save_all_parsed_books(skip_txt_parsing=args.skip_txt_parsing)


if __name__ == "__main__":
    main()