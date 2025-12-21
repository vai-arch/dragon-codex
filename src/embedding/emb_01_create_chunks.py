"""
Week 4 - Chunk creation

Input: wiki_character.json
Output: wiki_chunks_character.jsonl
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm

from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_chunking_functions import (
    chunk_statistics,
    split_into_paragraphs,
    split_paragraph_into_chunks,
)
from src.utils.util_files_functions import load_json_from_file, save_jsonl_to_file
from src.utils.util_statistics import (
    log_results_table,
    print_results,
    print_results_table,
    total_statistics_logging,
)

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


def chunk_character_pages():
    """
    Chunk the 2,452 character pages.
    Groups sections together to reach target size, preserving structure.
    """
    character_data = load_json_from_file(in_file_wiki_character)
    all_chunks = []

    # Process each character page
    for filename, page_data in tqdm(character_data.items(), desc="Processing characters"):
        character_name = page_data["character_name"]

        # Build list of section texts
        section_texts = []
        section_titles = []

        for section in page_data["non_temporal_sections"]:
            section_title = section["section_title"]

            # Get content - either from section or combined subsections
            if section["content"]:
                # Section has direct content
                text = section["content"]
            elif section["subsections"]:
                # Section has subsections - combine them
                subsection_texts = []
                for subsection in section["subsections"]:
                    if subsection["content"]:
                        subsection_texts.append(f"**{subsection['title']}**\n{subsection['content']}")
                text = "\n\n".join(subsection_texts)
            else:
                # Empty section - skip
                continue

            # Skip if text is empty after processing
            if not text.strip():
                continue

            section_texts.append(text)
            section_titles.append(section_title)

        if not section_texts:
            continue

        # Group sections into chunks
        chunks = []
        current_chunk_sections = []
        current_chunk_titles = []
        current_size = 0

        for section_text, section_title in zip(section_texts, section_titles):
            section_size = len(section_text)

            # If single section exceeds max, split it
            if section_size > cfg_max_chunk_size:
                # Save current chunk if exists
                if current_chunk_sections:
                    chunks.append(
                        {
                            "text": "\n\n".join(current_chunk_sections),
                            "section_title": ", ".join(current_chunk_titles),
                        }
                    )
                    current_chunk_sections = []
                    current_chunk_titles = []
                    current_size = 0

                # Split oversized section
                section_chunks = split_into_paragraphs(section_text)
                for chunk_text in section_chunks:
                    chunks.append({"text": chunk_text, "section_title": section_title})
                continue

            # Check if adding this section would exceed max
            separator_size = 2 if current_chunk_sections else 0
            new_size = current_size + separator_size + section_size

            if new_size <= cfg_max_chunk_size:
                # Fits - add to current chunk
                current_chunk_sections.append(section_text)
                current_chunk_titles.append(section_title)
                current_size = new_size
            else:
                # Doesn't fit - start new chunk
                if current_chunk_sections:
                    chunks.append(
                        {
                            "text": "\n\n".join(current_chunk_sections),
                            "section_title": ", ".join(current_chunk_titles),
                        }
                    )

                current_chunk_sections = [section_text]
                current_chunk_titles = [section_title]
                current_size = section_size

        # Add final chunk
        if current_chunk_sections:
            chunks.append(
                {
                    "text": "\n\n".join(current_chunk_sections),
                    "section_title": ", ".join(current_chunk_titles),
                }
            )

        # Create chunk objects with metadata
        total_chunks = len(chunks)
        for idx, chunk_data in enumerate(chunks):
            chunk = {
                "source": "wiki",
                "wiki_type": "character",
                "character_name": character_name,
                "filename": filename,
                "section_title": chunk_data["section_title"],
                "temporal_order": None,
                "chunk_index": idx + 1,
                "total_chunks": total_chunks,
                "text": chunk_data["text"],
            }
            all_chunks.append(chunk)

    # Save chunks
    save_jsonl_to_file(all_chunks, out_file_wiki_chunks_character)

    # Print statistics
    results = chunk_statistics(all_chunks, "CHARACTERS CHUNKS")
    results["metrics"]["number_of_items"] = len(character_data)

    print_results(results, "")

    return results


def chunk_chapter_summary_pages():
    """
    Chunk the 714 chapter summary pages.
    Split oversized chapters into multiple chunks with overlap.
    """
    # Load chapter summary data
    chapter_data = load_json_from_file(in_file_wiki_chapter_summary)

    all_chunks = []

    # Process each chapter summary
    for filename, page_data in tqdm(chapter_data.items(), desc="Processing chapters"):
        # Build the full content
        content_parts = []

        for section in page_data["sections"]:
            if section["content"]:
                content_parts.append(f"**{section['title']}**\n{section['content']}")

        # Combine all sections into one text
        full_content = "\n\n".join(content_parts)

        if not full_content.strip():
            continue

        # Split into paragraphs (same as books)
        paragraphs = split_into_paragraphs(full_content)

        # Process all paragraphs through the chunking function (same as books)
        text_chunks = []
        for paragraph in paragraphs:
            para_chunks = split_paragraph_into_chunks(paragraph=paragraph)
            text_chunks.extend(para_chunks)

        # Create chunk objects with metadata (same structure as books)
        total_chunks = len(text_chunks)

        for idx, chunk_text in enumerate(text_chunks):
            chunk = {
                "source": "wiki",
                "wiki_type": "chapter_summary",
                "book_number": page_data["book_number"],
                "book_title": page_data["book_title"],
                "chapter_number": page_data["chapter_number"],
                "chapter_title": page_data["chapter_title"],
                "filename": filename,
                "temporal_order": page_data["book_number"],
                "chunk_index": idx + 1,
                "total_chunks": total_chunks,
                "text": chunk_text,
            }
            all_chunks.append(chunk)

    # Save chunks
    save_jsonl_to_file(all_chunks, out_file_wiki_chunks_chapter_summary)

    # Print statistics
    results = chunk_statistics(all_chunks, "CHAPTER SUMMARY CHUNKS")
    results["metrics"]["number_of_items"] = len(chapter_data)

    print_results(results, "")

    return results


def chunk_chronology_pages():
    """
    Chunk the chronology pages into temporal sections.
    Handles both temporal (book-based) and non-temporal (event-based) structures.
    """

    chronology_data = load_json_from_file(in_file_wiki_chronology)
    all_chunks = []

    # Process each chronology page
    for filename, page_data in tqdm(chronology_data.items(), desc="Processing chronologies"):
        character_name = page_data["character_name"]

        # Process temporal sections (book-by-book) - Rand, Mat
        for section in page_data.get("temporal_sections", []):
            content = section["content"]

            if not content.strip():
                continue

            # Split large content into chunks
            content_chunks = split_into_paragraphs(content)

            # Create a chunk object for each split
            for idx, chunk_text in enumerate(content_chunks):
                chunk = {
                    "source": "wiki",
                    "wiki_type": "chronology",
                    "character_name": character_name,
                    "filename": filename,
                    "temporal_order": section["book_number"],
                    "book_title": section["book_title"],
                    "chunk_index": idx + 1,
                    "total_chunks": len(content_chunks),
                    "text": chunk_text,
                }
                all_chunks.append(chunk)

        # Process non-temporal sections (event-based) - Perrin, Egwene, Elayne
        for section in page_data.get("non_temporal_sections", []):
            section_title = section.get("section_title", "")
            content = section.get("content", "")

            # Combine subsections if present
            if section.get("subsections"):
                subsection_texts = []
                if content.strip():
                    subsection_texts.append(content)
                for subsection in section["subsections"]:
                    if subsection.get("content"):
                        subsection_texts.append(f"**{subsection['title']}**\n{subsection['content']}")
                if subsection_texts:
                    content = "\n\n".join(subsection_texts)

            if not content.strip():
                continue

            # Split large content into chunks
            content_chunks = split_into_paragraphs(content)

            # Create a chunk object for each split
            for idx, chunk_text in enumerate(content_chunks):
                chunk = {
                    "source": "wiki",
                    "wiki_type": "chronology",
                    "character_name": character_name,
                    "filename": filename,
                    "temporal_order": None,  # Event-based, no specific book number
                    "book_title": None,
                    "section_title": section_title,
                    "chunk_index": idx + 1,
                    "total_chunks": len(content_chunks),
                    "text": chunk_text,
                }
                all_chunks.append(chunk)

    # Save chunks
    save_jsonl_to_file(all_chunks, out_file_wiki_chunks_chronology)

    # Character breakdown
    char_counts = {}
    for chunk in all_chunks:
        char_name = chunk["character_name"]
        char_counts[char_name] = char_counts.get(char_name, 0) + 1

    results = chunk_statistics(all_chunks, "CHRONOLOGIES CHUNKS")
    results["metrics"]["number_of_items"] = len(char_counts)

    print_results(results, "")

    return results


def aux_chunk_book_chapter(chapter: Dict, book_number: int, book_title: str) -> List[Dict]:
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

    # Process all paragraphs through the chunking function
    all_chunks = []
    for paragraph in paragraphs:
        para_chunks = split_paragraph_into_chunks(paragraph=paragraph)
        all_chunks.extend(para_chunks)

    # Create chunk objects with metadata
    chunk_objects = []
    total_chunks = len(all_chunks)

    for idx, chunk_text in enumerate(all_chunks):
        chunk_id = f"book_{book_number:02d}_ch_{chapter_number:02d}_chunk_{idx + 1:03d}"

        chunk_obj = {
            "source": "book",
            "chunk_id": chunk_id,
            "book_number": book_number,
            "book_title": book_title,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "chapter_type": chapter_type,
            "chunk_index": idx + 1,
            "total_chunks_in_chapter": total_chunks,
            "text": chunk_text,
            "temporal_order": book_number,
        }

        chunk_objects.append(chunk_obj)

    return chunk_objects


def chunk_books():
    """
    Process all books and create chunks.

    Args:
        books_file: Path to books_all_parsed.json
        output_file: Path to save book_chunks.jsonl
    """

    all_books = load_json_from_file(in_file_books_all_parsed)

    # Process each book
    all_chunks = []

    number_of_chapters = 0
    book_statistics = []
    for book_data in tqdm(all_books, desc="Processing books", unit="book"):
        book_number = book_data.get("book_metadata", {}).get("book_number", 0)
        book_title = book_data.get("book_metadata", {}).get("book_title", "Unknown")
        chapters = book_data.get("chapters", [])

        number_of_chapters += len(chapters)

        book_chunks = []
        for chapter in chapters:
            chapter_chunks = aux_chunk_book_chapter(chapter, int(book_number), book_title)
            book_chunks.extend(chapter_chunks)

        all_chunks.extend(book_chunks)
        book_statistics.append(
            {
                "name": book_title,
                "metrics": {"chapters": len(chapters), "chunks": len(book_chunks)},
            }
        )

    print_results_table(book_statistics, "")
    log_results_table(book_statistics, "chunks_by_chapters")

    save_jsonl_to_file(all_chunks, out_file_book_chunks)

    results = chunk_statistics(all_chunks, "BOOKS CHUNKS")
    results["metrics"]["number_of_items"] = number_of_chapters

    print_results(results, "")

    return results


def aux_chunk_page(filename: str, page_data: Dict, source_type: str) -> List[Dict]:
    """
    Chunk a single wiki page by grouping sections to reach target size.
    Preserves section structure while creating properly-sized chunks.

    Args:
        filename: Source filename
        page_data: Parsed page data
        source_type: 'concept', 'prophecy', or 'magic'

    Returns:
        List of chunks
    """
    page_name = page_data.get("page_name", "")
    page_type = page_data.get("page_type", "")
    sections = page_data.get("sections", [])
    categories = page_data.get("metadata", {}).get("categories", [])

    # Build list of section texts (each section with its subsections)
    section_texts = []
    section_titles = []

    for section in sections:
        section_title = section.get("title", "")
        section_content = section.get("content", "").strip()

        # Skip category sections
        if section_title.lower() in ["categories", "category"]:
            continue

        # Build section text with subsections
        section_parts = []

        # Add main section content
        if section_title and section_content:
            section_parts.append(f"## {section_title}\n{section_content}")
        elif section_title:
            section_parts.append(f"## {section_title}")
        elif section_content:
            section_parts.append(section_content)

        # Add subsections
        for subsection in section.get("subsections", []):
            sub_title = subsection.get("title", "")
            sub_content = subsection.get("content", "").strip()

            if sub_title and sub_content:
                section_parts.append(f"### {sub_title}\n{sub_content}")
            elif sub_title:
                section_parts.append(f"### {sub_title}")
            elif sub_content:
                section_parts.append(sub_content)

        # Combine section and subsections
        full_section_text = "\n\n".join(section_parts)

        if not full_section_text.strip():
            continue

        section_texts.append(full_section_text)
        section_titles.append(section_title if section_title else "Content")

    if not section_texts:
        return []

    # Group sections into chunks (like grouping paragraphs)
    chunks = []
    current_chunk_sections = []
    current_chunk_titles = []
    current_size = 0

    max_size = cfg_max_chunk_size

    for section_text, section_title in zip(section_texts, section_titles):
        section_size = len(section_text)

        # If single section exceeds max, split it by paragraphs
        if section_size > max_size:
            # Save current chunk if exists
            if current_chunk_sections:
                chunk_text = "\n\n".join(current_chunk_sections)
                chunk_titles = ", ".join(current_chunk_titles)
                chunks.append({"text": chunk_text, "section_title": chunk_titles})
                current_chunk_sections = []
                current_chunk_titles = []
                current_size = 0

            # Split oversized section by paragraphs and group them
            section_chunks = split_into_paragraphs(section_text)

            for chunk_text in section_chunks:
                chunks.append({"text": chunk_text, "section_title": section_title})
            continue

        # Check if adding this section would exceed max
        separator_size = 2 if current_chunk_sections else 0
        new_size = current_size + separator_size + section_size

        if new_size <= max_size:
            # Fits - add to current chunk
            current_chunk_sections.append(section_text)
            current_chunk_titles.append(section_title)
            current_size = new_size
        else:
            # Doesn't fit - start new chunk
            if current_chunk_sections:
                chunk_text = "\n\n".join(current_chunk_sections)
                chunk_titles = ", ".join(current_chunk_titles)
                chunks.append({"text": chunk_text, "section_title": chunk_titles})

            current_chunk_sections = [section_text]
            current_chunk_titles = [section_title]
            current_size = section_size

    # Add final chunk
    if current_chunk_sections:
        chunk_text = "\n\n".join(current_chunk_sections)
        chunk_titles = ", ".join(current_chunk_titles)
        chunks.append({"text": chunk_text, "section_title": chunk_titles})

    # Convert to final chunk format with metadata
    final_chunks = []
    total_chunks = len(chunks)

    for idx, chunk_data in enumerate(chunks):
        chunk = {
            "source": "wiki",
            "source_type": source_type,
            "page_type": page_type,
            "page_name": page_name,
            "source_file": filename,
            "section_title": chunk_data["section_title"],
            "temporal_order": None,
            "chunk_index": idx + 1,
            "total_chunks": total_chunks,
            "text": chunk_data["text"],
        }

        if categories:
            chunk["categories"] = categories

        final_chunks.append(chunk)

    return final_chunks


def chunk_concept_magic_prophecy(input_file: Path, output_file: Path, source_type: str) -> tuple:
    """
    Process a single file type (concept, prophecy, or magic).

    Args:
        input_file: Input JSON file path
        output_file: Output JSONL file path
        source_type: 'concept', 'prophecy', or 'magic'

    Returns:
        (chunks_created, stats_dict)
    """

    concept_data = load_json_from_file(input_file)

    # Process all pages
    all_chunks = []
    pages_processed = 0
    empty_pages = 0

    for filename, page_data in tqdm(concept_data.items(), desc=f"Processing {source_type}"):
        chunks = aux_chunk_page(filename, page_data, source_type)

        if not chunks:
            empty_pages += 1
            continue

        all_chunks.extend(chunks)
        pages_processed += 1

    save_jsonl_to_file(all_chunks, output_file)

    # Print statistics

    results = chunk_statistics(all_chunks, f"{source_type.upper()} CHUNKS")
    results["metrics"]["number_of_items"] = pages_processed

    print_results(results, "")

    return results


def main():
    start_time = datetime.now()

    statistics = []

    statistics.append(chunk_character_pages())
    statistics.append(chunk_chapter_summary_pages())
    statistics.append(chunk_chronology_pages())
    statistics.append(chunk_books())
    statistics.append(chunk_concept_magic_prophecy(in_file_wiki_concept, out_file_wiki_chunks_concept, "concept"))
    statistics.append(chunk_concept_magic_prophecy(in_file_wiki_prophecies, out_file_wiki_chunks_prophecies, "prophecy"))
    statistics.append(chunk_concept_magic_prophecy(in_file_wiki_magic, out_file_wiki_chunks_magic, "magic"))

    total_time = (datetime.now() - start_time).total_seconds()

    total_statistics_logging(total_time=total_time, log_name="emb_01_create_chunks", statistics=statistics, title="CHUNK CREATION", tables=True)


if __name__ == "__main__":
    paths = get_paths()
    config = get_config()

    cfg_max_chunk_size = config.MAX_CHUNK_SIZE

    in_file_wiki_character = paths.FILE_WIKI_CHARACTER
    in_file_wiki_chapter_summary = paths.FILE_WIKI_CHAPTER_SUMMARY
    in_file_wiki_chronology = paths.FILE_WIKI_CHRONOLOGY
    in_file_books_all_parsed = paths.FILE_BOOKS_ALL_PARSED
    in_file_wiki_concept = paths.FILE_WIKI_CONCEPT
    in_file_wiki_prophecies = paths.FILE_WIKI_PROPHECIES
    in_file_wiki_magic = paths.FILE_WIKI_MAGIC
    out_file_wiki_chunks_chapter_summary = paths.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY
    out_file_wiki_chunks_character = paths.FILE_WIKI_CHUNKS_CHARACTER
    out_file_wiki_chunks_chronology = paths.FILE_WIKI_CHUNKS_CHRONOLOGY
    out_file_book_chunks = paths.FILE_BOOK_CHUNKS
    out_file_wiki_chunks_concept = paths.FILE_WIKI_CHUNKS_CONCEPT
    out_file_wiki_chunks_prophecies = paths.FILE_WIKI_CHUNKS_PROPHECIES
    out_file_wiki_chunks_magic = paths.FILE_WIKI_CHUNKS_MAGIC

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
