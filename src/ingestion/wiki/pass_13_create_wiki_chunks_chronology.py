"""
Week 4 - Goal 1: Create Wiki Chunks (Chronology)
Creates chunks from chronology wiki pages (5 files, ~70 chunks expected)
Input: wiki_chronology.json
Output: wiki_chunks_chronology.jsonl
"""

import json
from pathlib import Path
from src.utils.config import get_config
from src.utils.util_files_functions import load_json_from_file, remove_file, save_jsonl_to_file
from src.utils.util_chunking_functions import split_into_paragraphs, split_paragraph_into_chunks, chunk_statistics
from src.utils.config import Config
def chunk_chronology_pages():
    """
    Chunk the chronology pages into temporal sections.
    Handles both temporal (book-based) and non-temporal (event-based) structures.
    """
    
    chronology_data = load_json_from_file(Config().FILE_WIKI_CHRONOLOGY)
    config = Config()
    chunks = []
    
    # Process each chronology page
    for filename, page_data in chronology_data.items():
        character_name = page_data['character_name']
        
        # Process temporal sections (book-by-book) - Rand, Mat
        for section in page_data.get('temporal_sections', []):
            content = section['content']
            
            if not content.strip():
                continue

            # Split large content into chunks
            content_chunks = split_into_paragraphs(content)
            
            # Create a chunk object for each split
            for idx, chunk_text in enumerate(content_chunks):
                chunk = {
                    'source': 'wiki',
                    'wiki_type': 'chronology',
                    'character_name': character_name,
                    'filename': filename,
                    'temporal_order': section['book_number'],
                    'book_title': section['book_title'],
                    'chunk_index': idx + 1,
                    'total_chunks': len(content_chunks),
                    'text': chunk_text
                }
                chunks.append(chunk)
        
        # Process non-temporal sections (event-based) - Perrin, Egwene, Elayne
        for section in page_data.get('non_temporal_sections', []):
            section_title = section.get('section_title', '')
            content = section.get('content', '')
            
            # Combine subsections if present
            if section.get('subsections'):
                subsection_texts = []
                if content.strip():
                    subsection_texts.append(content)
                for subsection in section['subsections']:
                    if subsection.get('content'):
                        subsection_texts.append(f"**{subsection['title']}**\n{subsection['content']}")
                if subsection_texts:
                    content = "\n\n".join(subsection_texts)
            
            if not content.strip():
                continue
            
            # Split large content into chunks
            content_chunks = split_into_paragraphs(content)
            
            # Create a chunk object for each split
            for idx, chunk_text in enumerate(content_chunks):
                chunk = {
                    'source': 'wiki',
                    'wiki_type': 'chronology',
                    'character_name': character_name,
                    'filename': filename,
                    'temporal_order': None,  # Event-based, no specific book number
                    'book_title': None,
                    'section_title': section_title,
                    'chunk_index': idx + 1,
                    'total_chunks': len(content_chunks),
                    'text': chunk_text
                }
                chunks.append(chunk)
    
    # Save chunks
    save_jsonl_to_file(chunks, config.FILE_WIKI_CHUNKS_CHRONOLOGY)

    # Print statistics
    print(f"✅ Chronology Chunking Complete")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Output: {config.FILE_WIKI_CHUNKS_CHRONOLOGY}")
    
    # Character breakdown
    char_counts = {}
    for chunk in chunks:
        char_name = chunk['character_name']
        char_counts[char_name] = char_counts.get(char_name, 0) + 1
    
    print(f"\n📊 Chunks per character:")
    for char, count in sorted(char_counts.items()):
        print(f"   {char}: {count} chunks")
    
    chunk_statistics(chunks)

if __name__ == "__main__":
    chunk_chronology_pages()