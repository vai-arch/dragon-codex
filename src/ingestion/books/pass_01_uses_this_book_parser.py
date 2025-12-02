"""
Book Parser Module
Parses WoT book JSON files and extracts structured data with metadata

Based on parse_all_books.py but as a reusable class
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.wot_constants import BOOK_TITLES

logger = get_logger(__name__)


class BookParser:
    """
    Parses WoT book JSON files into structured format
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize parser
        
        Args:
            config: Configuration object (uses default if None)
        """
        self.config = config or Config()
        self.books_path = Path(self.config.BOOKS_PATH)
        logger.info(f"BookParser initialized. Books path: {self.books_path}")
    
    def load_book_json(self, book_number: int) -> Optional[Dict]:
        """
        Load a book's JSON file in ${BOOKS_PATH}
        
        Args:
            book_number: Book number (0-14)
        
        Returns:
            dict with book data, or None if not found
        """
        # Try different filename patterns
        patterns = [
            f"{book_number:02d}-*.json",  # 00-New_Spring.json
            f"{book_number}-*.json"        # 0-New_Spring.json
        ]
        
        for pattern in patterns:
            files = list(self.books_path.glob(pattern))
            if files:
                book_file = files[0]
                logger.info(f"Loading book {book_number}: {book_file.name}")
                
                with open(book_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return data
        
        logger.warning(f"Book {book_number} not found")
        return None
    
    def parse_book(self, book_number: int) -> Optional[Dict]:
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
        book_data = self.load_book_json(book_number)
        if not book_data:
            return None
        
        # Build metadata
        metadata = {
            'book_number': book_number,
            'book_title': BOOK_TITLES.get(book_number, book_data.get('book_name', '')),
            'book_name_file': book_data.get('book_name', ''),
            'total_chapters': len(book_data.get('chapters', [])),
            'has_prologue': any(ch['type'] == 'prologue' for ch in book_data.get('chapters', [])),
            'has_epilogue': any(ch['type'] == 'epilogue' for ch in book_data.get('chapters', [])),
            'glossary_entries': len(book_data.get('glossary', []))
        }
        
        # Process chapters with metadata
        chapters = []
        for chapter in book_data.get('chapters', []):
            chapter_with_meta = {
                'chapter_number': chapter['number'],
                'chapter_type': chapter['type'],
                'chapter_title': chapter['title'],
                'content': chapter['content'],
                'metadata': {
                    'book_number': book_number,
                    'book_title': metadata['book_title'],
                    'temporal_order': book_number,  # For filtering
                    'content_length': len(chapter['content']),
                    'word_count': len(chapter['content'].split())
                }
            }
            chapters.append(chapter_with_meta)
        
        # Process glossary with metadata
        glossary = []
        for entry in book_data.get('glossary', []):
            glossary_with_meta = {
                'term': (
                    " ".join(entry['term']) if isinstance(entry['term'], list)
                    else str(entry['term'])
                ).rstrip(":"),  # remove trailing colon
                'pronunciation': entry.get('pronunciation', ''),
                'description': entry.get('description', ''),
                'metadata': {
                    'book_number': book_number,
                    'book_title': metadata['book_title'],
                    'source': 'book_glossary'
                }
            }
            glossary.append(glossary_with_meta)
        
        result = {
            'book_metadata': metadata,
            'chapters': chapters,
            'glossary': glossary
        }
        
        logger.info(f"Parsed book {book_number}: {metadata['total_chapters']} chapters, "
                   f"{metadata['glossary_entries']} glossary entries")
        
        return result
    
    def parse_all_books(self) -> List[Dict]:
        """
        Parse all 15 books
        
        Returns:
            list of parsed book dicts
        """
        logger.info("Parsing all books (0-14)...")
        
        all_books = []
        for book_num in range(15):
            book_data = self.parse_book(book_num)
            if book_data:
                all_books.append(book_data)
            else:
                logger.warning(f"Skipped book {book_num} (not found)")
        
        logger.info(f"Successfully parsed {len(all_books)} books")
        return all_books
    
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
        
        for chapter in book_data['chapters']:
            if chapter['chapter_number'] == chapter_number:
                return chapter
        
        return None
    
    def get_all_chapters_flat(self) -> List[Dict]:
        """
        Get all chapters from all books as flat list
        
        Returns:
            list of all chapter dicts with metadata
        """
        logger.info("Extracting all chapters from all books...")
        
        all_chapters = []
        all_books = self.parse_all_books()
        
        for book in all_books:
            all_chapters.extend(book['chapters'])
        
        logger.info(f"Extracted {len(all_chapters)} total chapters")
        return all_chapters
    
    def get_all_glossary_terms(self) -> List[Dict]:
        """
        Get all glossary entries from all books
        
        Returns:
            list of all glossary entries with metadata
        """
        logger.info("Extracting all glossary terms from all books...")
        
        all_glossary = []
        all_books = self.parse_all_books()
        
        for book in all_books:
            all_glossary.extend(book['glossary'])
        
        logger.info(f"Extracted {len(all_glossary)} total glossary entries")
        return all_glossary
    
    def build_unified_glossary(self) -> Dict[str, Dict]:
        """
        Build unified glossary with all sources tracked
        
        Returns:
            dict mapping term to {definition, pronunciation, sources[]}
        """
        logger.info("Building unified glossary...")
        
        unified = {}
        all_glossary = self.get_all_glossary_terms()
        
        for entry in all_glossary:
            term = entry['term']
            
            if term not in unified:
                unified[term] = {
                    'term': term,
                    'pronunciation': entry['pronunciation'],
                    'definition': entry['description'],
                    'sources': []
                }
            
            # Track which books mention this term
            source_info = {
                'book_number': entry['metadata']['book_number'],
                'book_title': entry['metadata']['book_title']
            }
            if source_info not in unified[term]['sources']:
                unified[term]['sources'].append(source_info)
        
        logger.info(f"Built unified glossary with {len(unified)} unique terms")
        return unified


def main():
    """Test the parser"""
    from src.utils.logger import setup_logging
    
    setup_logging()
    logger.info("="*70)
    logger.info("Testing BookParser")
    logger.info("="*70)
    
    parser = BookParser()
    
    # Test: Parse book 1
    print("\nTest 1: Parse Book 1 (Eye of the World)")
    print("-"*70)
    book1 = parser.parse_book(1)
    
    if book1:
        meta = book1['book_metadata']
        print(f"✓ Title: {meta['book_title']}")
        print(f"✓ Chapters: {meta['total_chapters']}")
        print(f"✓ Prologue: {meta['has_prologue']}")
        print(f"✓ Epilogue: {meta['has_epilogue']}")
        print(f"✓ Glossary entries: {meta['glossary_entries']}")
        
        # Show first chapter
        first_ch = book1['chapters'][0]
        print(f"\nFirst chapter:")
        print(f"  Type: {first_ch['chapter_type']}")
        print(f"  Number: {first_ch['chapter_number']}")
        print(f"  Title: {first_ch['chapter_title']}")
        print(f"  Content length: {first_ch['metadata']['content_length']} chars")
        print(f"  Word count: {first_ch['metadata']['word_count']} words")
    
    # Test: Get specific chapter
    print("\n\nTest 2: Get specific chapter")
    print("-"*70)
    chapter = parser.get_chapter_by_number(1, 1)
    if chapter:
        print(f"✓ Book 1, Chapter 1: {chapter['chapter_title']}")
        print(f"  First 200 chars: {chapter['content'][:200]}...")
    
    # Test: Parse all books
    print("\n\nTest 3: Parse all books")
    print("-"*70)
    all_books = parser.parse_all_books()
    print(f"✓ Parsed {len(all_books)} books")
    
    for book in all_books:
        meta = book['book_metadata']
        print(f"  Book {meta['book_number']:2}: {meta['book_title']:35} "
              f"- {meta['total_chapters']:3} chapters")
    
    # Test: Unified glossary
    print("\n\nTest 4: Build unified glossary")
    print("-"*70)
    unified_glossary = parser.build_unified_glossary()
    print(f"✓ Unified glossary: {len(unified_glossary)} unique terms")
    
    # Show sample terms
    print("\nSample terms:")
    for i, (term, data) in enumerate(list(unified_glossary.items())[:5], 1):
        sources = len(data['sources'])
        pron = f" ({data['pronunciation']})" if data['pronunciation'] else ""
        print(f"  {i}. {term}{pron} - appears in {sources} book(s)")
    
    print("\n" + "="*70)
    print("✓✓✓ BookParser tests complete!")
    print("="*70)


if __name__ == "__main__":
    main()