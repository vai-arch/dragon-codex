"""
Dragon's Codex - Unified Wiki Concept/Prophecy/Magic Chunker
Chunks concept, prophecy, and magic pages into separate JSONL files.

Processes:
- wiki_concept.json -> wiki_chunks_concept.jsonl
- wiki_prophecy.json -> wiki_chunks_prophecy.jsonl  
- wiki_magic.json -> wiki_chunks_magic.jsonl

Chunking Strategy:
- Split long sections using same logic as chapter summaries
- Preserves section hierarchy and structure
- Adds metadata for retrieval (source, type, categories)

Input:
- wiki_concept.json
- wiki_prophecy.json
- wiki_magic.json
Output:
- wiki_chunks_concept.jsonl
- wiki_chunks_prophecy.jsonl
- wiki_chunks_magic.jsonl

"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.config import Config
from src.utils.util_chunking_functions import (
    split_into_paragraphs, 
    split_paragraph_into_chunks,
    chunk_statistics
)
from src.utils.util_files_functions import save_jsonl_to_file

config = Config()

# Input files
concept_file = config.FILE_WIKI_CONCEPT
prophecy_file = config.FILE_WIKI_PROPHECIES
magic_file = config.FILE_WIKI_MAGIC

# Output files
concept_output = config.FILE_WIKI_CHUNKS_CONCEPT
prophecy_output = config.FILE_WIKI_CHUNKS_PROPHECIES
magic_output = config.FILE_WIKI_CHUNKS_MAGIC


# def chunk_page(
#     filename: str,
#     page_data: Dict,
#     source_type: str
# ) -> List[Dict]:
#     """
#     Chunk a single wiki page, splitting long sections.
    
#     Args:
#         filename: Source filename
#         page_data: Parsed page data
#         source_type: 'concept', 'prophecy', or 'magic'
        
#     Returns:
#         List of chunks
#     """
#     page_name = page_data.get('page_name', '')
#     page_type = page_data.get('page_type', '')
#     sections = page_data.get('sections', [])
#     categories = page_data.get('metadata', {}).get('categories', [])
    
#     # Build full content from all sections
#     content_parts = []
    
#     for section in sections:
#         section_title = section.get('title', '')
#         section_content = section.get('content', '').strip()
        
#         # Skip category sections
#         if section_title.lower() in ['categories', 'category']:
#             continue
        
#         # Add section with title
#         if section_title and section_content:
#             content_parts.append(f"**{section_title}**\n{section_content}")
#         elif section_content:
#             content_parts.append(section_content)
        
#         # Add subsections
#         for subsection in section.get('subsections', []):
#             sub_title = subsection.get('title', '')
#             sub_content = subsection.get('content', '').strip()
#             if sub_title and sub_content:
#                 content_parts.append(f"**{sub_title}**\n{sub_content}")
#             elif sub_content:
#                 content_parts.append(sub_content)
    
#     # Combine all sections
#     full_content = "\n\n".join(content_parts)
    
#     if not full_content.strip():
#         return []
    
#     # Split into paragraphs (same as chapter summaries)
#     paragraphs = split_into_paragraphs(full_content)
    
#     # Process all paragraphs through chunking function
#     text_chunks = []
#     for paragraph in paragraphs:
#         para_chunks = split_paragraph_into_chunks(paragraph=paragraph)
#         text_chunks.extend(para_chunks)
    
#     # Create chunk objects with metadata
#     total_chunks = len(text_chunks)
#     chunks = []
    
#     for idx, chunk_text in enumerate(text_chunks):
#         chunk = {
#             'source': 'wiki',
#             'source_type': source_type,
#             'page_type': page_type,
#             'page_name': page_name,
#             'source_file': filename,
#             'temporal_order': None,  # Wiki pages don't have book ordering
#             'chunk_index': idx + 1,
#             'total_chunks': total_chunks,
#             'text': chunk_text
#         }
        
#         # Add categories
#         if categories:
#             chunk['categories'] = categories
        
#         chunks.append(chunk)
    
#     return chunks

