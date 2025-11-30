"""
Reprocess Books Pipeline
Runs all steps needed when raw book files are modified

Steps:
1. Parse raw TXT books to JSON
2. Load JSON and create structured output
3. Save all processed files

Usage:
    python scripts\reprocess_books.py
    python scripts\reprocess_books.py --book 5  # Only reprocess book 5
"""

import argparse
import subprocess
import sys
from pathlib import Path
from src.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def run_command(command, description):
    """Run a command and log results"""
    logger.info("="*70)
    logger.info(f"STEP: {description}")
    logger.info("="*70)
    logger.info(f"Running: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        logger.info(f"✓ {description} - SUCCESS")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} - FAILED")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False


def reprocess_all_books():
    """Reprocess all books from raw TXT to final processed output"""
    
    setup_logging()
    
    logger.info("\n")
    logger.info("="*70)
    logger.info("REPROCESSING ALL BOOKS")
    logger.info("="*70)
    logger.info("\nThis will:")
    logger.info("  1. Parse raw TXT books to JSON")
    logger.info("  2. Load JSON and add metadata")
    logger.info("  3. Save structured output")
    logger.info("  4. Rebuild unified glossary")
    logger.info("")
    
    # # Step 1: Parse raw TXT to JSON
    # success = run_command(
    #     "python parse_all_books.py",
    #     "Parse raw TXT books to JSON"
    # )
    # if not success:
    #     logger.error("Failed at step 1. Aborting.")
    #     return False
    
    # Step 2: Process JSON to structured output
    success = run_command(
        "C:/Users/victor.diaz/AppData/Local/miniconda3/envs/dragon/python.exe c:/Users/victor.diaz/Documents/_AI/dragon-codex/src/ingestion/books/save_parsed_books.py",
        "Process JSON and save structured output"
    )
    if not success:
        logger.error("Failed at step 2. Aborting.")
        return False
    
    logger.info("\n" + "="*70)
    logger.info("✓✓✓ REPROCESSING COMPLETE!")
    logger.info("="*70)
    logger.info("\nOutput files updated:")
    logger.info("  - data/raw/books/*.json (from TXT)")
    logger.info("  - data/processed/book_*_parsed.json")
    logger.info("  - data/processed/books_all_parsed.json")
    logger.info("  - data/processed/all_chapters.json")
    logger.info("  - data/metadata/unified_glossary.json")
    logger.info("")
    
    return True


def reprocess_single_book(book_number):
    """Reprocess a single book"""
    
    setup_logging()
    
    logger.info("\n")
    logger.info("="*70)
    logger.info(f"REPROCESSING BOOK {book_number}")
    logger.info("="*70)
    logger.info("\nNote: parse_all_books.py processes ALL books")
    logger.info("      (no single-book option available)")
    logger.info("")
    
    # Still need to run full pipeline
    # because unified glossary needs all books
    
    success = reprocess_all_books()
    
    if success:
        logger.info(f"\n✓ Book {book_number} changes are now in processed output")
    
    return success


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Reprocess WoT books after raw file changes"
    )
    parser.add_argument(
        '--book',
        type=int,
        help='Reprocess only specific book number (0-14)'
    )
    
    args = parser.parse_args()
    
    if args.book is not None:
        if 0 <= args.book <= 14:
            success = reprocess_single_book(args.book)
        else:
            print("Error: Book number must be between 0 and 14")
            sys.exit(1)
    else:
        success = reprocess_all_books()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()