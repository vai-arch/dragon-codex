"""
Week 4 - Goal 1: Create Wiki Chunks (Concept)
Creates chunks from concept wiki pages (2,716 files)
Splits oversized sections into multiple chunks
"""

import json
from pathlib import Path
from src.utils.config import get_config

def split_text_by_paragraphs(text, target_size=5000):
    """
    Split text into chunks at paragraph boundaries.
    Target size: ~5000 chars (1250 tokens).
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para) + 2  # +2 for \n\n
        
        if current_size + para_size > target_size and current_chunk:
            # Save current chunk and start new one
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def chunk_concept_pages():
    """
    Chunk the 2,716 concept pages.
    Split oversized sections into multiple chunks.
    """
    config = get_config()
    
    # Load concept data
    concept_file = config.FILE_WIKI_CONCEPT
    with open(concept_file, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)
    
    chunks = []
    split_count = 0
    
    # Process each concept page
    for filename, page_data in concept_data.items():
        page_name = page_data['page_name']
        
        # Process sections
        for section in page_data['sections']:
            # Skip empty sections and "Categories" sections
            if not section['content'] or section['title'] == 'Categories':
                continue
            
            section_content = section['content']
            section_title = section['title']
            
            # Check if we need to split
            if len(section_content) > 8000:  # 2000 tokens
                # Split the content
                content_chunks = split_text_by_paragraphs(section_content, target_size=5000)
                split_count += 1
                
                # Create multiple chunks
                for i, content_chunk in enumerate(content_chunks, 1):
                    chunk = {
                        'source': 'wiki',
                        'wiki_type': 'concept',
                        'concept_name': page_name,
                        'filename': filename,
                        'section_title': f"{section_title} (Part {i} of {len(content_chunks)})",
                        'temporal_order': None,
                        'chunk_part': f"{i} of {len(content_chunks)}",
                        'text': content_chunk
                    }
                    chunks.append(chunk)
            else:
                # No split needed
                chunk = {
                    'source': 'wiki',
                    'wiki_type': 'concept',
                    'concept_name': page_name,
                    'filename': filename,
                    'section_title': section_title,
                    'temporal_order': None,
                    'chunk_part': None,
                    'text': section_content
                }
                chunks.append(chunk)
    
    # Save chunks
    output_file = config.FILE_WIKI_CHUNKS_CONCEPT
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Print statistics
    print(f"✅ Concept Chunking Complete")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Concepts processed: {len(concept_data)}")
    print(f"   Sections split: {split_count}")
    print(f"   Average chunks per concept: {len(chunks)/len(concept_data):.1f}")
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
        print(f"   Sizes: {sorted(oversized, reverse=True)[:5]}")
    else:
        print(f"\n✅ All chunks within size limits!")

if __name__ == "__main__":
    chunk_concept_pages()