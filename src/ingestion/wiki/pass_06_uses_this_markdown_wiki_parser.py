"""
Dragon's Codex - Wiki Markdown Parser
Parses wiki markdown files with page type-specific strategies.

Page Types:
1. CHRONOLOGY: 5 files with ## Book Title sections
2. CHARACTER: ~2,451 files with ## Activities → ### Book/Event
3. CHAPTER_SUMMARY: 714 files with chapter metadata
4. CONCEPT: ~3,368 files with topic-based sections
5. REDIRECT/SKIP: ~3,178 files (redirects + no categories)
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from src.utils.wot_constants import BOOK_TITLES, TITLE_TO_NUMBER
from src.utils.util_files_functions import load_text_from_file
from src.utils.wiki_constants import REDIRECT_CATEGORIES, CATEGORIES_TO_SKIP, PROPHECIES_CATEGORIES, MAGIC_CATEGORIES, extract_categories, extract_id


def classify_page_type(filename: str, categories: List[str]) -> str:
    """
    Classify wiki page type based on filename and categories.
    
    Args:
        filename: Wiki file name
        categories: List of page categories
        
    Returns:
        str: One of: 'SKIP', 'CHRONOLOGY', 'CHARACTER', 'CHAPTER_SUMMARY', 'PROPHECIES', 'MAGIC', 'CONCEPT'
    """
     
    # Skip files with no categories
    if not categories:
        return 'SKIP'
    
    # Skip disambiguation pages
    if any(cat in CATEGORIES_TO_SKIP for cat in categories):
        return 'SKIP'
    
    # Skip redirect pages
    if any(cat in REDIRECT_CATEGORIES for cat in categories):
        return 'SKIP'
    
    # Chronology pages
    if 'Character_Chronologies' in categories:
        return 'CHRONOLOGY'
    
    # Character pages (~2,451 files)
    if 'Men' in categories or 'Women' in categories:
        return 'CHARACTER'
    
    # Chapter summary pages (714 files)
    if 'Chapter_summaries' in categories:
        return 'CHAPTER_SUMMARY'

    # Skip redirect pages
    if any(cat in PROPHECIES_CATEGORIES for cat in categories):
        return 'PROPHECIES'
       
   # Skip redirect pages
    if any(cat in MAGIC_CATEGORIES for cat in categories):
        return 'MAGIC'
       
    # Everything else is a concept/place/event page
    return 'CONCEPT'


def extract_character_name(filename: str, content: str) -> str:
    """
    Extract character name from filename or H1 header.
    
    Args:
        filename: Wiki filename (e.g., "Rand_al'Thor.txt")
        content: File content
        
    Returns:
        str: Character name (e.g., "Rand al'Thor")
    """
    # First try H1 header
    h1_match = re.search(r'^#\s+(.+?)(?:/Chronology)?\s*$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    # Fall back to filename
    # Remove .txt extension and replace underscores with spaces
    name = filename.replace('.txt', '').replace('_', ' ')
    # Remove /Chronology suffix if present
    name = name.replace('/Chronology', '')
    return name


def is_book_section(section_title: str) -> Tuple[bool, Optional[int]]:
    """
    Check if section title matches a book title.
    
    Args:
        section_title: Section header text
        
    Returns:
        tuple: (is_book_section, book_number or None)
    """
    section_clean = section_title.strip()
    
    if section_clean in TITLE_TO_NUMBER:
        return True, TITLE_TO_NUMBER[section_clean]
    
    return False, None


def extract_metadata(filepath, content: str) -> Dict: 
    """
    Extract metadata from wiki page header.
    
    Args:
        content: File content
        
    Returns:
        dict: Metadata including page_id and categories
    """
    metadata = {}
    
    metadata['page_id'] = extract_id(content)
    metadata['categories'] = extract_categories(filepath, content)

    return metadata


def parse_markdown_structure(content: str) -> List[Dict]:
    """
    Parse markdown content into structured sections using simple line-by-line parsing.
    This captures 100% of content - every single line.
    
    Args:
        content: Markdown content
        
    Returns:
        list: List of section dictionaries with hierarchy
    """
    lines = content.split('\n')
    sections = []
    current_h2 = None
    current_h3 = None
    
    for line in lines:
        # Skip metadata comments
        if line.strip().startswith('<!--'):
            continue
        
        # Skip horizontal rules
        if line.strip() in ['---', '***', '___']:
            continue
        
        # Check for ## header (h2)
        if line.startswith('## '):
            # Save previous h2 section if exists
            if current_h2:
                # Clean up trailing empty content
                current_h2['content'] = current_h2['content'].strip()
                for subsection in current_h2['subsections']:
                    subsection['content'] = subsection['content'].strip()
                sections.append(current_h2)
            
            # Start new h2 section
            current_h2 = {
                'level': 2,
                'title': line.replace('## ', '').strip(),
                'content': '',
                'subsections': []
            }
            current_h3 = None
        
        # Check for ### header (h3)
        elif line.startswith('### ') and current_h2:
            # Start new h3 subsection
            current_h3 = {
                'level': 3,
                'title': line.replace('### ', '').strip(),
                'content': ''
            }
            current_h2['subsections'].append(current_h3)
        
        # Check for # header (h1) - skip it, we don't need it
        elif line.startswith('# '):
            continue
        
        # Regular content line
        else:
            if current_h2:
                # Add content to current section or subsection
                if current_h3:
                    # We're inside a ### subsection
                    current_h3['content'] += line + '\n'
                else:
                    # We're inside a ## section but no ### yet
                    current_h2['content'] += line + '\n'
    
    # Save final h2 section if exists
    if current_h2:
        current_h2['content'] = current_h2['content'].strip()
        for subsection in current_h2['subsections']:
            subsection['content'] = subsection['content'].strip()
        sections.append(current_h2)
    
    return sections


def parse_chronology_page(filepath: Path, content: str, metadata: Dict) -> Dict:
    """
    Parse chronology page with ## Book Title sections.
    
    Structure:
    # Character/Chronology
    ## The Eye of the World
    [content]
    ## The Great Hunt
    [content]
    
    Args:
        filepath: Path to file
        content: File content
        metadata: Extracted metadata
        
    Returns:
        dict: Parsed page data
    """
    character_name = extract_character_name(filepath.name, content)
    sections = parse_markdown_structure(content)
    
    # Process sections - h2 headers should be book titles
    temporal_sections = []
    non_temporal_sections = []
    
    for section in sections:
        if section['level'] == 2:
            is_book, book_num = is_book_section(section['title'])
            
            if is_book:
                temporal_sections.append({
                    'type': 'temporal',
                    'book_number': book_num,
                    'book_title': section['title'],
                    'content': section['content'],
                    'subsections': section.get('subsections', [])
                })
            else:
                # Non-book sections (e.g., "Overview", "The fight with the Shadow")
                non_temporal_sections.append({
                    'type': 'non_temporal',
                    'section_title': section['title'],
                    'content': section['content'],
                    'subsections': section.get('subsections', [])
                })
    
    return {
        'filename': filepath.name,
        'page_type': 'CHRONOLOGY',
        'character_name': character_name,
        'page_name': character_name,
        'metadata': metadata,
        'temporal_sections': temporal_sections,
        'non_temporal_sections': non_temporal_sections
    }


def parse_character_page(filepath: Path, content: str, metadata: Dict) -> Dict:
    """
    Parse character page with ## Activities → ### Book/Event sections.
    
    Structure:
    # Character Name
    ## Overview
    ## Appearance
    ## Activities
       ### The Great Hunt
       ### Becoming the Prophet
    
    Args:
        filepath: Path to file
        content: File content
        metadata: Extracted metadata
        
    Returns:
        dict: Parsed page data
    """
    character_name = extract_character_name(filepath.name, content)
    sections = parse_markdown_structure(content)
    
    temporal_sections = []
    non_temporal_sections = []
    
    # Find "Activities" section
    activities_section = None
    for section in sections:
        if section['level'] == 2 and section['title'].lower() == 'activities':
            activities_section = section
            break
    
    if activities_section and 'subsections' in activities_section:
        # Process ### subsections under Activities
        for subsection in activities_section['subsections']:
            is_book, book_num = is_book_section(subsection['title'])
            
            if is_book:
                temporal_sections.append({
                    'type': 'temporal',
                    'book_number': book_num,
                    'book_title': subsection['title'],
                    'content': subsection['content']
                })
            else:
                # Event-based section (not a book)
                temporal_sections.append({
                    'type': 'event',
                    'event_title': subsection['title'],
                    'content': subsection['content']
                })
    
    # Collect all other ## sections as non-temporal
    for section in sections:
        if section['level'] == 2 and section['title'].lower() != 'activities':
            non_temporal_sections.append({
                'type': 'non_temporal',
                'section_title': section['title'],
                'content': section['content'],
                'subsections': section.get('subsections', [])
            })
    
    return {
        'filename': filepath.name,
        'page_type': 'CHARACTER',
        'character_name': character_name,
        'page_name': character_name,
        'metadata': metadata,
        'temporal_sections': temporal_sections,
        'non_temporal_sections': non_temporal_sections
    }


def parse_chapter_summary_page(filepath: Path, content: str, metadata: Dict) -> Dict:
    """
    Parse chapter summary page.
    
    Args:
        filepath: Path to file
        content: File content
        metadata: Extracted metadata
        
    Returns:
        dict: Parsed page data with chapter metadata
    """
    # Extract book from categories
    # e.g., "The_Eye_of_the_World_chapter_summaries" → book 1
    book_number = None
    book_title = None
    
    for category in metadata.get('categories', []):
        if category.endswith('_chapter_summaries'):
            # Remove "_chapter_summaries" suffix
            book_cat = category.replace('_chapter_summaries', '').replace('_', ' ')
            # Try to match to book title
            for num, title in BOOK_TITLES.items():
                if title.lower() == book_cat.lower():
                    book_number = num
                    book_title = title
                    break
    
    # Extract chapter number and title from filename or H1
    chapter_match = re.search(r'Chapter[_\s]+(\d+)', filepath.name, re.IGNORECASE)
    chapter_number = int(chapter_match.group(1)) if chapter_match else None
    
    # Get chapter title from H1
    h1_match = re.search(r'^#\s+(.+?)\s*$', content, re.MULTILINE)
    chapter_title = h1_match.group(1).strip() if h1_match else None
    
    # Parse content sections
    sections = parse_markdown_structure(content)
    
    return {
        'filename': filepath.name,
        'page_type': 'CHAPTER_SUMMARY',
        'page_name': chapter_title,
        'book_number': book_number,
        'book_title': book_title,
        'chapter_number': chapter_number,
        'chapter_title': chapter_title,
        'metadata': metadata,
        'sections': sections
    }


def parse_concept_page(filepath: Path, content: str, metadata: Dict, concept_type: str) -> Dict:
    """
    Parse concept/place/event page (topic-based, no temporal structure).
    
    Args:
        filepath: Path to file
        content: File content
        metadata: Extracted metadata
        
    Returns:
        dict: Parsed page data
    """
    # Get page name from H1 or filename
    h1_match = re.search(r'^#\s+(.+?)\s*$', content, re.MULTILINE)
    page_name = h1_match.group(1).strip() if h1_match else filepath.name.replace('.txt', '').replace('_', ' ')
    
    # Parse all sections
    sections = parse_markdown_structure(content)
    
    return {
        'filename': filepath.name,
        'page_type': concept_type,
        'page_name': page_name,
        'metadata': metadata,
        'sections': sections
    }


def parse_wiki_file(filepath: Path, categories: List[str]) -> Optional[Dict]:
    """
    Parse a wiki file based on its page type.
    
    Args:
        filepath: Path to wiki .txt file
        categories: List of page categories (from category analysis)
        
    Returns:
        dict: Parsed page data, or None if page should be skipped
    """
    # Classify page type
    page_type = classify_page_type(filepath.name, categories)
    
    if page_type == 'SKIP':
        return None
    
    #read file content
    content = load_text_from_file(filepath)
    
    # Extract metadata
    metadata = extract_metadata(filepath, content)
    
    # Parse based on page type
    if page_type == 'CHRONOLOGY':
        return parse_chronology_page(filepath, content, metadata)
    elif page_type == 'CHARACTER':
        return parse_character_page(filepath, content, metadata)
    elif page_type == 'CHAPTER_SUMMARY':
        return parse_chapter_summary_page(filepath, content, metadata)
    elif page_type == 'PROPHECIES':
        return parse_concept_page(filepath, content, metadata, concept_type='PROPHECIES')
    elif page_type == 'MAGIC':
        return parse_concept_page(filepath, content, metadata, concept_type='MAGIC')
    elif page_type == 'CONCEPT':
        return parse_concept_page(filepath, content, metadata, concept_type='CONCEPT')
    
    return None


def main():
    """Test the parser on sample files."""
    import sys
    
    # print("\nUsage: python markdown_wiki_parser.py <wiki_file> <categories_json>")
    # print("\nExample:")
    # print("  python markdown_wiki_parser.py wiki/Rand_al'Thor.txt category_mappings.json")
    import sys
    
    from src.utils.config import Config
    from src.utils.logger import get_logger

    if len(sys.argv) < 3:
        wiki_file = Config().WIKI_PATH / "Two_Rivers.txt"
        categories_json = Config().FILE_FILENAME_TO_CATEGORIES
    else:
        wiki_file = Path(sys.argv[1])
        categories_json = Path(sys.argv[2])
    
    # Load categories
    with open(categories_json, 'r') as f:
        filename_to_categories = json.load(f)
    
    categories = filename_to_categories.get(wiki_file.name, [])
    
    print(f"\n{'='*80}")
    print(f"Parsing: {wiki_file.name}")
    print(f"Categories: {categories}")
    print(f"{'='*80}\n")
    
    # Parse file
    result = parse_wiki_file(wiki_file, categories)
    
    if result is None:
        print("⏭️  File skipped (redirect or no content)")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
