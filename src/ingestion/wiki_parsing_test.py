"""
Dragon's Codex - Wiki Parsing Test
Tests parsing of wiki markdown files for character and temporal sections.
"""

from pathlib import Path
import re
from collections import defaultdict


def load_wiki_file(wiki_path):
    """Load a wiki file"""
    with open(wiki_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_character_name(content, filename):
    """
    Extract character name from H1 header or filename.
    """
    # Try H1 header first
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    # Fallback to filename
    return filename.stem.replace('_', ' ').title()


def extract_temporal_sections(content):
    """
    Extract all "In [Book Name]" sections with their content.
    """
    temporal_sections = []
    
    # Pattern for "## In [Book Title]"
    pattern = r'##\s+In\s+(.+?)(?=\n##|\n#|$)'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        book_title = match.group(1).split('\n')[0].strip()
        
        # Get the full section content
        section_start = match.start()
        # Find next ## or # header
        next_header = re.search(r'\n##?\s+', content[match.end():])
        if next_header:
            section_end = match.end() + next_header.start()
        else:
            section_end = len(content)
        
        section_content = content[section_start:section_end]
        
        # Extract subsections within this temporal section
        subsections = extract_subsections(section_content)
        
        temporal_sections.append({
            'book_title': book_title,
            'content_length': len(section_content),
            'subsection_count': len(subsections),
            'subsections': subsections
        })
    
    return temporal_sections


def extract_subsections(section_content):
    """
    Extract subsections (### headers) within a section.
    """
    subsections = []
    
    # Pattern for ### headers
    pattern = r'###\s+(.+?)(?=\n###|\n##|\n#|$)'
    
    for match in re.finditer(pattern, section_content, re.DOTALL):
        title = match.group(1).split('\n')[0].strip()
        subsections.append(title)
    
    return subsections


def extract_non_temporal_sections(content):
    """
    Extract sections that are not "In [Book]" - like Abilities, Relationships, etc.
    """
    non_temporal = []
    
    # All ## headers
    all_h2 = re.finditer(r'##\s+(.+?)$', content, re.MULTILINE)
    
    for match in all_h2:
        section_title = match.group(1).strip()
        
        # Skip temporal sections
        if section_title.startswith('In '):
            continue
        
        # Get section content
        section_start = match.start()
        next_h2 = re.search(r'\n##\s+', content[match.end():])
        if next_h2:
            section_end = match.end() + next_h2.start()
        else:
            section_end = len(content)
        
        section_content = content[section_start:section_end]
        
        non_temporal.append({
            'title': section_title,
            'content_length': len(section_content),
            'preview': section_content[:200].strip()
        })
    
    return non_temporal


def map_book_title_to_number(book_title):
    """
    Map book title to number.
    This is a simple version - will be replaced with wot_constants.py later.
    """
    book_mapping = {
        'New Spring': 0,
        'The Eye of the World': 1,
        'The Great Hunt': 2,
        'The Dragon Reborn': 3,
        'The Shadow Rising': 4,
        'The Fires of Heaven': 5,
        'Lord of Chaos': 6,
        'A Crown of Swords': 7,
        'The Path of Daggers': 8,
        "Winter's Heart": 9,
        'Crossroads of Twilight': 10,
        'Knife of Dreams': 11,
        'The Gathering Storm': 12,
        'Towers of Midnight': 13,
        'A Memory of Light': 14,
    }
    
    return book_mapping.get(book_title, -1)


def test_wiki_parsing(wiki_path):
    """
    Test parsing a single wiki file.
    """
    print(f"\n{'='*60}")
    print(f"Testing Wiki: {wiki_path.name}")
    print(f"{'='*60}\n")
    
    # Load wiki
    print("Loading wiki file...", end=" ")
    content = load_wiki_file(wiki_path)
    print(f"✓ ({len(content):,} characters)")
    
    # Extract character name
    print("Extracting character name...", end=" ")
    char_name = extract_character_name(content, wiki_path)
    print(f"✓ '{char_name}'")
    
    # Extract temporal sections
    print("Extracting temporal sections...", end=" ")
    temporal = extract_temporal_sections(content)
    print(f"✓ ({len(temporal)} book sections found)")
    
    # Display temporal sections
    if temporal:
        print("\nTemporal Sections (Book Appearances):")
        print("-" * 60)
        for section in temporal:
            book_num = map_book_title_to_number(section['book_title'])
            print(f"  Book {book_num:2}: {section['book_title']}")
            print(f"           {section['content_length']:,} chars, "
                  f"{section['subsection_count']} subsections")
            if section['subsections']:
                for subsec in section['subsections'][:3]:
                    print(f"             - {subsec}")
                if len(section['subsections']) > 3:
                    print(f"             ... and {len(section['subsections'])-3} more")
    
    # Extract non-temporal sections
    print("\nNon-Temporal Sections:")
    print("-" * 60)
    non_temporal = extract_non_temporal_sections(content)
    if non_temporal:
        for section in non_temporal:
            print(f"  {section['title']}")
            print(f"    {section['content_length']:,} characters")
            print(f"    Preview: {section['preview'][:100]}...")
            print()
    else:
        print("  None found")
    
    return {
        'file': wiki_path.name,
        'character': char_name,
        'content_length': len(content),
        'temporal_sections': len(temporal),
        'non_temporal_sections': len(non_temporal),
        'books_appeared': [map_book_title_to_number(t['book_title']) 
                          for t in temporal]
    }


def main():
    """
    Main test function.
    """
    print("=" * 60)
    print("Dragon's Codex - Wiki Parsing Test")
    print("=" * 60)
    
    # Find wiki files
    wiki_path = Path('data/raw/wiki')
    
    if not wiki_path.exists():
        print(f"\n✗ Wiki directory not found: {wiki_path}")
        print("  Please ensure wiki files are in data/raw/wiki/")
        return
    
    wiki_files = list(wiki_path.glob('*.md'))
    
    if not wiki_files:
        print(f"\n✗ No wiki files found in {wiki_path}")
        return
    
    print(f"\nFound {len(wiki_files)} wiki files")
    
    # Test a few sample characters
    test_characters = [
        'Rand_al\'Thor',
        'Egwene_al\'Vere',
        'Moiraine_Damodred',
        'Perrin_Aybara',
        'Mat_Cauthon'
    ]
    
    results = []
    
    for char_file in test_characters:
        # Find file (may have different naming)
        matching_files = [f for f in wiki_files if char_file.lower() in f.stem.lower()]
        
        if matching_files:
            result = test_wiki_parsing(matching_files[0])
            results.append(result)
        else:
            print(f"\n⚠ Could not find wiki file for {char_file}")
    
    # If no matching files found, just test the first few
    if not results:
        print("\n" + "=" * 60)
        print("Testing First Available Wiki Files")
        print("=" * 60)
        
        for wiki_file in sorted(wiki_files)[:3]:
            result = test_wiki_parsing(wiki_file)
            results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    print(f"\nTotal wiki files found: {len(wiki_files)}")
    print(f"Files tested: {len(results)}")
    
    if results:
        print("\nCharacters analyzed:")
        for r in results:
            print(f"\n  {r['character']}")
            print(f"    Content: {r['content_length']:,} characters")
            print(f"    Appears in {r['temporal_sections']} books: "
                  f"{sorted([b for b in r['books_appeared'] if b >= 0])}")
            print(f"    Non-temporal sections: {r['non_temporal_sections']}")
    
    print("\n✓ Wiki parsing test complete!")
    print("\nNext steps:")
    print("  1. Verify book title patterns match your wiki")
    print("  2. Check that all major characters have expected book appearances")
    print("  3. Document any book title variations found")
    print("  4. Test with more wiki files to find edge cases")


if __name__ == "__main__":
    main()
