"""
Week 4 - Goal 1: Create Wiki Chunks (Character)
Creates chunks from character wiki pages (2,452 files)
Each section becomes one chunk (combining subsections if present)
"""

import json
from pathlib import Path
from src.utils.config import get_config

def chunk_character_pages():
    """
    Chunk the 2,452 character pages.
    Each section (or combined subsections) becomes one chunk.
    """
    config = get_config()
    
    # Load character data
    character_file = config.FILE_WIKI_CHARACTER
    with open(character_file, 'r', encoding='utf-8') as f:
        character_data = json.load(f)
    
    chunks = []
    
    # Process each character page
    for filename, page_data in character_data.items():
        character_name = page_data['character_name']
        
        # Process non-temporal sections
        for section in page_data['non_temporal_sections']:
            section_title = section['section_title']
            
            # Get content - either from section or combined subsections
            if section['content']:
                # Section has direct content
                text = section['content']
            elif section['subsections']:
                # Section has subsections - combine them
                subsection_texts = []
                for subsection in section['subsections']:
                    if subsection['content']:
                        subsection_texts.append(f"**{subsection['title']}**\n{subsection['content']}")
                text = "\n\n".join(subsection_texts)
            else:
                # Empty section - skip
                continue
            
            # Skip if text is empty after processing
            if not text.strip():
                continue
            
            chunk = {
                'source': 'wiki',
                'wiki_type': 'character',
                'character_name': character_name,
                'filename': filename,
                'section_title': section_title,
                'temporal_order': None,
                'text': text
            }
            chunks.append(chunk)
    
    # Save chunks
    output_file = config.FILE_WIKI_CHUNKS_CHARACTER
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Print statistics
    print(f"✅ Character Chunking Complete")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Characters processed: {len(character_data)}")
    print(f"   Average chunks per character: {len(chunks)/len(character_data):.1f}")
    print(f"   Output: {output_file}")
    
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
    
    # Check for oversized chunks
    oversized = [size for size in chunk_sizes if size > 8000]  # 2000 tokens
    if oversized:
        print(f"\n⚠️  WARNING: {len(oversized)} chunks exceed 2000 tokens:")
        print(f"   Sizes: {sorted(oversized, reverse=True)[:5]}")  # Show top 5

if __name__ == "__main__":
    chunk_character_pages()