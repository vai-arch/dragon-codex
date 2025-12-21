"""
Week 4 - Chunk creation

Input: wiki_character.json
Output: wiki_chunks_character.jsonl
"""

import re
import sys
import traceback
from typing import Dict, List

from tqdm import tqdm

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file
from src.utils.util_statistics import log_results_table, reset_log

cfg_max_chunk_size = None

in_file_wiki_character = None
in_file_wiki_chapter_summary = None
in_file_wiki_chronology = None
in_file_books_all_parsed = None
in_file_wiki_concept = None
in_file_wiki_prophecies = None
in_file_wiki_magic = None

out_file_wiki_chunks_chapter_summary = None
out_file_wiki_chunks_character = None
out_file_wiki_chunks_chronology = None
out_file_book_chunks = None
out_file_wiki_chunks_concept = None
out_file_wiki_chunks_prophecies = None
out_file_wiki_chunks_magic = None


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into properly-sized chunks, grouping paragraphs as needed.

    Args:
        text: Text to split
        config: Config object

    Returns:
        List of chunk strings
    """
    if not text:
        return []

    # Content too large - split into paragraphs
    paragraphs = re.split(r"\n\s*\n+", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return paragraphs


def log_paragraph_statistics_for_chapter(chapter: Dict, book_number: int, book_title: str) -> List[Dict]:
    """
    Chunk a single chapter into smaller pieces.

    Args:
        chapter: Chapter dict with content, title, etc.
        book_number: Book number (0-14)
        book_title: Book title

    Returns:
        List of chunk dicts
    """
    content = chapter.get("content", "")
    chapter_number = chapter.get("chapter_number", 0)
    chapter_title = chapter.get("chapter_title", "")
    chapter_type = chapter.get("chapter_type", "chapter")

    # Split into paragraphs
    paragraphs = split_into_paragraphs(content)

    paragraph_stats = []
    for idx, paragraph in enumerate(paragraphs):
        paragraph_id = f"book_{book_number:02d}_ch_{chapter_number:02d}_paragraph_{idx + 1:03d}"

        paragraph_stat = {
            "name": paragraph_id,
            "metrics": {
                "source": "book",
                "book_number": book_number,
                "book_title": book_title,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "chapter_type": chapter_type,
                "paragraph_id": paragraph_id,
                "paragraph_index": idx + 1,
                "paragraph_length": len(paragraph),
            },
        }

        paragraph_stats.append(paragraph_stat)

    log_results_table(log_file="val_01_paragraphs_length", main_message="", results=paragraph_stats)

    return paragraph_stats


def chunk_books():
    """
    Process all books and create chunks.

    Args:
        books_file: Path to books_all_parsed.json
        output_file: Path to save book_chunks.jsonl
    """

    all_books = load_json_from_file(in_file_books_all_parsed)

    # Process each book
    number_of_chapters = 0
    for book_data in tqdm(all_books, desc="Processing books", unit="book"):
        book_number = book_data.get("book_metadata", {}).get("book_number", 0)
        book_title = book_data.get("book_metadata", {}).get("book_title", "Unknown")
        chapters = book_data.get("chapters", [])

        number_of_chapters += len(chapters)

        chapter_stats = []
        for chapter in chapters:
            log_paragraph_statistics_for_chapter(chapter, int(book_number), book_title)
            chapter_number = chapter.get("chapter_number", 0)
            chapter_id = f"book_{int(book_number):02d}_ch_{chapter_number:02d}"
            chapter_title = chapter.get("chapter_title", "")
            chapter_type = chapter.get("chapter_type", "chapter")
            content = chapter.get("content", "")

            chapter_stat = {
                "name": chapter_id,
                "metrics": {
                    "source": "book",
                    "book_number": book_number,
                    "book_title": book_title,
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "chapter_type": chapter_type,
                    "chapter_id": chapter_id,
                    "chapter_length": len(content),
                },
            }

            chapter_stats.append(chapter_stat)

        log_results_table(log_file="val_01_chapters_length", main_message="", results=chapter_stats)


def main():
    reset_log("val_01_paragraphs_length")
    reset_log("val_01_chapters_length")
    chunk_books()


if __name__ == "__main__":
    paths = get_paths()
    config = get_config()

    cfg_max_chunk_size = config.MAX_CHUNK_SIZE

    in_file_books_all_parsed = paths.FILE_BOOKS_ALL_PARSED
    out_file_book_chunks = paths.VALIDATIONS_TESTS / "book_chunks_validations.jsonl"

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
