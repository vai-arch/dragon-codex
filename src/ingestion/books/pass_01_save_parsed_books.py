"""
Complete Book Processing Pipeline

USES book_parser.py

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
    └── books/
│       ├── book_00_parsed.json             # ← With metadata
│       ├── book_01_parsed.json
│       ├── ...
│       ├── books_all_parsed.json           # ← All books combined
│       └── all_chapters.json               # ← All chapters flat
└── metadata/
    └── books/
        └──unified_glossary.json        # ← Unique terms
"""

import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from src.utils.config import get_config
from src.utils.util_files_functions import (
    find_files_in_folder,
    load_txt_line_by_line,
    save_json_to_file,
)
from src.utils.util_statistics import total_statistics_logging

in_raw_books_folder = ""
out_auxiliary_books_folder = ""


def parse_txt_to_json() -> int:
    """
    Parse all raw TXT book files to JSON format

    Args:
        books_path: Path to books directory

    Returns:
        Number of books processed
    """

    filenames = find_files_in_folder(in_raw_books_folder, ".txt")

    statistics = []

    for filename in tqdm(filenames, desc="Processing txt files"):
        # Get basename to handle paths
        filename_base = Path(filename).name

        # Parse book number and name from filename
        book_parts = filename_base.split("-", 1)
        book_number = book_parts[0].strip()
        if len(book_parts) > 1:
            book_name = book_parts[1].rstrip(".txt").strip()
        else:
            book_name = ""

        lines = load_txt_line_by_line(filename, False)

        # Initialize structures
        data = {
            "book_number": book_number,
            "book_name": book_name,
            "chapters": [],
            "glossary": [],
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
                current_chapter = {
                    "number": chapter_num,
                    "type": "prologue",
                    "title": "",
                    "content": "",
                }
                i += 1
                # Skip blank lines to title
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    current_chapter["title"] = lines[i].strip().strip("*").strip()
                i += 1
                # Skip blank lines to content
                while i < len(lines) and not lines[i].strip():
                    i += 1
                continue

            elif stripped == "CHAPTER":
                if current_section == "chapter" and current_chapter:
                    current_chapter["content"] = "".join(chapter_content).strip()
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
                current_chapter = {
                    "number": chapter_num,
                    "type": "chapter",
                    "title": "",
                    "content": "",
                }
                i += 1
                # Skip blank lines to title
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    current_chapter["title"] = lines[i].strip().strip("*").strip()
                i += 1
                # Skip blank lines to content
                while i < len(lines) and not lines[i].strip():
                    i += 1
                current_section = "chapter"
                continue

            elif stripped == "EPILOGUE":
                if current_section == "chapter" and current_chapter:
                    current_chapter["content"] = "".join(chapter_content).strip()
                    data["chapters"].append(current_chapter)
                    chapter_content = []

                chapter_num = max_chapter_num + 1
                current_chapter = {
                    "number": chapter_num,
                    "type": "epilogue",
                    "title": "",
                    "content": "",
                }
                i += 1
                # Skip blank lines to title
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    current_chapter["title"] = lines[i].strip().strip("*").strip()
                i += 1
                # Skip blank lines to content
                while i < len(lines) and not lines[i].strip():
                    i += 1
                current_section = "chapter"
                continue

            elif stripped == "GLOSSARY":
                if current_section == "chapter" and current_chapter:
                    current_chapter["content"] = "".join(chapter_content).strip()
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
            current_chapter["content"] = "".join(chapter_content).strip()
            data["chapters"].append(current_chapter)
        elif current_section == "glossary":
            current_term = None
            term_description = []

            for line in glossary_lines:
                if line.strip().startswith("> "):
                    # Save previous term
                    if current_term:
                        current_term["description"] = "".join(term_description).strip()
                        data["glossary"].append(current_term)
                        term_description = []

                    raw = line.strip()[2:].strip()

                    # Step 1: Extract bold term, optional colon after bold
                    term_match = re.match(r"^\*\*(.+?)\*\*\s*:?\s*(.*)", raw)
                    if term_match:
                        term_name = term_match.group(1).strip().rstrip("::")
                        rest = term_match.group(2).strip()
                    else:
                        term_name = None
                        rest = raw

                    # Step 2: Check for pronunciation (parentheses)
                    pronunciation = ""
                    description = rest

                    # Only match parentheses if they are at the very start of `rest`
                    pron_match = re.match(r"^\(([^)]+)\)\s*[:\-]?\s*(.*)$", rest)

                    # # Unescape parentheses so we can match them normally
                    # rest_unescaped = rest.replace("\\(", "(").replace("\\)", ")")

                    if pron_match:
                        pronunciation = pron_match.group(1).strip().rstrip("\\")
                        description = pron_match.group(2).strip()
                    else:
                        base_term = ""

                    final_term = term_name or base_term or rest

                    current_term = {"term": final_term, "pronunciation": pronunciation}

                    if description:
                        term_description.append(description + "\n")
                else:
                    # Continuation line
                    if current_term:
                        term_description.append(line.strip() + "\n")

        output_path = out_auxiliary_books_folder / filename.name.replace(".txt", ".json")

        save_json_to_file(data, output_path, 2, False)

        statistic = {
            "name": output_path.name,
            "metrics": {
                "chapters": len(data["chapters"]),
                "glossary_entries": len(data["glossary"]),
            },
        }

        statistics.append(statistic)

    return statistics


def main():
    start_time = datetime.now()

    statistics = parse_txt_to_json()

    total_time = (datetime.now() - start_time).total_seconds()

    total_statistics_logging(statistics, total_time, "PARSING RAW BOOKS", "raw_books_parsing")


if __name__ == "__main__":
    config = get_config()
    in_raw_books_folder = config.BOOKS_PATH
    out_auxiliary_books_folder = config.AUXILIARY_BOOKS_PATH

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace  # noqa: F821
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
