"""
Week 4 - Goal 1: Create Wiki Chunks (Character)
Creates chunks from character wiki pages (2,452 files)
Each section becomes one chunk (combining subsections if present)
Input: wiki_character.json
Output: wiki_chunks_character.jsonl
"""

from src.utils.config import get_config
from src.utils.util_files_functions import load_json_from_file, remove_file, save_jsonl_to_file
from src.utils.util_chunking_functions import split_into_paragraphs, split_paragraph_into_chunks, chunk_statistics
from src.utils.config import Config

def chunk_character_pages():
    """
    Chunk the 2,452 character pages.
    Groups sections together to reach target size, preserving structure.
    """
    character_data = load_json_from_file(Config().FILE_WIKI_CHARACTER)
    config = Config()
    all_chunks = []
    
    # Process each character page
    for filename, page_data in character_data.items():
        character_name = page_data['character_name']
        
        # Build list of section texts
        section_texts = []
        section_titles = []
        
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
            
            section_texts.append(text)
            section_titles.append(section_title)
        
        if not section_texts:
            continue
        
        # Group sections into chunks
        chunks = []
        current_chunk_sections = []
        current_chunk_titles = []
        current_size = 0
        
        for section_text, section_title in zip(section_texts, section_titles):
            section_size = len(section_text)
            
            # If single section exceeds max, split it
            if section_size > config.MAX_CHUNK_SIZE:
                # Save current chunk if exists
                if current_chunk_sections:
                    chunks.append({
                        'text': "\n\n".join(current_chunk_sections),
                        'section_title': ", ".join(current_chunk_titles)
                    })
                    current_chunk_sections = []
                    current_chunk_titles = []
                    current_size = 0
                
                # Split oversized section
                section_chunks = split_into_paragraphs(section_text)
                for chunk_text in section_chunks:
                    chunks.append({
                        'text': chunk_text,
                        'section_title': section_title
                    })
                continue
            
            # Check if adding this section would exceed max
            separator_size = 2 if current_chunk_sections else 0
            new_size = current_size + separator_size + section_size
            
            if new_size <= config.MAX_CHUNK_SIZE:
                # Fits - add to current chunk
                current_chunk_sections.append(section_text)
                current_chunk_titles.append(section_title)
                current_size = new_size
            else:
                # Doesn't fit - start new chunk
                if current_chunk_sections:
                    chunks.append({
                        'text': "\n\n".join(current_chunk_sections),
                        'section_title': ", ".join(current_chunk_titles)
                    })
                
                current_chunk_sections = [section_text]
                current_chunk_titles = [section_title]
                current_size = section_size
        
        # Add final chunk
        if current_chunk_sections:
            chunks.append({
                'text': "\n\n".join(current_chunk_sections),
                'section_title': ", ".join(current_chunk_titles)
            })
        
        # Create chunk objects with metadata
        total_chunks = len(chunks)
        for idx, chunk_data in enumerate(chunks):
            chunk = {
                'source': 'wiki',
                'wiki_type': 'character',
                'character_name': character_name,
                'filename': filename,
                'section_title': chunk_data['section_title'],
                'temporal_order': None,
                'chunk_index': idx + 1,
                'total_chunks': total_chunks,
                'text': chunk_data['text']
            }
            all_chunks.append(chunk)
    
    # Save chunks
    save_jsonl_to_file(all_chunks, config.FILE_WIKI_CHUNKS_CHARACTER)

    # Print statistics
    print(f"✅ Character Chunking Complete")
    print(f"   Total chunks: {len(all_chunks)}")
    print(f"   Characters processed: {len(character_data)}")
    print(f"   Average chunks per character: {len(all_chunks)/len(character_data):.1f}")
    print(f"   Output: {config.FILE_WIKI_CHUNKS_CHARACTER}")
    
    chunk_statistics(all_chunks)

if __name__ == "__main__":
    chunk_character_pages()