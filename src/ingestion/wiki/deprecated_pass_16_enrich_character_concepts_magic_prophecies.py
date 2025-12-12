"""
Week 4 - Goal 4: Concept, Magic & Prophecy Tagging (v2.0)
Adds concept_mentions, magic_mentions, and prophecy_mentions fields to all chunks.

Input: 
- unified_glossary.json
- magic_system_index.json   
- prophecy_index.json
- chunk files
Output:
- enriched chunk files with concept_mentions, magic_mentions, and prophecy_mentions fields

"""

import sys
import re
from pathlib import Path
from typing import Set, Dict

from tqdm import tqdm
from src.utils.config import get_config
from src.utils.util_files_functions import load_json_from_file, remove_file, save_jsonl_to_file, load_line_by_line

class ConceptMagicProphecyTagger:
    """Tag chunks with WoT concepts, magic system, and prophecy mentions."""
    
    def __init__(self):
        """Initialize with character, magic, prophecy and concepts indexes."""
        self.character_terms = {} # {lowercase_term: original_term}
        self.concept_terms = {}   # {lowercase_term: original_term}
        self.magic_terms = {}     # {lowercase_term: original_term}
        self.prophecy_terms = {}  # {lowercase_term: original_term}
        self._load_indexes()
    
    def _load_indexes(self):
        """Load unified glossary, magic system index, and prophecy index."""
        config = get_config()
        
        # Load wiki_concept.json
        character_index = load_json_from_file(config.FILE_CHARACTER_INDEX)

        # Build character lookup (use page_name from index)
        for page_name, data in character_index.items():
            self.character_terms[page_name.lower()] = page_name
            
            # Also add aliases if present
            for alias in data.get('aliases', []):
                self.character_terms[alias.lower()] = page_name
        
        print(f"✓ Loaded {len(character_index)} character terms ({len(self.character_terms)} with aliases)")

        # Load wiki_concept.json
        concept_index = load_json_from_file(config.FILE_CONCEPT_INDEX)

        # Build concept lookup (use page_name from index)
        for page_name, data in concept_index.items():
            self.concept_terms[page_name.lower()] = page_name
            
            # Also add aliases if present
            for alias in data.get('aliases', []):
                self.concept_terms[alias.lower()] = page_name
        
        print(f"✓ Loaded {len(concept_index)} concept terms ({len(self.concept_terms)} with aliases)")

        # Load magic system index
        magic_index = load_json_from_file(config.FILE_MAGIC_SYSTEM_INDEX)

        # Build magic lookup (use page_name from index)
        for page_name, data in magic_index.items():
            self.magic_terms[page_name.lower()] = page_name
            
            # Also add aliases
            for alias in data.get('aliases', []):
                self.magic_terms[alias.lower()] = page_name
        
        print(f"✓ Loaded {len(magic_index)} magic system terms ({len(self.magic_terms)} with aliases)")
        
        # Load prophecy index
        prophecy_index = load_json_from_file(config.FILE_PROPHECY_INDEX)

        # Build prophecy lookup (use page_name from index)
        for page_name, data in prophecy_index.items():
            self.prophecy_terms[page_name.lower()] = page_name
            
            # Also add aliases
            for alias in data.get('aliases', []):
                self.prophecy_terms[alias.lower()] = page_name
        
        print(f"✓ Loaded {len(prophecy_index)} prophecy terms ({len(self.prophecy_terms)} with aliases)")
    
    def extract_mentions(self, text_lower: str, items, page_name) -> Set[str]:
        """
        Extract mentions (defined in items) from text.
        
        Args:
            text: Chunk text in lowercase
            items: mention terms to check
            
        Returns:
            Set of the terms mentioned
        """
        
        mentioned = set()
        mentioned_add = mentioned.add
        chunk = f" {text_lower} "

        # Check each term
        for entry in items:
            if(page_name and page_name == entry['original_term']):
                mentioned.add(entry['original_term'])
                continue
            # Fast path for single words with word boundaries
            if entry.get("simple"):
                # Check with spaces around for word boundaries
                if entry["simple_search_term"] in chunk:
                    mentioned_add(entry["original_term"])
            else:
                # Regex for multi-word terms
                if entry["pattern"].search(chunk):
                    mentioned_add(entry["original_term"])
        
        sorted_mentioned = sorted(list(mentioned))

        return sorted_mentioned
    
    def add_pattern_to_items(self, items):
        """
        Add regex pattern with word boundaries to each item in the dict.
        
        Args:
            items: dict of terms
            
        Returns:
            dict with added 'pattern' key for each term
        """
        enhanced_items = []
        
        for term_lower, original_term in items:
            # Use word boundaries to avoid partial matches
            pattern = re.compile(r'\b' + re.escape(term_lower) + r'\b')
            enhanced_items.append({
                "term_lower": term_lower,
                "original_term": original_term,
                "pattern": pattern,
                "simple": " " not in term_lower,
                "simple_search_term": f" {term_lower} "
            })
        
        return enhanced_items
    
    def enrich_chunk_file(self, file_path: Path, chunk_type: str):
        """
        Add concept_mentions, magic_mentions, and prophecy_mentions to all chunks in a file.
        
        Args:
            file_path: Path to JSONL file
            chunk_type: Type of chunks (for logging)
        """
        print(f"\n📂 Processing {chunk_type}...")
        print(f"   File: {file_path.name}")
        
        # Load chunks
        chunks = load_line_by_line(file_path)

        # Add mentions to each chunk
        chunks_with_characters = 0
        chunks_with_concepts = 0
        chunks_with_magic = 0
        chunks_with_prophecies = 0
        total_character_mentions = 0
        total_concept_mentions = 0
        total_magic_mentions = 0
        total_prophecy_mentions = 0

        chunks_with_mentions = 0

        if not self.character_terms or not self.prophecy_terms or not self.magic_terms or not self.concept_terms:
            raise ValueError("❌ Error: One or more indexes (characters, concepts, magic, prophecies) are empty.")
        
        character_terms_items = self.add_pattern_to_items(self.character_terms.items()) 
        concept_terms_items = self.add_pattern_to_items(self.concept_terms.items()) 
        magic_terms_items = self.add_pattern_to_items(self.magic_terms.items()) 
        prophecy_terms_items = self.add_pattern_to_items(self.prophecy_terms.items()) 

        pbar = tqdm(chunks, desc="Processing chunks", dynamic_ncols=True, leave=False, file=sys.stderr)

        for chunk in pbar:
            text = chunk["text"].lower()
            page_name = chunk["page_name"]
            character_name = chunk["character_name"]

            text_lower = text.lower()
            
            # Extract character mentions
            character_mentions = self.extract_mentions(text_lower, character_terms_items, character_name)
            chunk['character_mentions'] = character_mentions
            
            if character_mentions:
                chunks_with_characters += 1
                total_character_mentions += len(character_mentions)
            
            # Extract concept mentions
            concept_mentions = self.extract_mentions(text_lower, concept_terms_items, page_name)
            chunk['concept_mentions'] = concept_mentions
            
            if concept_mentions:
                chunks_with_concepts += 1
                total_concept_mentions += len(concept_mentions)
            
            magic_mentions = self.extract_mentions(text_lower, magic_terms_items, page_name)
            chunk['magic_mentions'] = magic_mentions
            
            if magic_mentions:
                chunks_with_magic += 1
                total_magic_mentions += len(magic_mentions)
            
            # Extract prophecy mentions
            prophecy_mentions = self.extract_mentions(text_lower, prophecy_terms_items, page_name)
            chunk['prophecy_mentions'] = prophecy_mentions
            
            if prophecy_mentions:
                chunks_with_prophecies += 1
                total_prophecy_mentions += len(prophecy_mentions)
            
            # Progress indicator for large files
            pbar.set_postfix_str(f"Chunks with Characters: {chunks_with_characters}, Concepts: {chunks_with_concepts}, Magic: {chunks_with_magic}, Prophecies: {chunks_with_prophecies}")
        
        # Save enriched chunks
        save_jsonl_to_file(chunks, file_path)
        
        print(f"   ✅ Enriched: {len(chunks):,} chunks")
        print(f"   Characters:   {chunks_with_characters:,} chunks ({chunks_with_characters/len(chunks)*100:.1f}%)")
        if chunks_with_characters > 0:
            print(f"               Avg per chunk: {total_concept_mentions/chunks_with_characters:.1f}")
        print(f"   Concepts:   {chunks_with_concepts:,} chunks ({chunks_with_concepts/len(chunks)*100:.1f}%)")
        if chunks_with_concepts > 0:
            print(f"               Avg per chunk: {total_concept_mentions/chunks_with_concepts:.1f}")
        print(f"   Magic:      {chunks_with_magic:,} chunks ({chunks_with_magic/len(chunks)*100:.1f}%)")
        if chunks_with_magic > 0:
            print(f"               Avg per chunk: {total_magic_mentions/chunks_with_magic:.1f}")
        print(f"   Prophecies: {chunks_with_prophecies:,} chunks ({chunks_with_prophecies/len(chunks)*100:.1f}%)")
        if chunks_with_prophecies > 0:
            print(f"               Avg per chunk: {total_prophecy_mentions/chunks_with_prophecies:.1f}")
        
        return {
            'total': len(chunks),
            'with_characters': chunks_with_characters,
            'total_characters': total_character_mentions,
            'with_concepts': chunks_with_concepts,
            'total_concepts': total_concept_mentions,
            'with_magic': chunks_with_magic,
            'total_magic': total_magic_mentions,
            'with_prophecies': chunks_with_prophecies,
            'total_prophecies': total_prophecy_mentions
        }

