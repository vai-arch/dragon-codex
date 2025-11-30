import json
import re
import os
import glob
from pathlib import Path
from src.utils.config import Config

config = Config()
folder = Path(config.BOOKS_PATH)

filenames = sorted(glob.glob(os.path.join(folder, '*.txt')))

for filename in filenames:
    # Get basename to handle paths
    filename_base = os.path.basename(filename)

    # Parse book number and name from filename
    book_parts = filename_base.split('-', 1)
    book_number = book_parts[0].strip()
    if len(book_parts) > 1:
        book_name = book_parts[1].rstrip('.txt').strip()
    else:
        book_name = ''

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

                raw = line.strip()[2:].strip() # Keep formatting symbols

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
                    # No pronunciation → rest is description
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


    # Write to JSON
    output_filename = filename.replace('.txt', '.json')
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"JSON file created: {output_filename}")