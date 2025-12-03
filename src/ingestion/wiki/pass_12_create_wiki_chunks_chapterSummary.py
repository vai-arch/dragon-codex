"""
Week 4 - Goal 1: Create Wiki Chunks (Chapter Summary)
Creates chunks from chapter summary wiki pages (714 files)
Splits oversized summaries into multiple chunks
"""

import json
from pathlib import Path
from src.utils.config import get_config

def split_text_by_paragraphs(text, target_size=5000):
    """
    Split text into chunks at paragraph boundaries.
    Target size: ~5000 chars (1250 tokens), leaving room for metadata sections.
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

def chunk_chapter_summary_pages():
    """
    Chunk the 714 chapter summary pages.
    Split oversized chapters into multiple chunks.
    """
    config = get_config()
    
    # Load chapter summary data
    chapter_file = config.FILE_WIKI_CHAPTER_SUMMARY
    with open(chapter_file, 'r', encoding='utf-8') as f:
        chapter_data = json.load(f)
    
    chunks = []
    split_count = 0
    
    # Process each chapter summary
    for filename, page_data in chapter_data.items():
        # Separate summary from other sections
        summary_text = ""
        other_sections = []
        
        for section in page_data['sections']:
            if section['title'] in ['Summary', 'Overview'] and section['content']:
                summary_text = section['content']
                summary_title = section['title']  # Track which one it is
            elif section['content']:
                other_sections.append(f"**{section['title']}**\n{section['content']}")
        
        # Combine other sections (Characters, Places, etc.)
        other_text = "\n\n".join(other_sections) if other_sections else ""
        
        # Check if we need to split
        total_size = len(summary_text) + len(other_text)
        
        if total_size > 8000:  # 2000 tokens
            # Split the summary
            summary_chunks = split_text_by_paragraphs(summary_text, target_size=5000)
            split_count += 1
            
            # Create multiple chunks
            for i, summary_chunk in enumerate(summary_chunks, 1):
                # Combine: Summary part + other sections
                if other_text:
                    text = f"**{summary_title} (Part {i} of {len(summary_chunks)})**\n{summary_chunk}\n\n{other_text}"
                else:
                    text = f"**{summary_title} (Part {i} of {len(summary_chunks)})**\n{summary_chunk}"
                
                chunk = {
                    'source': 'wiki',
                    'wiki_type': 'chapter_summary',
                    'book_number': page_data['book_number'],
                    'book_title': page_data['book_title'],
                    'chapter_number': page_data['chapter_number'],
                    'chapter_title': page_data['chapter_title'],
                    'filename': filename,
                    'temporal_order': page_data['book_number'],
                    'chunk_part': f"{i} of {len(summary_chunks)}",
                    'text': text
                }
                chunks.append(chunk)
        else:
            # No split needed - combine all sections
            if summary_text:
                text = f"**{summary_title}**\n{summary_text}"
                if other_text:
                    text += f"\n\n{other_text}"
            else:
                text = other_text
            
            if not text.strip():
                continue
            
            chunk = {
                'source': 'wiki',
                'wiki_type': 'chapter_summary',
                'book_number': page_data['book_number'],
                'book_title': page_data['book_title'],
                'chapter_number': page_data['chapter_number'],
                'chapter_title': page_data['chapter_title'],
                'filename': filename,
                'temporal_order': page_data['book_number'],
                'chunk_part': None,
                'text': text
            }
            chunks.append(chunk)
    
    # Save chunks
    output_file = config.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    # Print statistics
    print(f"✅ Chapter Summary Chunking Complete")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Chapters processed: {len(chapter_data)}")
    print(f"   Chapters split: {split_count}")
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
        print(f"\n⚠️  WARNING: {len(oversized)} chunks still exceed 2000 tokens:")
        print(f"   Sizes: {sorted(oversized, reverse=True)[:5]}")
    else:
        print(f"\n✅ All chunks within size limits!")

if __name__ == "__main__":
    chunk_chapter_summary_pages()