def main():
    """Main execution."""
    config = get_config()
    
    print("=" * 80)
    print("CONCEPT, MAGIC & PROPHECY TAGGING - Week 4 Goal 4 (v2.0)")
    print("=" * 80)
    print("Adding concept_mentions, magic_mentions, and prophecy_mentions to all chunks")
    
    # Initialize tagger
    tagger = ConceptMagicProphecyTagger()
    
    # All chunk files to tag
    chunk_files = [
        (config.FILE_BOOK_CHUNKS, "Books"),
        (config.FILE_WIKI_CHUNKS_CHAPTER_SUMMARY, "Wiki Chapter Summary"),
        (config.FILE_WIKI_CHUNKS_CHRONOLOGY, "Wiki Chronology"),
        (config.FILE_WIKI_CHUNKS_CHARACTER, "Wiki Character"),
        (config.FILE_WIKI_CHUNKS_CONCEPT, "Wiki Concept"),
        (config.FILE_WIKI_CHUNKS_MAGIC, "Wiki Magic"),
        (config.FILE_WIKI_CHUNKS_PROPHECIES, "Wiki Prophecy"),
    ]
    
    results = {}
    
    for file_path, chunk_type in chunk_files:
        if not file_path.exists():
            print(f"\n⚠️  Warning: {file_path.name} not found, skipping")
            continue
        
        stats = tagger.enrich_chunk_file(file_path, chunk_type)
        results[chunk_type] = stats
    
    # Summary
    print("\n" + "=" * 80)
    print("TAGGING SUMMARY")
    print("=" * 80)
    
    total_chunks = sum(r['total'] for r in results.values())
    total_with_characters = sum(r['with_characters'] for r in results.values())
    total_with_concepts = sum(r['with_concepts'] for r in results.values())
    total_with_magic = sum(r['with_magic'] for r in results.values())
    total_with_prophecies = sum(r['with_prophecies'] for r in results.values())
    total_characters = sum(r['total_characters'] for r in results.values())
    total_concepts = sum(r['total_concepts'] for r in results.values())
    total_magic = sum(r['total_magic'] for r in results.values())
    total_prophecies = sum(r['total_prophecies'] for r in results.values())
    
    print(f"\n✅ Tagged {total_chunks:,} total chunks")
    print(f"✅ {total_with_characters:,} chunks with characters mentions ({total_with_characters/total_chunks*100:.1f}%)")
    print(f"   {total_characters:,} total character mention instances")
    print(f"✅ {total_with_concepts:,} chunks with concept mentions ({total_with_concepts/total_chunks*100:.1f}%)")
    print(f"   {total_concepts:,} total concept mention instances")
    print(f"✅ {total_with_magic:,} chunks with magic mentions ({total_with_magic/total_chunks*100:.1f}%)")
    print(f"   {total_magic:,} total magic mention instances")
    print(f"✅ {total_with_prophecies:,} chunks with prophecy mentions ({total_with_prophecies/total_chunks*100:.1f}%)")
    print(f"   {total_prophecies:,} total prophecy mention instances")
    
    print("\nBreakdown by source:")
    print(f"{'Source':25} {'Total':>7} {'Characters':>12} {'Concepts':>12} {'Magic':>12} {'Prophecies':>12}")
    print("-" * 80)
    for chunk_type, stats in results.items():
        characters_pct = stats['with_characters']/stats['total']*100 if stats['total'] > 0 else 0
        concept_pct = stats['with_concepts']/stats['total']*100 if stats['total'] > 0 else 0
        magic_pct = stats['with_magic']/stats['total']*100 if stats['total'] > 0 else 0
        prophecy_pct = stats['with_prophecies']/stats['total']*100 if stats['total'] > 0 else 0
        
        print(f"{chunk_type:25} {stats['total']:7,} "
              f"{stats['with_characters']:7,} ({characters_pct:4.1f}%) "
              f"{stats['with_concepts']:7,} ({concept_pct:4.1f}%) "
              f"{stats['with_magic']:7,} ({magic_pct:4.1f}%) "
              f"{stats['with_prophecies']:7,} ({prophecy_pct:4.1f}%)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()