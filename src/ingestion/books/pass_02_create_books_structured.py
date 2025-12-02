"""
Create books_structured.json with all processed book data.

Week 2 Session 2 - Dragon's Codex
Consolidates all 15 books into a single structured JSON file.

'output_path': 'data/processed/books_structured.json'

"""

import json
import os
from pathlib import Path
from datetime import datetime

def load_config():
    """Load basic configuration"""
    return {
        'books_json_path': 'data/raw/books',
        'output_path': 'data/processed/books_structured.json'
    }

def process_all_books(books_path: str) -> dict:
    """
    Load and structure all book data.
    
    Returns:
        Dictionary with all books and metadata
    """
    books = []
    stats = {
        'total_books': 0,
        'total_chapters': 0,
        'total_glossary_entries': 0,
        'processing_date': datetime.now().isoformat(),
        'errors': []
    }
    
    # Get all JSON book files
    book_files = sorted(Path(books_path).glob('*.json'))
    
    print(f"\nProcessing {len(book_files)} books...")
    print("=" * 70)
    
    for book_file in book_files:
        try:
            with open(book_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            book_num = book_data.get('book_number', 'unknown')
            book_name = book_data.get('book_name', 'unknown')
            chapters = book_data.get('chapters', [])
            glossary = book_data.get('glossary', [])
            
            # Calculate statistics for this book
            chapter_stats = {
                'total': len(chapters),
                'prologues': len([ch for ch in chapters if ch.get('type') == 'prologue']),
                'regular_chapters': len([ch for ch in chapters if ch.get('type') == 'chapter']),
                'epilogues': len([ch for ch in chapters if ch.get('type') == 'epilogue'])
            }
            
            # Calculate content statistics
            total_chars = sum(len(ch.get('content', '')) for ch in chapters)
            avg_chapter_length = total_chars // len(chapters) if chapters else 0
            
            # Create structured book object
            structured_book = {
                'book_number': book_num,
                'book_name': book_name,
                'metadata': {
                    'total_chapters': chapter_stats['total'],
                    'prologues': chapter_stats['prologues'],
                    'regular_chapters': chapter_stats['regular_chapters'],
                    'epilogues': chapter_stats['epilogues'],
                    'glossary_entries': len(glossary),
                    'total_characters': total_chars,
                    'average_chapter_length': avg_chapter_length,
                    'source_file': book_file.name
                },
                'chapters': chapters,
                'glossary': glossary
            }
            
            books.append(structured_book)
            
            # Update overall stats
            stats['total_books'] += 1
            stats['total_chapters'] += len(chapters)
            stats['total_glossary_entries'] += len(glossary)
            
            print(f"✅ Book {book_num:>2}: {book_name}")
            print(f"   Chapters: {chapter_stats['total']} | Glossary: {len(glossary)} | Avg length: {avg_chapter_length:,} chars")
            
        except Exception as e:
            error_msg = f"Error processing {book_file.name}: {str(e)}"
            print(f"❌ {error_msg}")
            stats['errors'].append(error_msg)
    
    return {
        'metadata': stats,
        'books': books
    }

def save_structured_books(data: dict, output_path: str):
    """Save structured books to JSON file"""
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save with indentation for readability
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Get file size
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    
    print(f"\n✅ Structured books saved to: {output_path}")
    print(f"   File size: {file_size:.2f} MB")

def print_summary(data: dict):
    """Print processing summary"""
    metadata = data['metadata']
    books = data['books']
    
    print("\n" + "=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Total books: {metadata['total_books']}")
    print(f"Total chapters: {metadata['total_chapters']}")
    print(f"Total glossary entries: {metadata['total_glossary_entries']}")
    print(f"Processing date: {metadata['processing_date']}")
    
    if metadata['errors']:
        print(f"\n⚠️  Errors: {len(metadata['errors'])}")
        for error in metadata['errors']:
            print(f"  - {error}")
    else:
        print("\n✅ No errors encountered")
    
    # Book breakdown
    print("\nBook breakdown:")
    for book in books:
        book_num = book['book_number']
        book_name = book['book_name']
        meta = book['metadata']
        print(f"  Book {book_num:>2}: {book_name}")
        print(f"          {meta['total_chapters']} chapters, {meta['glossary_entries']} glossary entries")

def validate_structure(data: dict) -> bool:
    """
    Validate the structured data meets requirements.
    
    Returns True if valid, False otherwise.
    """
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    issues = []
    
    # Check we have all 15 books
    if len(data['books']) != 15:
        issues.append(f"Expected 15 books, got {len(data['books'])}")
    
    # Check each book has required fields
    for book in data['books']:
        if 'book_number' not in book:
            issues.append(f"Book missing book_number: {book.get('book_name', 'unknown')}")
        if 'book_name' not in book:
            issues.append(f"Book {book.get('book_number', 'unknown')} missing book_name")
        if 'chapters' not in book:
            issues.append(f"Book {book.get('book_number', 'unknown')} missing chapters")
        if 'glossary' not in book:
            issues.append(f"Book {book.get('book_number', 'unknown')} missing glossary")
        if 'metadata' not in book:
            issues.append(f"Book {book.get('book_number', 'unknown')} missing metadata")
    
    # Check chapter count is in expected range
    total_chapters = data['metadata']['total_chapters']
    if not (700 <= total_chapters <= 800):
        issues.append(f"Total chapters ({total_chapters}) outside expected range (400-500)")
    
    if issues:
        print("⚠️  Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All validation checks passed!")
        return True

def main():
    """Main execution"""
    config = load_config()
    
    print("Dragon's Codex - Books Structured Generator")
    print("Week 2 Session 2")
    print("=" * 70)
    
    # Process all books
    data = process_all_books(config['books_json_path'])
    
    # Print summary
    print_summary(data)
    
    # Validate
    is_valid = validate_structure(data)
    
    # Save
    save_structured_books(data, config['output_path'])
    
    print("\n" + "=" * 70)
    if is_valid:
        print("✅ books_structured.json created successfully!")
    else:
        print("⚠️  books_structured.json created with validation warnings")
    print("=" * 70)

if __name__ == '__main__':
    main()