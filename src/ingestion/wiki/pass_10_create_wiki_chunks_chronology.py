"""
Week 4 - Goal 1: Create Wiki Chunks (Chronology)
Creates chunks from chronology wiki pages (5 files, ~70 chunks expected)
"""

import json
from pathlib import Path
from src.utils.config import get_config

def chunk_chronology_pages():
    """
    Chunk the 5 chronology pages into temporal sections.
    Each book section becomes one chunk.
    """
    config = get_config()
    
    # Load chronology data
    chronology_file = config.FILE_WIKI_CHRONOLOGY
    with open(chronology_file, 'r', encoding='utf-8') as f:
        chronology_data = json.load(f)
    
    chunks = []
    
    # Process each chronology page (5 characters)
    for filename, page_data in chronology_data.items():
        character_name = page_data['character_name']
        
        # Process temporal sections (book-by-book)
        for section in page_data['temporal_sections']:
            chunk = {
                'source': 'wiki',
                'wiki_type': 'chronology',
                'character_name': character_name,
                'filename': filename,
                'temporal_order': section['book_number'],
                'book_title': section['book_title'],
                'text': section['content']
            }
            chunks.append(chunk)
    
    # Save chunks
    output_file = config.FILE_WIKI_CHUNKS_CHRONOLOGY
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Print statistics
    print(f"✅ Chronology Chunking Complete")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Output: {output_file}")
    
    # Character breakdown
    char_counts = {}
    for chunk in chunks:
        char_name = chunk['character_name']
        char_counts[char_name] = char_counts.get(char_name, 0) + 1
    
    print(f"\n📊 Chunks per character:")
    for char, count in sorted(char_counts.items()):
        print(f"   {char}: {count} chunks")
    
    # Size analysis
    chunk_sizes = [len(chunk['text']) for chunk in chunks]
    avg_size = sum(chunk_sizes) / len(chunk_sizes)
    min_size = min(chunk_sizes)
    max_size = max(chunk_sizes)
    
    print(f"\n📏 Chunk size statistics (characters):")
    print(f"   Average: {avg_size:.0f}")
    print(f"   Min: {min_size}")
    print(f"   Max: {max_size}")
    print(f"   Approx tokens (÷4): avg={avg_size/4:.0f}, max={max_size/4:.0f}")

if __name__ == "__main__":
    chunk_chronology_pages()