"""
Dragon's Codex - Pipeline Test Script
Tests complete chunking and enrichment pipeline.

Pipeline:
1. Chunk concepts/prophecy/magic → 3 JSONL files
2. Enrich all 7 chunk files → add character/concept/magic/prophecy mentions
3. Validate chunk structure, counts, and enrichment coverage
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config import Config

config = Config()


class PipelineValidator:
    """Validates the complete chunking and enrichment pipeline."""
    
    def __init__(self):
        """Initialize validator."""
        self.issues = []
        self.chunk_files = {
            'books': config.FILE_BOOK_CHUNKS,
            'chronology': config.FILE_WIKI_CHUNKS_CHRONOLOGY,
            'character': config.FILE_WIKI_CHUNKS_CHARACTER,
            'chapter_summary': config.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY,
            'concept': config.FILE_WIKI_CHUNKS_CONCEPT,
            'prophecy': config.PROCESSED_WIKI_PATH / 'wiki_chunks_prophecy.jsonl',
            'magic': config.PROCESSED_WIKI_PATH / 'wiki_chunks_magic.jsonl',
        }
    
    def load_chunks(self, file_path: Path) -> list:
        """Load chunks from JSONL file."""
        if not file_path.exists():
            return []
        
        chunks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunks.append(json.loads(line))
        return chunks
    
    def validate_chunk_structure(self, chunk: dict, chunk_type: str, index: int) -> list:
        """Validate a single chunk structure."""
        issues = []
        
        # Required fields for all chunks
        required_fields = ['source', 'text']
        for field in required_fields:
            if field not in chunk:
                issues.append(f"{chunk_type} chunk {index}: Missing required field '{field}'")
        
        # Check text content
        text = chunk.get('text', '')
        if len(text) < 10:
            issues.append(f"{chunk_type} chunk {index}: Text too short ({len(text)} chars)")
        
        # Check enrichment fields (should be present after enrichment)
        enrichment_fields = ['character_mentions', 'concept_mentions', 'magic_mentions', 'prophecy_mentions']
        for field in enrichment_fields:
            if field not in chunk:
                issues.append(f"{chunk_type} chunk {index}: Missing enrichment field '{field}'")
        
        return issues
    
    def validate_chunk_file(self, file_name: str, file_path: Path):
        """Validate a chunk file."""
        print(f"\n📂 Validating {file_name}...")
        
        if not file_path.exists():
            self.issues.append(f"MISSING FILE: {file_path}")
            print(f"   ❌ File not found: {file_path}")
            return
        
        # Load chunks
        chunks = self.load_chunks(file_path)
        
        if not chunks:
            self.issues.append(f"EMPTY FILE: {file_name}")
            print(f"   ⚠️  File is empty")
            return
        
        print(f"   ✓ Loaded {len(chunks):,} chunks")
        
        # Statistics
        stats = {
            'total': len(chunks),
            'with_character_mentions': 0,
            'with_concept_mentions': 0,
            'with_magic_mentions': 0,
            'with_prophecy_mentions': 0,
            'total_characters': 0,
            'total_concepts': 0,
            'total_magic': 0,
            'total_prophecies': 0,
            'structure_issues': 0,
        }
        
        # Validate each chunk
        for i, chunk in enumerate(chunks):
            # Structure validation
            chunk_issues = self.validate_chunk_structure(chunk, file_name, i)
            if chunk_issues:
                stats['structure_issues'] += len(chunk_issues)
                self.issues.extend(chunk_issues)
                # Only show first 3 issues per file
                if stats['structure_issues'] <= 3:
                    for issue in chunk_issues:
                        print(f"      ⚠️  {issue}")
            
            # Enrichment statistics
            char_mentions = chunk.get('character_mentions', [])
            concept_mentions = chunk.get('concept_mentions', [])
            magic_mentions = chunk.get('magic_mentions', [])
            prophecy_mentions = chunk.get('prophecy_mentions', [])
            
            if char_mentions:
                stats['with_character_mentions'] += 1
                stats['total_characters'] += len(char_mentions)
            
            if concept_mentions:
                stats['with_concept_mentions'] += 1
                stats['total_concepts'] += len(concept_mentions)
            
            if magic_mentions:
                stats['with_magic_mentions'] += 1
                stats['total_magic'] += len(magic_mentions)
            
            if prophecy_mentions:
                stats['with_prophecy_mentions'] += 1
                stats['total_prophecies'] += len(prophecy_mentions)
        
        # Print statistics
        if stats['structure_issues'] > 3:
            print(f"      ... and {stats['structure_issues'] - 3} more structure issues")
        
        if stats['structure_issues'] == 0:
            print(f"   ✓ All chunks have valid structure")
        else:
            print(f"   ⚠️  Found {stats['structure_issues']} structure issues")
        
        # Enrichment coverage
        char_pct = stats['with_character_mentions'] / stats['total'] * 100 if stats['total'] > 0 else 0
        concept_pct = stats['with_concept_mentions'] / stats['total'] * 100 if stats['total'] > 0 else 0
        magic_pct = stats['with_magic_mentions'] / stats['total'] * 100 if stats['total'] > 0 else 0
        prophecy_pct = stats['with_prophecy_mentions'] / stats['total'] * 100 if stats['total'] > 0 else 0
        
        print(f"\n   📊 Enrichment Coverage:")
        print(f"      Characters: {stats['with_character_mentions']:6,} chunks ({char_pct:5.1f}%) - {stats['total_characters']:,} mentions")
        print(f"      Concepts:   {stats['with_concept_mentions']:6,} chunks ({concept_pct:5.1f}%) - {stats['total_concepts']:,} mentions")
        print(f"      Magic:      {stats['with_magic_mentions']:6,} chunks ({magic_pct:5.1f}%) - {stats['total_magic']:,} mentions")
        print(f"      Prophecies: {stats['with_prophecy_mentions']:6,} chunks ({prophecy_pct:5.1f}%) - {stats['total_prophecies']:,} mentions")
        
        return stats
    
    def validate_all_files(self):
        """Validate all chunk files."""
        print("\n" + "="*80)
        print("VALIDATING ALL CHUNK FILES")
        print("="*80)
        
        all_stats = {}
        
        for file_name, file_path in self.chunk_files.items():
            stats = self.validate_chunk_file(file_name, file_path)
            if stats:
                all_stats[file_name] = stats
        
        return all_stats
    
    def print_summary(self, all_stats: dict):
        """Print validation summary."""
        print("\n" + "="*80)
        print("PIPELINE VALIDATION SUMMARY")
        print("="*80)
        
        if not all_stats:
            print("\n❌ No chunk files validated")
            return
        
        # Combined statistics
        total_chunks = sum(s['total'] for s in all_stats.values())
        total_with_chars = sum(s['with_character_mentions'] for s in all_stats.values())
        total_with_concepts = sum(s['with_concept_mentions'] for s in all_stats.values())
        total_with_magic = sum(s['with_magic_mentions'] for s in all_stats.values())
        total_with_prophecies = sum(s['with_prophecy_mentions'] for s in all_stats.values())
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total chunks:               {total_chunks:,}")
        print(f"   With character mentions:    {total_with_chars:,} ({total_with_chars/total_chunks*100:.1f}%)")
        print(f"   With concept mentions:      {total_with_concepts:,} ({total_with_concepts/total_chunks*100:.1f}%)")
        print(f"   With magic mentions:        {total_with_magic:,} ({total_with_magic/total_chunks*100:.1f}%)")
        print(f"   With prophecy mentions:     {total_with_prophecies:,} ({total_with_prophecies/total_chunks*100:.1f}%)")
        
        print(f"\n📋 Breakdown by File:")
        print(f"{'File':20} {'Chunks':>8} {'Chars%':>8} {'Concept%':>9} {'Magic%':>8} {'Prophecy%':>10}")
        print("-"*80)
        
        for file_name, stats in all_stats.items():
            char_pct = stats['with_character_mentions']/stats['total']*100 if stats['total'] > 0 else 0
            concept_pct = stats['with_concept_mentions']/stats['total']*100 if stats['total'] > 0 else 0
            magic_pct = stats['with_magic_mentions']/stats['total']*100 if stats['total'] > 0 else 0
            prophecy_pct = stats['with_prophecy_mentions']/stats['total']*100 if stats['total'] > 0 else 0
            
            print(f"{file_name:20} {stats['total']:8,} {char_pct:7.1f}% {concept_pct:8.1f}% {magic_pct:7.1f}% {prophecy_pct:9.1f}%")
        
        # Issues summary
        if not self.issues:
            print("\n✅ ALL VALIDATIONS PASSED!")
            print("   Pipeline is working correctly.")
            print("   Ready for Week 5 (Embedding).")
        else:
            print(f"\n⚠️  FOUND {len(self.issues)} ISSUES:")
            # Show first 10 unique issues
            unique_issues = list(set(self.issues))[:10]
            for i, issue in enumerate(unique_issues, 1):
                print(f"   {i}. {issue}")
            if len(unique_issues) < len(self.issues):
                print(f"   ... and {len(self.issues) - len(unique_issues)} more")
            print("\n   Please review and fix issues before proceeding.")
        
        print("\n" + "="*80)


def main():
    """Main validation function."""
    
    print("\n" + "="*80)
    print("DRAGON'S CODEX - PIPELINE TEST & VALIDATION")
    print("="*80)
    print("\nTests complete chunking + enrichment pipeline")
    
    start_time = datetime.now()
    
    validator = PipelineValidator()
    
    # Validate all chunk files
    all_stats = validator.validate_all_files()
    
    # Print summary
    validator.print_summary(all_stats)
    
    # Final timing
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n⏱️  Validation completed in {duration}")
    print()


if __name__ == "__main__":
    main()
