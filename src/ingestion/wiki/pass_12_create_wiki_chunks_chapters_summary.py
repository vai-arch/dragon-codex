"""
Week 4 - Goal 1: Create Wiki Chunks (Chapter Summary)
Creates chunks from chapter summary wiki pages (714 files)
Splits oversized summaries into multiple chunks
Input: wiki_chapter_summary.json
Output: wiki_chunks_chapter_summary.jsonl
"""

from src.utils.config import get_config
from src.utils.util_files_functions import load_json_from_file, remove_file, save_jsonl_to_file
from src.utils.util_chunking_functions import split_into_paragraphs, split_paragraph_into_chunks, chunk_statistics
from src.utils.config import Config


def chunk_chapter_summary_pages():
    """
    Chunk the 714 chapter summary pages.
    Split oversized chapters into multiple chunks with overlap.
    """
    # Load chapter summary data
    chapter_data = load_json_from_file(Config().FILE_WIKI_CHAPTER_SUMMARY)
    
    all_chunks = []
    
    # Process each chapter summary
    for filename, page_data in chapter_data.items():
        # Build the full content
        content_parts = []
        
        for section in page_data['sections']:
            if section['content']:
                content_parts.append(f"**{section['title']}**\n{section['content']}")
        
        # Combine all sections into one text
        full_content = "\n\n".join(content_parts)
        
        if not full_content.strip():
            continue
        
        # Split into paragraphs (same as books)
        paragraphs = split_into_paragraphs(full_content)
        
        # Process all paragraphs through the chunking function (same as books)
        text_chunks = []
        for paragraph in paragraphs:
            para_chunks = split_paragraph_into_chunks(
                paragraph=paragraph
            )
            text_chunks.extend(para_chunks)
        
        # Create chunk objects with metadata (same structure as books)
        total_chunks = len(text_chunks)
        
        for idx, chunk_text in enumerate(text_chunks):
            chunk = {
                'source': 'wiki',
                'wiki_type': 'chapter_summary',
                'book_number': page_data['book_number'],
                'book_title': page_data['book_title'],
                'chapter_number': page_data['chapter_number'],
                'chapter_title': page_data['chapter_title'],
                'filename': filename,
                'temporal_order': page_data['book_number'],
                'chunk_index': idx + 1,
                'total_chunks': total_chunks,
                'text': chunk_text
            }
            all_chunks.append(chunk)
    
    # Save chunks
    save_jsonl_to_file(all_chunks, Config().FILE_WIKI_CHUNKS_CHAPTER_SUMMARY)
    
    # Print statistics
    print(f"✅ Chapter Summary Chunking Complete")
    print(f"   Total chunks: {len(all_chunks)}")
    print(f"   Chapters processed: {len(chapter_data)}")
    print(f"   Output: {Config().FILE_WIKI_CHUNKS_CHAPTER_SUMMARY}")
    
    chunk_statistics(all_chunks)

if __name__ == "__main__":
    chunk_chapter_summary_pages()