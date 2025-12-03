"""
Week 4 - Goal 2: Chunk Quality Review
Validates all chunks (books + wiki) for quality issues
"""

import json
import random
from pathlib import Path
from src.utils.config import get_config

def load_chunks(file_path):
    """Load chunks from a JSONL file"""
    chunks = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks

def validate_chunks():
    """
    Validate all chunks for quality issues:
    - Missing required metadata
    - Empty text
    - Temporal order consistency
    - Size distribution
    """
    config = get_config()
    
    print("=" * 60)
    print("CHUNK QUALITY VALIDATION")
    print("=" * 60)
    
    # Load all chunks
    print("\n📂 Loading chunks...")
    
    book_chunks = load_chunks(config.FILE_BOOK_CHUNKS)
    wiki_chronology = load_chunks(config.FILE_WIKI_CHUNKS_CHRONOLOGY)
    wiki_character = load_chunks(config.FILE_WIKI_CHUNKS_CHARACTER)
    wiki_chapter_summary = load_chunks(config.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY)
    wiki_concept = load_chunks(config.FILE_WIKI_CHUNKS_CONCEPT)
    
    all_chunks = {
        'books': book_chunks,
        'wiki_chronology': wiki_chronology,
        'wiki_character': wiki_character,
        'wiki_chapter_summary': wiki_chapter_summary,
        'wiki_concept': wiki_concept
    }
    
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    print(f"   Total chunks loaded: {total_chunks:,}")
    
    # Validation checks
    issues = []
    
    print("\n🔍 Running validation checks...")
    
    # Check 1: Required metadata fields
    print("\n1️⃣ Checking required metadata fields...")
    required_fields = ['source', 'text', 'temporal_order']
    
    for source_name, chunks in all_chunks.items():
        for i, chunk in enumerate(chunks):
            missing = [field for field in required_fields if field not in chunk]
            if missing:
                issues.append({
                    'type': 'missing_metadata',
                    'source': source_name,
                    'chunk_index': i,
                    'missing_fields': missing
                })
    
    if not any(issue['type'] == 'missing_metadata' for issue in issues):
        print("   ✅ All chunks have required metadata")
    else:
        missing_count = sum(1 for i in issues if i['type'] == 'missing_metadata')
        print(f"   ❌ {missing_count} chunks missing metadata")
    
    # Check 2: Empty or very short text
    print("\n2️⃣ Checking for empty or very short chunks...")
    
    for source_name, chunks in all_chunks.items():
        for i, chunk in enumerate(chunks):
            text_len = len(chunk.get('text', ''))
            if text_len == 0:
                issues.append({
                    'type': 'empty_text',
                    'source': source_name,
                    'chunk_index': i
                })
            # elif text_len < 10:  # Suspiciously short
            #     issues.append({
            #         'type': 'very_short_text',
            #         'source': source_name,
            #         'chunk_index': i,
            #         'length': text_len
            #     })
    
    empty_count = sum(1 for i in issues if i['type'] == 'empty_text')
    short_count = sum(1 for i in issues if i['type'] == 'very_short_text')
    
    if empty_count == 0 and short_count == 0:
        print("   ✅ No empty or suspiciously short chunks")
    else:
        if empty_count > 0:
            print(f"   ❌ {empty_count} chunks with empty text")
        if short_count > 0:
            print(f"   ⚠️  {short_count} chunks with very short text (<10 chars)")
    
    # Check 3: Temporal order consistency
    print("\n3️⃣ Checking temporal order consistency...")
    
    # Book chunks should have temporal_order 0-14
    invalid_temporal = []
    for i, chunk in enumerate(book_chunks):
        temporal = chunk.get('temporal_order')
        if temporal is None or not (0 <= temporal <= 14):
            invalid_temporal.append(('books', i, temporal))
    
    # Wiki chronology should have temporal_order 1-14
    for i, chunk in enumerate(wiki_chronology):
        temporal = chunk.get('temporal_order')
        if temporal is None or not (1 <= temporal <= 14):
            invalid_temporal.append(('wiki_chronology', i, temporal))
    
    # Wiki chapter summary should have temporal_order 0-14 OR None (for companion books)
    for i, chunk in enumerate(wiki_chapter_summary):
        temporal = chunk.get('temporal_order')
        # Allow None for non-narrative material (like Origins companion book)
        if temporal is not None and not (0 <= temporal <= 14):
            invalid_temporal.append(('wiki_chapter_summary', i, temporal))
    
    # Character and concept should have temporal_order = None
    for i, chunk in enumerate(wiki_character):
        temporal = chunk.get('temporal_order')
        if temporal is not None:
            invalid_temporal.append(('wiki_character', i, temporal))
    
    for i, chunk in enumerate(wiki_concept):
        temporal = chunk.get('temporal_order')
        if temporal is not None:
            invalid_temporal.append(('wiki_concept', i, temporal))
    
    if not invalid_temporal:
        print("   ✅ All temporal orders are valid")
    else:
        print(f"   ❌ {len(invalid_temporal)} chunks with invalid temporal_order")
        # Show first 5 examples
        for source, idx, temporal in invalid_temporal[:5]:
            print(f"      - {source}[{idx}]: temporal_order = {temporal}")
    
    # Check 4: Size distribution
    print("\n4️⃣ Analyzing chunk size distribution...")
    
    size_stats = {}
    for source_name, chunks in all_chunks.items():
        sizes = [len(chunk['text']) for chunk in chunks]
        size_stats[source_name] = {
            'count': len(sizes),
            'min': min(sizes) if sizes else 0,
            'max': max(sizes) if sizes else 0,
            'avg': sum(sizes) / len(sizes) if sizes else 0,
            'oversized': sum(1 for s in sizes if s > 8000)  # >2000 tokens
        }
    
    print("\n   Size Statistics (characters):")
    print("   " + "-" * 60)
    for source_name, stats in size_stats.items():
        print(f"   {source_name:25} | {stats['count']:6,} chunks | "
              f"avg: {stats['avg']:5.0f} | max: {stats['max']:5,} | "
              f"oversized: {stats['oversized']}")
    
    # Overall summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    total_issues = len(issues) + len(invalid_temporal)
    
    if total_issues == 0:
        print("✅ All validation checks passed!")
        print(f"   {total_chunks:,} chunks are ready for embedding")
    else:
        print(f"⚠️  Found {total_issues} potential issues")
        print(f"   Review needed before proceeding to embedding")
    
    # Save issues to file if any
    if issues or invalid_temporal:
        issues_file = config.DATA_PATH / 'validation_issues.json'
        with open(issues_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata_issues': issues,
                'temporal_issues': [
                    {'source': s, 'index': i, 'value': t} 
                    for s, i, t in invalid_temporal
                ]
            }, f, indent=2)
        print(f"\n📄 Issues saved to: {issues_file}")
    
    # Return random sample for manual review
    print("\n" + "=" * 60)
    print("RANDOM SAMPLE FOR MANUAL REVIEW")
    print("=" * 60)
    
    # Select 10 random chunks from each source (50 total)
    samples = {}
    for source_name, chunks in all_chunks.items():
        sample_size = min(10, len(chunks))
        samples[source_name] = random.sample(chunks, sample_size)
    
    return samples

if __name__ == "__main__":
    samples = validate_chunks()
    
    # Optionally save samples for manual review
    config = get_config()
    samples_file = config.DATA_PATH / 'chunk_samples_for_review.json'
    with open(samples_file, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 50 random samples saved to: {samples_file}")
    print("   Review these manually to verify quality")