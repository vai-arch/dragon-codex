"""
Book Chunker - Week 2
Chunks book chapters into smaller pieces with metadata and character mentions.

Strategy:
- Target chunk size: 400 tokens (~1600 characters)
- Max chunk size: 500 tokens (~2000 characters)
- Split at paragraph boundaries
- 50 token overlap (~200 characters)
- Extract character mentions using aliases from character_index.json
"""

import json

from pathlib import Path
from typing import List, Dict, Set
import sys

from src.utils.util_files_functions import load_json_from_file, remove_file, save_jsonl_to_file
from src.utils.util_chunking_functions import split_into_paragraphs, split_paragraph_into_chunks, chunk_statistics
from src.utils.config import Config

config = Config()

# Input: books_all_parsed.json
input_file = config.FILE_BOOKS_ALL_PARSED

# Output: book_chunks.jsonl
output_file = config.FILE_BOOK_CHUNKS

class BookChunker:
    """Chunks books into smaller pieces with metadata."""
    
    def chunk_chapter(self, chapter: Dict, book_number: int, book_title: str) -> List[Dict]:
        """
        Chunk a single chapter into smaller pieces.
        
        Args:
            chapter: Chapter dict with content, title, etc.
            book_number: Book number (0-14)
            book_title: Book title
            
        Returns:
            List of chunk dicts
        """
        content = chapter.get('content', '')
        chapter_number = chapter.get('chapter_number', 0)
        chapter_title = chapter.get('chapter_title', '')
        chapter_type = chapter.get('chapter_type', 'chapter')
        
        # Split into paragraphs
        paragraphs = split_into_paragraphs(content)
        
        # Process all paragraphs through the chunking function
        all_chunks = []
        for paragraph in paragraphs:
            para_chunks = split_paragraph_into_chunks(
                paragraph=paragraph
            )
            all_chunks.extend(para_chunks)
        
        # Create chunk objects with metadata
        chunk_objects = []
        total_chunks = len(all_chunks)
        
        for idx, chunk_text in enumerate(all_chunks):
            chunk_id = f"book_{book_number:02d}_ch_{chapter_number:02d}_chunk_{idx+1:03d}"
            
            chunk_obj = {
                'source': 'book',
                'chunk_id': chunk_id,
                'book_number': book_number,
                'book_title': book_title,
                'chapter_number': chapter_number,
                'chapter_title': chapter_title,
                'chapter_type': chapter_type,
                'chunk_index': idx + 1,
                'total_chunks_in_chapter': total_chunks,
                'text': chunk_text,
                'temporal_order': book_number
            }
            
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    
    def process_all_books(self, books_all_parsed: Path, output_file: Path):
        """
        Process all books and create chunks.
        
        Args:
            books_file: Path to books_all_parsed.json
            output_file: Path to save book_chunks.jsonl
        """
        print("\n" + "="*80)
        print("BOOK CHUNKER - Week 2")
        print("="*80)
        
        all_books = load_json_from_file(books_all_parsed)
        
        # Process each book
        all_chunks = []
        
        for book_data in all_books:
            book_number = book_data.get('book_metadata', {}).get('book_number', 0)
            book_title = book_data.get('book_metadata', {}).get('book_title', 'Unknown')
            chapters = book_data.get('chapters', [])
            
            print(f"\n📖 Processing Book {book_number}: {book_title}")
            print(f"   Chapters: {len(chapters)}")
            
            book_chunks = []
            for chapter in chapters:
                chapter_chunks = self.chunk_chapter(chapter, book_number, book_title)
                book_chunks.extend(chapter_chunks)
            
            print(f"   ✓ Created {len(book_chunks)} chunks")
            all_chunks.extend(book_chunks)

        save_jsonl_to_file(all_chunks, output_file)
        
        # Statistics
        self.print_statistics(all_chunks)
    
    def print_statistics(self, chunks: List[Dict]):
        """Print chunking statistics."""
        print("\n" + "="*80)
        print("CHUNKING STATISTICS")
        print("="*80)
        
        total_chunks = len(chunks)
        
        # Chunks per book
        chunks_per_book = {}
        for chunk in chunks:
            book_num = chunk['book_number']
            chunks_per_book[book_num] = chunks_per_book.get(book_num, 0) + 1
        
        print(f"\nTotal chunks: {total_chunks:,}")
        print(f"\nChunks per book:")
        for book_num in sorted(chunks_per_book.keys()):
            print(f"  Book {book_num:2d}: {chunks_per_book[book_num]:4,} chunks")
        
        chunk_statistics(chunks)

def main():
    """Main execution."""
    
    remove_file(output_file)

    # Create chunker and process
    chunker = BookChunker()
    chunker.process_all_books(input_file, output_file)
    
    print("\n✅ Book chunking complete!")
    print(f"📁 Chunks saved to: {output_file}")


if __name__ == "__main__":
    main()