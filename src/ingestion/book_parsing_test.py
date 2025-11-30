"""
Dragon's Codex - Book Parsing Test
Tests parsing of book markdown files for chapter extraction.
"""

from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
import re


def load_book(book_path):
    """Load a book file"""
    with open(book_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_chapters_simple(content):
    """
    Simple chapter extraction using pattern matching.
    Adapts to the actual structure found in WoT books.
    """
    chapters = []
    
    # Pattern for: Chapter \n<number>\n*<title>*
    chapter_pattern = r'Chapter\s*\n\s*(\d+)\s*\n\s*\*([^*]+)\*'
    
    # Pattern for: Prologue\n*<title>*
    prologue_pattern = r'Prologue\s*\n\s*\*([^*]+)\*'
    
    # Pattern for: Epilogue\n*<title>*
    epilogue_pattern = r'Epilogue\s*\n\s*\*([^*]+)\*'
    
    # Find prologue
    prologue_match = re.search(prologue_pattern, content)
    if prologue_match:
        chapters.append({
            'type': 'prologue',
            'number': 0,
            'title': prologue_match.group(1).strip(),
            'position': prologue_match.start()
        })
    
    # Find regular chapters
    for match in re.finditer(chapter_pattern, content):
        chapters.append({
            'type': 'chapter',
            'number': int(match.group(1)),
            'title': match.group(2).strip(),
            'position': match.start()
        })
    
    # Find epilogue
    epilogue_match = re.search(epilogue_pattern, content)
    if epilogue_match:
        chapters.append({
            'type': 'epilogue',
            'number': 999,  # Special number for epilogue
            'title': epilogue_match.group(1).strip(),
            'position': epilogue_match.start()
        })
    
    # Sort by position
    chapters.sort(key=lambda x: x['position'])
    
    return chapters


def extract_glossary(content):
    """
    Extract glossary section and parse entries.
    """
    # Find glossary section
    glossary_match = re.search(r'Glossary\s*\n(.*)', content, re.DOTALL)
    
    if not glossary_match:
        return None
    
    glossary_text = glossary_match.group(1)
    
    # Pattern for: ***<term>*** <definition>
    entry_pattern = r'\*\*\*([^*]+)\*\*\*\s*([^\n*]+(?:\n(?!\*\*\*)[^\n*]+)*)'
    
    entries = []
    for match in re.finditer(entry_pattern, glossary_text):
        term = match.group(1).strip()
        definition = match.group(2).strip()
        entries.append({
            'term': term,
            'definition': definition
        })
    
    return {
        'entry_count': len(entries),
        'entries': entries[:10]  # First 10 for inspection
    }


def extract_chapter_content(content, chapters, chapter_index):
    """
    Extract the actual content of a specific chapter.
    """
    if chapter_index >= len(chapters):
        return None
    
    chapter = chapters[chapter_index]
    start_pos = chapter['position']
    
    # Find end position (start of next chapter or glossary)
    if chapter_index < len(chapters) - 1:
        end_pos = chapters[chapter_index + 1]['position']
    else:
        # Last chapter - goes until glossary or end
        glossary_match = re.search(r'Glossary\s*\n', content[start_pos:])
        if glossary_match:
            end_pos = start_pos + glossary_match.start()
        else:
            end_pos = len(content)
    
    chapter_content = content[start_pos:end_pos]
    
    return {
        'chapter': chapter,
        'content_length': len(chapter_content),
        'content_preview': chapter_content[:500] + "..." if len(chapter_content) > 500 else chapter_content
    }


def test_book_parsing(book_path):
    """
    Test parsing a single book file.
    """
    print(f"\n{'='*60}")
    print(f"Testing Book: {book_path.name}")
    print(f"{'='*60}\n")
    
    # Load book
    print("Loading book...", end=" ")
    content = load_book(book_path)
    print(f"✓ ({len(content):,} characters)")
    
    # Extract chapters
    print("Extracting chapters...", end=" ")
    chapters = extract_chapters_simple(content)
    print(f"✓ ({len(chapters)} chapters found)")
    
    # Display chapter list
    print("\nChapter List:")
    print("-" * 60)
    for ch in chapters[:5]:  # First 5
        print(f"  {ch['type'].title():12} {ch['number']:3}: {ch['title']}")
    if len(chapters) > 10:
        print(f"  ... ({len(chapters) - 10} more chapters)")
        for ch in chapters[-5:]:  # Last 5
            print(f"  {ch['type'].title():12} {ch['number']:3}: {ch['title']}")
    
    # Extract a sample chapter's content
    if len(chapters) >= 2:
        print("\nSample Chapter Content:")
        print("-" * 60)
        sample = extract_chapter_content(content, chapters, 1)  # First regular chapter
        print(f"  Chapter: {sample['chapter']['title']}")
        print(f"  Length: {sample['content_length']:,} characters")
        print(f"  Preview:\n{sample['content_preview'][:300]}...")
    
    # Extract glossary
    print("\nGlossary:")
    print("-" * 60)
    glossary = extract_glossary(content)
    if glossary:
        print(f"  ✓ Glossary found ({glossary['entry_count']} entries)")
        print(f"  Sample entries:")
        for entry in glossary['entries'][:5]:
            print(f"    - {entry['term']}: {entry['definition'][:60]}...")
    else:
        print("  ✗ No glossary found")
    
    return {
        'file': book_path.name,
        'content_length': len(content),
        'chapter_count': len(chapters),
        'has_prologue': any(ch['type'] == 'prologue' for ch in chapters),
        'has_epilogue': any(ch['type'] == 'epilogue' for ch in chapters),
        'glossary_entries': glossary['entry_count'] if glossary else 0
    }


def main():
    """
    Main test function.
    """
    print("=" * 60)
    print("Dragon's Codex - Book Parsing Test")
    print("=" * 60)
    
    # Find book files
    books_path = Path('data/raw/books')
    
    if not books_path.exists():
        print(f"\n✗ Books directory not found: {books_path}")
        print("  Please ensure books are in data/raw/books/")
        return
    
    book_files = list(books_path.glob('*.md')) + list(books_path.glob('*.txt'))
    
    if not book_files:
        print(f"\n✗ No book files found in {books_path}")
        return
    
    print(f"\nFound {len(book_files)} book files")
    
    # Test first book
    print("\n" + "=" * 60)
    print("Testing First Book (Detailed)")
    print("=" * 60)
    
    first_book = sorted(book_files)[0]
    result1 = test_book_parsing(first_book)
    
    # If more books exist, test one more
    if len(book_files) > 1:
        print("\n" + "=" * 60)
        print("Testing Second Book (Quick Check)")
        print("=" * 60)
        
        second_book = sorted(book_files)[1]
        result2 = test_book_parsing(second_book)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    print(f"\nTotal books found: {len(book_files)}")
    print(f"\nFirst book analysis:")
    print(f"  File: {result1['file']}")
    print(f"  Content: {result1['content_length']:,} characters")
    print(f"  Chapters: {result1['chapter_count']}")
    print(f"  Has Prologue: {result1['has_prologue']}")
    print(f"  Has Epilogue: {result1['has_epilogue']}")
    print(f"  Glossary entries: {result1['glossary_entries']}")
    
    print("\n✓ Book parsing test complete!")
    print("\nNext steps:")
    print("  1. Verify chapter patterns match your books")
    print("  2. Adjust regex patterns if needed")
    print("  3. Test with all 15 books")
    print("  4. Document any inconsistencies found")


if __name__ == "__main__":
    main()
