"""
Create books_structured.json with all processed book data.

Week 2 Session 2 - Dragon's Codex
Consolidates all 15 books into a single structured JSON file.

'output_path': 'data/processed/books_structured.json'

"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from tqdm import tqdm

from src.utils.logger import get_logger
from src.utils.paths import get_paths
from src.utils.util_files_functions import (
    find_files_in_folder,
    load_json_from_file,
    save_json_to_file,
)
from src.utils.util_statistics import print_results_table, total_statistics_logging
from src.utils.wot_constants import BOOK_TITLES

logger = get_logger(__name__)

in_auxiliary_books_path = None
out_processed_books_path = None
out_file_books_all_parsed = None
out_file_all_chapters = None
out_file_unified_glossary = None


class BookParser:
    """
    Parses WoT book JSON files into structured format
    """

    def __init__(self, auxiliary_books_path=None):
        """
        Initialize parser

        Args:
        """
        self.books_path = auxiliary_books_path
        logger.info(f"BookParser initialized. Books path: {self.books_path}")

    def paragraph_stats(self, text: str) -> Dict[str, float]:
        """
        Compute paragraph statistics for text separated by double newlines.

        Returns:
            {
                "paragraphs": int,
                "min_chars": int,
                "max_chars": int,
                "avg_chars": float
            }
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            return {"paragraphs": 0, "min_chars": 0, "max_chars": 0, "avg_chars": 0.0}

        lengths = [len(p) for p in paragraphs]

        return {
            "paragraphs": len(paragraphs),
            "min_chars": min(lengths),
            "max_chars": max(lengths),
            "avg_chars": round(sum(lengths) / len(lengths)),
        }

    def parse_book(self, json_filepath: int) -> Optional[Dict]:
        """
        Parse a book and return structured data with metadata

        Args:
            book_number: Book number (0-14)

        Returns:
            dict with parsed book data including:
                - book_metadata
                - chapters (with metadata)
                - glossary
        """
        # Load JSON
        book_data = load_json_from_file(json_filepath, False)

        book_number = json_filepath.name.split("-", 1)[0]

        # Build metadata
        metadata = {
            "book_number": book_number,
            "book_filename": json_filepath.name,
            "book_title": BOOK_TITLES.get(book_number, book_data.get("book_name", "")),
            "book_name_file": book_data.get("book_name", ""),
            "total_chapters": len(book_data.get("chapters", [])),
            "has_prologue": any(ch["type"] == "prologue" for ch in book_data.get("chapters", [])),
            "has_epilogue": any(ch["type"] == "epilogue" for ch in book_data.get("chapters", [])),
            "glossary_entries": len(book_data.get("glossary", [])),
        }

        # Process chapters with metadata
        chapters = []
        chapters_statistics = []
        for chapter in book_data.get("chapters", []):
            para_stats = self.paragraph_stats(chapter["content"])
            chapter_with_meta = {
                "chapter_number": chapter["number"],
                "chapter_type": chapter["type"],
                "chapter_title": chapter["title"],
                "metadata": {
                    "book_number": book_number,
                    "book_title": metadata["book_title"],
                    "temporal_order": book_number,  # For filtering
                    "content_length": len(chapter["content"]),
                    "paragraph_stats": para_stats,
                    "word_count": len(chapter["content"].split()),
                },
                "content": chapter["content"],
            }
            chapters.append(chapter_with_meta)
            chapters_statistics.append(
                {
                    "name": str(book_number) + "-" + metadata["book_title"],
                    "metrics": {"chapter": chapter["type"] + " " + str(chapter["number"]), "number_of_chars": len(chapter["content"]), "word_count": len(chapter["content"].split()), **para_stats},
                }
            )
        # Process glossary with metadata
        glossary = []
        for entry in book_data.get("glossary", []):
            glossary_with_meta = {
                "term": (" ".join(entry["term"]) if isinstance(entry["term"], list) else str(entry["term"])).rstrip(":"),  # remove trailing colon
                "pronunciation": entry.get("pronunciation", ""),
                "description": entry.get("description", ""),
                "metadata": {
                    "book_number": book_number,
                    "book_title": metadata["book_title"],
                    "source": "book_glossary",
                },
            }
            glossary.append(glossary_with_meta)

        result = {
            "book_metadata": metadata,
            "chapters": chapters,
            "glossary": glossary,
            "chapters_statistics": chapters_statistics,
        }

        return result

    def get_chapter_by_number(self, book_number: int, chapter_number: int) -> Optional[Dict]:
        """
        Get a specific chapter

        Args:
            book_number: Book number (0-14)
            chapter_number: Chapter number (0=prologue, 1+=chapters, max+1=epilogue)

        Returns:
            Chapter dict or None
        """
        book_data = self.parse_book(book_number)
        if not book_data:
            return None

        for chapter in book_data["chapters"]:
            if chapter["chapter_number"] == chapter_number:
                return chapter

        return None

    def build_unified_glossary(self, all_books) -> Dict[str, Dict]:
        """
        Build unified glossary with all sources tracked

        Returns:
            dict mapping term to {definition, pronunciation, sources[]}
        """
        logger.info("Building unified glossary...")

        unified = {}
        all_glossary = []
        for book in all_books:
            all_glossary.extend(book["glossary"])

        for entry in all_glossary:
            term = entry["term"]

            if term not in unified:
                unified[term] = {
                    "term": term,
                    "pronunciation": entry["pronunciation"],
                    "definition": entry["description"],
                    "sources": [],
                }

            # Track which books mention this term
            source_info = {
                "book_number": entry["metadata"]["book_number"],
                "book_title": entry["metadata"]["book_title"],
            }
            if source_info not in unified[term]["sources"]:
                unified[term]["sources"].append(source_info)

        logger.info(f"Built unified glossary with {len(unified)} unique terms")
        return unified