def chunk_page(
    filename: str,
    page_data: Dict,
    source_type: str
) -> List[Dict]:
    """
    Chunk a single wiki page by grouping sections to reach target size.
    Preserves section structure while creating properly-sized chunks.
    
    Args:
        filename: Source filename
        page_data: Parsed page data
        source_type: 'concept', 'prophecy', or 'magic'
        
    Returns:
        List of chunks
    """
    page_name = page_data.get('page_name', '')
    page_type = page_data.get('page_type', '')
    sections = page_data.get('sections', [])
    categories = page_data.get('metadata', {}).get('categories', [])
    
    config = Config()
    
    # Build list of section texts (each section with its subsections)
    section_texts = []
    section_titles = []
    
    for section in sections:
        section_title = section.get('title', '')
        section_content = section.get('content', '').strip()
        
        # Skip category sections
        if section_title.lower() in ['categories', 'category']:
            continue
        
        # Build section text with subsections
        section_parts = []
        
        # Add main section content
        if section_title and section_content:
            section_parts.append(f"## {section_title}\n{section_content}")
        elif section_title:
            section_parts.append(f"## {section_title}")
        elif section_content:
            section_parts.append(section_content)
        
        # Add subsections
        for subsection in section.get('subsections', []):
            sub_title = subsection.get('title', '')
            sub_content = subsection.get('content', '').strip()
            
            if sub_title and sub_content:
                section_parts.append(f"### {sub_title}\n{sub_content}")
            elif sub_title:
                section_parts.append(f"### {sub_title}")
            elif sub_content:
                section_parts.append(sub_content)
        
        # Combine section and subsections
        full_section_text = "\n\n".join(section_parts)
        
        if not full_section_text.strip():
            continue
        
        section_texts.append(full_section_text)
        section_titles.append(section_title if section_title else "Content")
    
    if not section_texts:
        return []
    
    # Group sections into chunks (like grouping paragraphs)
    chunks = []
    current_chunk_sections = []
    current_chunk_titles = []
    current_size = 0
    
    target_size = config.CHUNK_SIZE  # 6,144 chars
    max_size = config.MAX_CHUNK_SIZE  # 7,680 chars
    
    for section_text, section_title in zip(section_texts, section_titles):
        section_size = len(section_text)
        
        # If single section exceeds max, split it by paragraphs
        if section_size > max_size:
            # Save current chunk if exists
            if current_chunk_sections:
                chunk_text = "\n\n".join(current_chunk_sections)
                chunk_titles = ", ".join(current_chunk_titles)
                chunks.append({
                    'text': chunk_text,
                    'section_title': chunk_titles
                })
                current_chunk_sections = []
                current_chunk_titles = []
                current_size = 0
            
            # Split oversized section by paragraphs and group them
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
        
        if new_size <= max_size:
            # Fits - add to current chunk
            current_chunk_sections.append(section_text)
            current_chunk_titles.append(section_title)
            current_size = new_size
        else:
            # Doesn't fit - start new chunk
            if current_chunk_sections:
                chunk_text = "\n\n".join(current_chunk_sections)
                chunk_titles = ", ".join(current_chunk_titles)
                chunks.append({
                    'text': chunk_text,
                    'section_title': chunk_titles
                })
            
            current_chunk_sections = [section_text]
            current_chunk_titles = [section_title]
            current_size = section_size
    
    # Add final chunk
    if current_chunk_sections:
        chunk_text = "\n\n".join(current_chunk_sections)
        chunk_titles = ", ".join(current_chunk_titles)
        chunks.append({
            'text': chunk_text,
            'section_title': chunk_titles
        })
    
    # Convert to final chunk format with metadata
    final_chunks = []
    total_chunks = len(chunks)
    
    for idx, chunk_data in enumerate(chunks):
        chunk = {
            'source': 'wiki',
            'source_type': source_type,
            'page_type': page_type,
            'page_name': page_name,
            'source_file': filename,
            'section_title': chunk_data['section_title'],
            'temporal_order': None,
            'chunk_index': idx + 1,
            'total_chunks': total_chunks,
            'text': chunk_data['text']
        }
        
        if categories:
            chunk['categories'] = categories
        
        final_chunks.append(chunk)
    
    return final_chunks

