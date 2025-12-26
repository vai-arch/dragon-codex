"""
Week 4 - Chunk creation

Input: wiki_character.json
Output: wiki_chunks_character.jsonl
"""

import re
import sys
import traceback
from datetime import datetime
from typing import Dict, List

from tqdm import tqdm

from src.utils.chunking.chunking_strategies import get_chunker
from src.utils.chunking.util_chunking_functions import (
    chunk_statistics,
)
from src.utils.config import get_config
from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, save_jsonl_to_file
from src.utils.util_statistics import (
    log_results_table,
    print_results,
    print_results_table,
    total_statistics_logging,
)

config = get_config()

_books_chunker = get_chunker(config.CHUNKING_STRATEGY["BOOKS_CHUNKING_STRATEGY_NAME"])
_wiki_character_chunker = get_chunker(config.CHUNKING_STRATEGY["WIKI_CHUNKING_STRATEGY_NAME"], "CHARACTER")
_wiki_chapter_summary_chunker = get_chunker(config.CHUNKING_STRATEGY["WIKI_CHUNKING_STRATEGY_NAME"], "CHAPTER_SUMMARY")
_wiki_chronology_chunker = get_chunker(config.CHUNKING_STRATEGY["WIKI_CHUNKING_STRATEGY_NAME"], "CHRONOLOGY")
_wiki_concept_chunker = get_chunker(config.CHUNKING_STRATEGY["WIKI_CHUNKING_STRATEGY_NAME"], "CONCEPT")