def process_json_files():
    parser = BookParser(in_auxiliary_books_path)

    # Parse all books
    all_books = []

    json_files_paths = find_files_in_folder(in_auxiliary_books_path, ".json")

    books_stats = []
    for json_filepath in tqdm(json_files_paths, desc="Processing Json files"):
        book_data = parser.parse_book(json_filepath)
        all_books.append(book_data)
        book_stats = book_data["chapters_statistics"]
        books_stats.extend(book_stats)

    # Save individual books
    for book in all_books:
        meta = book["book_metadata"]
        filename = meta["book_filename"]
        # Save individual book
        save_json_to_file(
            book,
            out_processed_books_path / f"{Path(filename).stem}_parsed.json",
            indent=2,
        )

    # Save combined file
    save_json_to_file(all_books, out_file_books_all_parsed, indent=2)

    # Save all chapters flat
    all_chapters = []
    for book in all_books:
        all_chapters.extend(book["chapters"])

    save_json_to_file(all_chapters, out_file_all_chapters, indent=2)

    # Save unified glossary
    unified_glossary = parser.build_unified_glossary(all_books)

    save_json_to_file(unified_glossary, out_file_unified_glossary, indent=2)

    print_results_table(books_stats)

    return books_stats


def main():
    start_time = datetime.now()

    statistics = process_json_files()

    total_time = (datetime.now() - start_time).total_seconds()

    total_statistics_logging(statistics, total_time, "PARSING JSON BOOKS", "prc_01_process_books")


if __name__ == "__main__":
    paths = get_paths()
    in_auxiliary_books_path = paths.AUXILIARY_BOOKS_PATH
    out_processed_books_path = paths.PROCESSED_BOOKS_PATH
    out_file_books_all_parsed = paths.FILE_BOOKS_ALL_PARSED
    out_file_all_chapters = paths.FILE_ALL_CHAPTERS
    out_file_unified_glossary = paths.FILE_UNIFIED_GLOSSARY

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