def process_file(
    input_file: Path,
    output_file: Path,
    source_type: str
) -> tuple:
    """
    Process a single file type (concept, prophecy, or magic).
    
    Args:
        input_file: Input JSON file path
        output_file: Output JSONL file path
        source_type: 'concept', 'prophecy', or 'magic'
        
    Returns:
        (chunks_created, stats_dict)
    """
    print(f"\n📄 Processing {source_type} pages from: {input_file.name}")
    
    # Load data
    with open(input_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    
    print(f"   ✓ Loaded {len(pages):,} pages")
    
    # Process all pages
    all_chunks = []
    pages_processed = 0
    empty_pages = 0
    
    for filename, page_data in pages.items():
        chunks = chunk_page(filename, page_data, source_type)
        
        if not chunks:
            empty_pages += 1
            continue
        
        all_chunks.extend(chunks)
        pages_processed += 1
    
    # Save chunks using utility function
    print(f"   💾 Saving {len(all_chunks):,} chunks to: {output_file.name}")
    save_jsonl_to_file(all_chunks, output_file)
    print(f"   ✓ Saved {len(all_chunks):,} chunks")
    
    # Statistics
    stats = {
        'pages_processed': pages_processed,
        'empty_pages': empty_pages,
        'chunks_created': len(all_chunks)
    }
    
    return all_chunks, stats


def print_statistics(source_type: str, stats: Dict):
    """Print chunking statistics."""
    print(f"\n   📊 {source_type.title()} Statistics:")
    print(f"      Pages processed:        {stats['pages_processed']:6,}")
    print(f"      Empty pages skipped:    {stats['empty_pages']:6,}")
    print(f"      Chunks created:         {stats['chunks_created']:6,}")


def main():
    """Main chunking function."""
    
    print("\n" + "=" * 80)
    print("DRAGON'S CODEX - UNIFIED CONCEPT/PROPHECY/MAGIC CHUNKER")
    print("=" * 80)
    
    print(f"\n📂 Configuration:")
    print(f"   Concept input:     {concept_file}")
    print(f"   Prophecy input:    {prophecy_file}")
    print(f"   Magic input:       {magic_file}")
    print(f"   Concept output:    {concept_output}")
    print(f"   Prophecy output:   {prophecy_output}")
    print(f"   Magic output:      {magic_output}")
    
    start_time = datetime.now()
    
    all_stats = {}
    
    # Process concepts
    concept_chunks, concept_stats = process_file(concept_file, concept_output, 'concept')
    print_statistics('concept', concept_stats)
    all_stats['concept'] = concept_stats
    
    # Process prophecies
    prophecy_chunks, prophecy_stats = process_file(prophecy_file, prophecy_output, 'prophecy')
    print_statistics('prophecy', prophecy_stats)
    all_stats['prophecy'] = prophecy_stats
    
    # Process magic
    magic_chunks, magic_stats = process_file(magic_file, magic_output, 'magic')
    print_statistics('magic', magic_stats)
    all_stats['magic'] = magic_stats
    
    # Combined statistics
    print("\n" + "=" * 80)
    print("COMBINED STATISTICS")
    print("=" * 80)
    
    total_pages = sum(s['pages_processed'] for s in all_stats.values())
    total_chunks = sum(s['chunks_created'] for s in all_stats.values())
    
    print(f"\n   Total pages processed:     {total_pages:6,}")
    print(f"   Total chunks created:      {total_chunks:6,}")
    
    print(f"\n   Breakdown by type:")
    for source_type, stats in all_stats.items():
        pct = stats['chunks_created']/total_chunks*100 if total_chunks > 0 else 0
        print(f"      {source_type.title():12s} {stats['chunks_created']:6,} chunks ({pct:5.1f}%)")
    
    # Detailed chunk statistics using utility function
    print("\n" + "=" * 80)
    print("CHUNK STATISTICS")
    print("=" * 80)
    
    print(f"\n📊 Concept Chunks:")
    chunk_statistics(concept_chunks)
    
    print(f"\n📊 Prophecy Chunks:")
    chunk_statistics(prophecy_chunks)
    
    print(f"\n📊 Magic Chunks:")
    chunk_statistics(magic_chunks)
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("CHUNKING COMPLETE!")
    print("=" * 80)
    print(f"\n⏱️  Total time: {duration}")
    print(f"📊 Total chunks: {total_chunks:,}")
    print(f"\n✅ All concept/prophecy/magic pages chunked!\n")


if __name__ == "__main__":
    main()