cfg_max_chunk_size = None
cfg_min_books_chunks_size_characters = None

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
    Chunk the ~2452 character wiki pages using hybrid strategy.
    Respects markdown structure + semantic refinement.
    """
    character_data = load_json_from_file(in_file_wiki_character)
    all_chunks = []

    for filename, page_data in tqdm(character_data.items(), desc="Processing characters"):
        character_name = page_data["character_name"]

        # === Build full page text with preserved headings ===
        page_parts = []

        # Non-temporal sections (Appearance, Personality, etc.)
        for section in page_data.get("non_temporal_sections", []):
            section_title = section.get("section_title", "Untitled Section")
            if section.get("content"):
                page_parts.append(f"## {section_title}\n{section['content'].strip()}")
            # Subsections
            if section.get("subsections"):
                for sub in section["subsections"]:
                    sub_title = sub.get("title", "")
                    sub_content = sub.get("content", "").strip()
                    if sub_title and sub_content:
                        page_parts.append(f"### {sub_title}\n{sub_content}")

        # Temporal sections (book-by-book chronology) - preserve book order
        temporal_sections = sorted(page_data.get("temporal_sections", []), key=lambda x: x.get("book_number", 999))
        for section in temporal_sections:
            book_title = section.get("book_title", "Unknown Book")
            content = section.get("content", "").strip()
            if content:
                page_parts.append(f"## Chronology: {book_title}\n{content}")

        full_text = "\n\n".join([part for part in page_parts if part.strip()])

        if not full_text.strip():
            continue

        # === Hybrid chunking ===
        raw_chunks = _wiki_character_chunker(full_text)

        # === Tiny chunk cleanup + metadata ===
        filtered_chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            temp_chunk = {
                "source": "wiki",
                "wiki_type": "character",
                "character_name": character_name,
                "filename": filename,
                "text": chunk_text,
                "temporal_order": None,  # Will infer from heading if possible
                "section_title": "",  # Extract below
            }

            # Extract section title from first heading in chunk (simple heuristic)
            heading_match = re.search(r"^##\s+(.+?)$", chunk_text, flags=re.MULTILINE)
            if heading_match:
                temp_chunk["section_title"] = heading_match.group(1)

            # Tiny chunk merge (<300 chars)
            if len(chunk_text) < cfg_min_books_chunks_size_characters:
                if filtered_chunks:
                    filtered_chunks[-1]["text"] += " " + chunk_text
                    # Update section_title if better one found
                    if temp_chunk["section_title"]:
                        filtered_chunks[-1]["section_title"] = temp_chunk["section_title"]
                # else: rare leading tiny → keep
            else:
                filtered_chunks.append(temp_chunk)

        # === Final indexing ===
        total_chunks = len(filtered_chunks)
        for final_idx, chunk in enumerate(filtered_chunks):
            chunk["chunk_index"] = final_idx + 1
            chunk["total_chunks"] = total_chunks

            # Infer temporal_order from section title (e.g., "Chronology: The Shadow Rising")
            if "Chronology:" in chunk.get("section_title", ""):
                # Map book title → book_number (you can build a dict or use existing)
                book_title = chunk["section_title"].replace("Chronology: ", "").strip()
                # Optional: add book_number mapping here if needed for filtering

        all_chunks.extend(filtered_chunks)

    # Save & stats
    save_jsonl_to_file(all_chunks, out_file_wiki_chunks_character)

    results = chunk_statistics(all_chunks, "CHARACTERS CHUNKS")
    results["metrics"]["number_of_items"] = len(character_data)
    print_results(results, "")

    return results


def chunk_chapter_summary_pages():
    """
    Chunk the ~714 chapter summary wiki pages using hybrid strategy.
    Respects section structure + minimal semantic refinement for factual content.
    """
    chapter_data = load_json_from_file(in_file_wiki_chapter_summary)
    all_chunks = []

    # Get hybrid chunker configured for chapter summaries

    for filename, page_data in tqdm(chapter_data.items(), desc="Processing chapter summaries"):
        book_number = page_data["book_number"]
        book_title = page_data["book_title"]
        chapter_number = page_data["chapter_number"]
        chapter_title = page_data["chapter_title"]

        # === Build full page text with preserved headings ===
        page_parts = []
        for section in page_data.get("sections", []):
            section_title = section.get("title", "Untitled")
            content = section.get("content", "").strip()
            if content:
                page_parts.append(f"## {section_title}\n{content}")

        full_text = "\n\n".join([part for part in page_parts if part.strip()])

        if not full_text.strip():
            continue

        # === Hybrid chunking ===
        raw_chunks = _wiki_chapter_summary_chunker(full_text)

        # === Tiny chunk cleanup + metadata ===
        filtered_chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            temp_chunk = {
                "source": "wiki",
                "wiki_type": "chapter_summary",
                "book_number": book_number,
                "book_title": book_title,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "filename": filename,
                "temporal_order": book_number,
                "text": chunk_text,
                "section_title": "",  # Extract first heading
            }

            # Extract primary section title from chunk
            heading_match = re.search(r"^##\s+(.+?)$", chunk_text, flags=re.MULTILINE)
            if heading_match:
                temp_chunk["section_title"] = heading_match.group(1)

            # Tiny chunk merge
            if len(chunk_text) < 300:
                if filtered_chunks:
                    filtered_chunks[-1]["text"] += " " + chunk_text
                    if temp_chunk["section_title"]:
                        filtered_chunks[-1]["section_title"] = temp_chunk["section_title"]
                # else: rare leading tiny → keep
            else:
                filtered_chunks.append(temp_chunk)

        # === Final indexing ===
        total_chunks = len(filtered_chunks)
        for final_idx, chunk in enumerate(filtered_chunks):
            chunk["chunk_index"] = final_idx + 1
            chunk["total_chunks"] = total_chunks

        all_chunks.extend(filtered_chunks)

    # Save & stats
    save_jsonl_to_file(all_chunks, out_file_wiki_chunks_chapter_summary)

    results = chunk_statistics(all_chunks, "CHAPTER SUMMARY CHUNKS")
    results["metrics"]["number_of_items"] = len(chapter_data)
    print_results(results, "")

    return results


def chunk_chronology_pages():
    """
    Chunk the chronology wiki pages using hybrid strategy.
    Preserves temporal structure and tight event grouping.
    """
    chronology_data = load_json_from_file(in_file_wiki_chronology)
    all_chunks = []

    # Get hybrid chunker configured for chronology

    for filename, page_data in tqdm(chronology_data.items(), desc="Processing chronologies"):
        character_name = page_data["character_name"]

        # === Build full page text with preserved headings ===
        page_parts = []

        # Temporal sections (book-by-book)
        temporal_sections = sorted(page_data.get("temporal_sections", []), key=lambda x: x.get("book_number", 999))
        for section in temporal_sections:
            book_title = section.get("book_title", "Unknown Book")
            content = section.get("content", "").strip()
            if content:
                page_parts.append(f"## Chronology: {book_title}\n{content}")

        # Non-temporal sections (event-based)
        for section in page_data.get("non_temporal_sections", []):
            section_title = section.get("section_title", "Untitled Event")
            content = section.get("content", "").strip()

            # Combine subsections
            subsection_parts = []
            if content:
                subsection_parts.append(content)
            for subsection in section.get("subsections", []):
                sub_title = subsection.get("title", "")
                sub_content = subsection.get("content", "").strip()
                if sub_content:
                    subsection_parts.append(f"### {sub_title}\n{sub_content}")
            if subsection_parts:
                combined = "\n\n".join(subsection_parts)
                page_parts.append(f"## {section_title}\n{combined}")

        full_text = "\n\n".join([part for part in page_parts if part.strip()])

        if not full_text.strip():
            continue

        # === Hybrid chunking ===
        raw_chunks = _wiki_chronology_chunker(full_text)

        # === Tiny chunk cleanup + metadata ===
        filtered_chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            temp_chunk = {
                "source": "wiki",
                "wiki_type": "chronology",
                "character_name": character_name,
                "filename": filename,
                "text": chunk_text,
                "temporal_order": None,
                "book_title": None,
                "section_title": "",
            }

            # Extract section title (e.g., "Chronology: The Shadow Rising" or event name)
            heading_match = re.search(r"^##\s+(.+?)$", chunk_text, flags=re.MULTILINE)
            if heading_match:
                full_heading = heading_match.group(1)
                temp_chunk["section_title"] = full_heading

                # Infer temporal_order from book titles in chronology sections
                if full_heading.startswith("Chronology: "):
                    book_part = full_heading.replace("Chronology: ", "").strip()
                    # Optional: map book_part to book_number if needed
                    temp_chunk["book_title"] = book_part

            # Tiny chunk merge
            if len(chunk_text) < 300:
                if filtered_chunks:
                    filtered_chunks[-1]["text"] += " " + chunk_text
                    if temp_chunk["section_title"]:
                        filtered_chunks[-1]["section_title"] = temp_chunk["section_title"]
                    if temp_chunk["book_title"]:
                        filtered_chunks[-1]["book_title"] = temp_chunk["book_title"]
                # else: keep rare leading tiny
            else:
                filtered_chunks.append(temp_chunk)

        # === Final indexing ===
        total_chunks = len(filtered_chunks)
        for final_idx, chunk in enumerate(filtered_chunks):
            chunk["chunk_index"] = final_idx + 1
            chunk["total_chunks"] = total_chunks

            # Set temporal_order from book_title if available (for filtering)
            if chunk.get("book_title"):
                # You can add a book_title → book_number map here if needed
                # For now, keep as string or set to book_number if mapped
                pass

        all_chunks.extend(filtered_chunks)

    # Save & stats
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

    # Semantic chunking (current strategy)
    raw_chunks = _books_chunker(content)

    # === TINY CHUNK CLEANUP & METADATA ASSIGNMENT ===
    filtered_chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        # Temporary chunk object (index will be recalculated)
        temp_chunk = {
            "source": "book",
            "chunk_id": f"book_{book_number:02d}_ch_{chapter_number:02d}_chunk_{idx + 1:03d}",  # temporary ID
            "book_number": book_number,
            "book_title": book_title,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "chapter_type": chapter_type,
            "text": chunk_text,
            "temporal_order": book_number,
        }

        # Merge tiny chunks (< 300 chars) into previous chunk
        if len(chunk_text) < cfg_min_books_chunks_size_characters:
            if filtered_chunks:  # Merge into last chunk if exists
                filtered_chunks[-1]["text"] += " " + chunk_text
            # else: very rare leading tiny chunk → keep as-is (unlikely with semantic chunker)
        else:
            filtered_chunks.append(temp_chunk)

    # If the very last raw chunk was tiny and merged, it's already handled above

    # === Recalculate final indices and IDs ===
    final_total = len(filtered_chunks)
    for final_idx, chunk in enumerate(filtered_chunks):
        # Update human-readable fields
        chunk["chunk_index"] = final_idx + 1
        chunk["total_chunks_in_chapter"] = final_total
        # Regenerate clean chunk_id with correct index
        chunk["chunk_id"] = f"book_{book_number:02d}_ch_{chapter_number:02d}_chunk_{final_idx + 1:03d}"

    return filtered_chunks


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


def chunk_concept_pages():
    """
    Chunk concept, magic, and prophecy wiki pages using hybrid strategy.
    Handles stubs and long explanations appropriately.
    """
    # Process all three types with same logic
    types_to_process = [
        ("concept", in_file_wiki_concept, out_file_wiki_chunks_concept),
        ("prophecy", in_file_wiki_prophecies, out_file_wiki_chunks_prophecies),
        ("magic", in_file_wiki_magic, out_file_wiki_chunks_magic),
    ]

    all_results = []

    for source_type, input_file, output_file in types_to_process:
        data = load_json_from_file(input_file)
        all_chunks = []

        for filename, page_data in tqdm(data.items(), desc=f"Processing {source_type}"):
            page_name = page_data.get("page_name", "")
            page_type = page_data.get("page_type", "")
            categories = page_data.get("metadata", {}).get("categories", [])

            # === Build full page text with preserved headings ===
            page_parts = []
            for section in page_data.get("sections", []):
                section_title = section.get("title", "")
                content = section.get("content", "").strip()

                # Skip category sections
                if section_title.lower() in ["categories", "category"]:
                    continue

                section_parts = []
                if section_title and content:
                    section_parts.append(f"## {section_title}\n{content}")
                elif section_title:
                    section_parts.append(f"## {section_title}")
                elif content:
                    section_parts.append(content)

                for subsection in section.get("subsections", []):
                    sub_title = subsection.get("title", "")
                    sub_content = subsection.get("content", "").strip()
                    if sub_title and sub_content:
                        section_parts.append(f"### {sub_title}\n{sub_content}")
                    elif sub_title:
                        section_parts.append(f"### {sub_title}")
                    elif sub_content:
                        section_parts.append(sub_content)

                if section_parts:
                    page_parts.append("\n\n".join(section_parts))

            full_text = "\n\n".join(page_parts)

            if not full_text.strip():
                continue

            # === Hybrid chunking ===
            raw_chunks = _wiki_concept_chunker(full_text)

            # === Tiny chunk cleanup + metadata ===
            filtered_chunks = []
            for idx, chunk_text in enumerate(raw_chunks):
                temp_chunk = {
                    "source": "wiki",
                    "wiki_type": source_type,  # 'concept', 'magic', or 'prophecy'
                    "page_type": page_type,
                    "page_name": page_name,
                    "source_file": filename,
                    "text": chunk_text,
                    "temporal_order": None,
                    "section_title": "",
                    "categories": categories,
                }

                # Extract section title
                heading_match = re.search(r"^##\s+(.+?)$", chunk_text, flags=re.MULTILINE)
                if heading_match:
                    temp_chunk["section_title"] = heading_match.group(1)

                # Tiny chunk merge
                if len(chunk_text) < 300:
                    if filtered_chunks:
                        filtered_chunks[-1]["text"] += " " + chunk_text
                        if temp_chunk["section_title"]:
                            filtered_chunks[-1]["section_title"] = temp_chunk["section_title"]
                    # else: keep rare leading tiny
                else:
                    filtered_chunks.append(temp_chunk)

            # Final indexing
            total_chunks = len(filtered_chunks)
            for final_idx, chunk in enumerate(filtered_chunks):
                chunk["chunk_index"] = final_idx + 1
                chunk["total_chunks"] = total_chunks

            all_chunks.extend(filtered_chunks)

        # Save
        save_jsonl_to_file(all_chunks, output_file)

        results = chunk_statistics(all_chunks, f"{source_type.upper()} CHUNKS")
        results["metrics"]["number_of_items"] = len(data)
        print_results(results, "")
        all_results.append(results)

    return all_results


def main():
    start_time = datetime.now()

    statistics = []

    # statistics.append(chunk_books())
    statistics.append(chunk_character_pages())
    statistics.append(chunk_chapter_summary_pages())
    statistics.append(chunk_chronology_pages())
    statistics.extend(chunk_concept_pages())

    total_time = (datetime.now() - start_time).total_seconds()

    total_statistics_logging(total_time=total_time, log_name="emb_01_create_chunks", statistics=statistics, title="CHUNK CREATION", tables=True)


if __name__ == "__main__":
    paths = get_paths()

    cfg_max_chunk_size = config.MAX_CHUNK_SIZE
    cfg_min_books_chunks_size_characters = config.CHUNKING_STRATEGY["MIN_BOOKS_CHUNKS_SIZE_CHARACTERS"]

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
