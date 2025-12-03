"""
Book Chunker - Week 2
Chunks book chapters into smaller pieces with metadata and character mentions.

Strategy:
- Target chunk size: 1000 tokens (~4000 characters)
- Max chunk size: 2000 tokens (~8000 characters)
- Split at paragraph boundaries
- 100 token overlap (~400 characters)
- Extract character mentions using aliases from character_index.json
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
import sys

from src.utils.config import Config

config = Config()

class BookChunker:
    """Chunks books into smaller pieces with metadata."""
    
    def __init__(self):
        """Initialize chunker with config and character data."""
        
        # Token estimation (rough: 1 token ≈ 4 characters)
        self.CHARS_PER_TOKEN = 4
        self.TARGET_TOKENS = 1000
        self.MAX_TOKENS = 2000
        self.OVERLAP_TOKENS = 100
        
        self.TARGET_CHARS = self.TARGET_TOKENS * self.CHARS_PER_TOKEN
        self.MAX_CHARS = self.MAX_TOKENS * self.CHARS_PER_TOKEN
        self.OVERLAP_CHARS = self.OVERLAP_TOKENS * self.CHARS_PER_TOKEN
        
        # Load character index for mention detection
        self.character_names = {}  # {lowercase_name: canonical_name}
        self._load_character_index()
    
    def _load_character_index(self):
        """Load character index and build name lookup dict."""
        char_index_path = config.FILE_CHARACTER_INDEX
        
        if not char_index_path.exists():
            print(f"⚠️  Warning: Character index not found at {char_index_path}")
            print("   Character mentions will not be extracted.")
            return
        
        with open(char_index_path, 'r', encoding='utf-8') as f:
            char_index = json.load(f)
        
        # Build lookup: all name variations -> canonical name
        for canonical_name, data in char_index.items():
            # Add canonical name
            self.character_names[canonical_name.lower()] = canonical_name
            
            # Add aliases
            aliases = data.get('aliases', [])
            for alias in aliases:
                self.character_names[alias.lower()] = canonical_name
        
        print(f"✓ Loaded {len(char_index)} characters with {len(self.character_names)} name variations")
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Chapter text
            
        Returns:
            List of paragraph strings
        """
        # Split on double newlines or more
        paragraphs = re.split(r'\n\s*\n+', text)
        
        # Clean and filter empty
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
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
        
        if not content:
            return []
        
        # Split into paragraphs
        paragraphs = self.split_into_paragraphs(content)
        
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk_text = []
        current_chunk_length = 0
        
        for i, paragraph in enumerate(paragraphs):
            para_length = len(paragraph)
            
            # If paragraph alone exceeds max, split it at sentence boundaries
            if para_length > self.MAX_CHARS:
                # First, save current chunk if any
                if current_chunk_text:
                    chunks.append('\n\n'.join(current_chunk_text))
                    current_chunk_text = []
                    current_chunk_length = 0
                
                # Split large paragraph at sentences
                sentences = re.split(r'([.!?]+\s+)', paragraph)
                temp_chunk = []
                temp_length = 0
                
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    
                    if temp_length + len(sentence) > self.MAX_CHARS and temp_chunk:
                        chunks.append(''.join(temp_chunk))
                        # Keep overlap
                        overlap_text = ''.join(temp_chunk)[-self.OVERLAP_CHARS:]
                        temp_chunk = [overlap_text, sentence]
                        temp_length = len(overlap_text) + len(sentence)
                    else:
                        temp_chunk.append(sentence)
                        temp_length += len(sentence)
                
                if temp_chunk:
                    chunks.append(''.join(temp_chunk))
                
                continue
            
            # Check if adding this paragraph exceeds target
            if current_chunk_length + para_length > self.TARGET_CHARS and current_chunk_text:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk_text))
                
                # Start new chunk with overlap from previous
                overlap_text = '\n\n'.join(current_chunk_text)[-self.OVERLAP_CHARS:]
                current_chunk_text = [overlap_text, paragraph]
                current_chunk_length = len(overlap_text) + para_length
            else:
                # Add to current chunk
                current_chunk_text.append(paragraph)
                current_chunk_length += para_length
        
        # Save last chunk
        if current_chunk_text:
            chunks.append('\n\n'.join(current_chunk_text))
        
        # Create chunk objects with metadata
        chunk_objects = []
        total_chunks = len(chunks)
        
        for idx, chunk_text in enumerate(chunks):
            chunk_id = f"book_{book_number:02d}_ch_{chapter_number:02d}_chunk_{idx+1:03d}"
            
            # Extract character mentions
            char_mentions = self.extract_character_mentions(chunk_text)
            
            chunk_obj = {
                'source': 'book',  # Add this line
                'chunk_id': chunk_id,
                'book_number': book_number,
                'book_title': book_title,
                'chapter_number': chapter_number,
                'chapter_title': chapter_title,
                'chapter_type': chapter_type,
                'chunk_index': idx + 1,
                'total_chunks_in_chapter': total_chunks,
                'text': chunk_text,
                'character_mentions': sorted(list(char_mentions)),
                'temporal_order': book_number
            }
            
            chunk_objects.append(chunk_obj)
        
        return chunk_objects
    
    def extract_character_mentions(self, text: str) -> Set[str]:
        """
        Extract character mentions from text using character index.
        
        Args:
            text: Chunk text
            
        Returns:
            Set of canonical character names mentioned
        """
        if not self.character_names:
            return set()
        
        mentioned = set()
        text_lower = text.lower()
        
        # Check each name variation
        for name_variation, canonical_name in self.character_names.items():
            # Use word boundaries to avoid partial matches
            # e.g., "Rand" shouldn't match "Random"
            pattern = r'\b' + re.escape(name_variation) + r'\b'
            if re.search(pattern, text_lower):
                mentioned.add(canonical_name)
        
        return mentioned
    
    def process_all_books(self, books_file: Path, output_file: Path):
        """
        Process all books and create chunks.
        
        Args:
            books_file: Path to books_all_parsed.json
            output_file: Path to save book_chunks.jsonl
        """
        print("\n" + "="*80)
        print("BOOK CHUNKER - Week 2")
        print("="*80)
        
        # Load all books
        print(f"\n📂 Loading books from: {books_file}")
        with open(books_file, 'r', encoding='utf-8') as f:
            all_books = json.load(f)
        
        print(f"✓ Loaded {len(all_books)} books")
        
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
        
        # Save to JSONL
        print(f"\n💾 Saving {len(all_chunks)} chunks to: {output_file}")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
        
        print(f"✓ Saved!")
        
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
        
        # Chunk sizes
        chunk_sizes = [len(c['text']) for c in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        
        print(f"\nChunk sizes (characters):")
        print(f"  Average: {avg_size:,.0f}")
        print(f"  Min: {min_size:,}")
        print(f"  Max: {max_size:,}")
        print(f"  Target: {self.TARGET_CHARS:,}")
        print(f"  Max allowed: {self.MAX_CHARS:,}")
        
        # Character mentions
        chunks_with_mentions = sum(1 for c in chunks if c['character_mentions'])
        total_mentions = sum(len(c['character_mentions']) for c in chunks)
        
        print(f"\nCharacter mentions:")
        print(f"  Chunks with mentions: {chunks_with_mentions:,} ({chunks_with_mentions/total_chunks*100:.1f}%)")
        print(f"  Total mention instances: {total_mentions:,}")
        if chunks_with_mentions > 0:
            print(f"  Average per chunk (with mentions): {total_mentions/chunks_with_mentions:.1f}")
        
        print("\n" + "="*80)


def main():
    """Main execution."""
    
    books_file = config.FILE_BOOKS_ALL_PARSED
    
    # Output: book_chunks.jsonl
    output_file = config.FILE_BOOK_CHUNKS
    
    if not books_file.exists():
        print(f"❌ Error: Books file not found: {books_file}")
        return
    
    # Create chunker and process
    chunker = BookChunker()
    chunker.process_all_books(books_file, output_file)
    
    print("\n✅ Book chunking complete!")
    print(f"📁 Chunks saved to: {output_file}")


if __name__ == "__main__":
    main()