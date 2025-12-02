"""
Build glossary-to-wiki filename mapping.

This script:
1. Loads unified glossary JSON (all terms from all books)
2. Tries various filename transformation strategies
3. Checks if corresponding wiki .txt file exists
4. Creates mapping: glossary_term -> wiki_filename (or null)
5. Reports statistics and unmatched terms

This is just for review purposes, the glossary_to_wiki_mapping.json is going to be used directly
The 32 unmatched terms will be handled in the next step by creating minimal wiki stubs for them.

THERE ARE 32 Terms Uunmatched (93.6%)
	Al Ellisande\!
	Carai an Caldazar\!
	Carai an Ellisande\!
	Covenant of the Ten Nations
	Great Pattern
	Bittern
	Do Miere A’vron
	Great Game, the
	Hide
	Kith
	Leashed Ones
	Sung Wood
	Tai’shar
	Tia mi aven Moridin isainde vadin
	Tree, the
	Treesong
	Fetches
	Treekillers
	Armsmen
	Companions, the
	Der’morat
	Lance-Captain
	Master of the Lances
	Sea Folk hierarchy
	Sword-Captain
	Depository
	Lady of the Shadows
	Stump
	Forced
	Standardbearer
	Succession
	Head of the Great Council of Thirteen

Usage:
    python build_glossary_wiki_mapping.py
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, Optional, Set, List
from src.utils.config import Config
from src.utils.logger import setup_logging, get_logger

# Paths
WIKI_PATH = Config().WIKI_PATH

# Input/Output files
UNIFIED_GLOSSARY = Config().METADATA_BOOKS_PATH / "unified_glossary.json"
OUTPUT_MAPPING = Config().METADATA_PATH / "glossary_to_wiki_mapping.json"

logger = get_logger(__name__)

def load_glossary(glossary_path: Path) -> Dict:
    """Load unified glossary JSON."""
    try:
        with open(glossary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded glossary: {len(data)} terms")
        return data
    except Exception as e:
        logger.error(f"Failed to load glossary from {glossary_path}: {e}")
        raise


def get_wiki_files(wiki_path: Path) -> Set[str]:
    """Get set of all wiki .txt filenames (lowercase for case-insensitive matching)."""
    try:
        files = set()
        for file_path in wiki_path.glob("*.txt"):
            files.add(file_path.name)
        logger.info(f"Found {len(files)} wiki files")
        return files
    except Exception as e:
        logger.error(f"Failed to get wiki files from {wiki_path}: {e}")
        raise


def try_transformations(term: str, wiki_files: Set[str]) -> Optional[str]:
    """
    Try various filename transformations to find matching wiki file.
    
    Returns:
        Wiki filename if found, None otherwise
    """

    # ========== ADD THIS FIRST (NORMALIZE APOSTROPHES) ==========
    # Normalize curly/smart apostrophes to straight apostrophes
    # Glossary has ' (U+2019) but filenames have ' (U+0027)
    term = term.replace("\u2019", "'")  
    term = term.replace("\u2018", "'")  
    term = term.replace("\u2019", "'")  
    term = term.replace("’", "'") 
    # ===========================================================

    # Examples: "Colavaere of House Saighan" → "Colavaere.txt"
    if ' of House ' in term:
        first_word = term.split()[0]  # Get just the first word
        candidate = f"{first_word}.txt"
        if candidate in wiki_files:
            return candidate
        
    # Special case: "Term, the" → "The_Term.txt"
    if term.endswith(', the'):
        base_term = term[:-5].strip()  # Remove ", the"
        candidate = f"The_{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate
        candidate = f"{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate
        
    # Special case: "Title, The" → "The_Title.txt" (capital T)
    if term.endswith(', The'):
        base_term = term[:-5].strip()  # Remove ", The"
        candidate = f"The_{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate  
          
    # Special case: "Title, A" → "A_Title.txt"
    if term.endswith(', A'):
        base_term = term[:-3].strip()  # Remove ", A"
        candidate = f"A_{base_term.replace(' ', '_')}.txt"
        if candidate in wiki_files:
            return candidate
        
    # Strategy 1: Terms with comma (Lastname, Firstname format)
    if ',' in term:
        # Example: "Adan, Heran" → "heran_adan.txt"
        parts = term.split(',', 1)
        if len(parts) == 2:
            lastname = parts[0].strip()
            firstname = parts[1].strip()
            
            # Try 1: Direct swap with original capitalization
            candidate = f"{firstname}_{lastname}.txt".replace(' ', '_')
            if candidate in wiki_files:
                return candidate
            
            # Try 2: Capitalize first letter of second part (for "the" → "The")
            if firstname and firstname[0].islower():
                second_part_cap = firstname[0].upper() + firstname[1:]
                candidate = f"{second_part_cap}_{lastname}.txt".replace(' ', '_')
                if candidate in wiki_files:
                    return candidate
                
            # Try 3: Just use first part (ignore title/descriptor after comma)
            # Handles: "Nisura, Lady" → "Nisura.txt"
            candidate = f"{lastname}.txt".replace(' ', '_')
            if candidate in wiki_files:
                return candidate
            # ===========================================
            
            # Try: firstname_lastname.txt (lowercase)
            candidate = f"{firstname.lower()}_{lastname.lower()}.txt"
            if candidate in wiki_files:
                return candidate
            
            # Try: Firstname_Lastname.txt (title case)
            candidate = f"{firstname}_{lastname}.txt"
            if candidate in wiki_files:
                return candidate
            
            # Special case: "Lastname, Title Firstname" → "Firstname_Lastname.txt"
            # Example: "Damodred, Lord Galadedrid" → "Galadedrid_Damodred.txt"
            firstname_words = firstname.split()
            if len(firstname_words) > 1:
                # Assume last word is the actual first name, rest are titles
                actual_firstname = firstname_words[-1]
                candidate = f"{actual_firstname}_{lastname}.txt"
                if candidate in wiki_files:
                    return candidate
    # Strategy 2: Regular terms (no comma)
    else:
       
        # Remove trailing ", the" if present
        cleaned = term
        
        # Try: Term_With_Spaces.txt (keep capitalization)
        candidate = cleaned.replace(' ', '_') + '.txt'
        if candidate in wiki_files:
            return candidate
        
        # Try: term_with_spaces.txt (lowercase)
        candidate = cleaned.lower().replace(' ', '_') + '.txt'
        if candidate in wiki_files:
            return candidate
        
        # Try: Term_With_Spaces.txt (title case each word)
        candidate = '_'.join(word.capitalize() for word in cleaned.split()) + '.txt'
        if candidate in wiki_files:
            return candidate
    
    # Strategy 3: Exact match (just add .txt)
    candidate = term + '.txt'
    if candidate in wiki_files:
        return candidate
    
    # Strategy 4: Direct underscore replacement
    candidate = term.replace(' ', '_') + '.txt'
    if candidate in wiki_files:
        return candidate
    
    # Strategy 5: Lowercase, direct underscore replacement
    candidate = term.lower().replace(' ', '_') + '.txt'
    if candidate in wiki_files:
        return candidate
    
    return None


def build_mapping(glossary: Dict, wiki_files: Set[str]) -> Dict[str, Optional[str]]:
    """
    Build mapping from glossary terms to wiki filenames.
    
    Returns:
        Dictionary: {term: wiki_filename or None}
    """
    mapping = {}
    matched_count = 0
    
    total = len(glossary)
    logger.info(f"Processing {total} glossary terms...")
    
    for i, (term, data) in enumerate(glossary.items(), 1):
        if i % 100 == 0:
            logger.info(f"Progress: {i}/{total} ({matched_count} matched so far)")
        
        # Try to find matching wiki file
        wiki_file = try_transformations(term, wiki_files)
        
        if wiki_file:
            mapping[term] = wiki_file
            matched_count += 1
            logger.debug(f"✓ Matched: {term} → {wiki_file}")
        else:
            mapping[term] = None
            logger.debug(f"✗ No match: {term}")
    
    logger.info(f"Matching complete: {matched_count}/{total} matched")
    return mapping


def print_statistics(mapping: Dict[str, Optional[str]]):
    """Print statistics about the mapping."""
    total = len(mapping)
    matched = sum(1 for v in mapping.values() if v is not None)
    unmatched = total - matched
    match_rate = (matched / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("GLOSSARY TO WIKI MAPPING STATISTICS")
    print("=" * 60)
    print(f"Total glossary terms: {total}")
    print(f"Matched: {matched} ({match_rate:.1f}%)")
    print(f"Unmatched: {unmatched} ({100-match_rate:.1f}%)")
    print("=" * 60)
    
    # Log to file too
    logger.info("=" * 60)
    logger.info(f"Total: {total}, Matched: {matched} ({match_rate:.1f}%), Unmatched: {unmatched}")
    logger.info("=" * 60)


def print_unmatched(mapping: Dict[str, Optional[str]], max_display: int = 50):
    """Print list of unmatched terms."""
    unmatched = [term for term, wiki_file in mapping.items() if wiki_file is None]
    
    if not unmatched:
        print("\n✓ All terms matched!")
        logger.info("All terms matched!")
        return
    
    print(f"\nUNMATCHED TERMS ({len(unmatched)} total):")
    print("-" * 60)
    
    for i, term in enumerate(unmatched[:max_display], 1):
        print(f"{i:3d}. {term}")
    
    if len(unmatched) > max_display:
        print(f"... and {len(unmatched) - max_display} more")
    
    print("-" * 60)
    
    # Log all unmatched to file
    logger.info(f"\nAll {len(unmatched)} unmatched terms:")
    for term in unmatched:
        logger.info(f"  - {term}")


def save_mapping(mapping: Dict[str, Optional[str]], output_path: Path):
    """Save mapping to JSON file."""
    try:
        # Sort by key for readability
        sorted_mapping = dict(sorted(mapping.items()))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_mapping, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Mapping saved to: {output_path}")
        print(f"\n✓ Mapping saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save mapping: {e}")
        raise


def analyze_patterns(mapping: Dict[str, Optional[str]]):
    """Analyze and report which transformation patterns worked."""
    patterns = {
        'swap_lowercase': 0,
        'keep_comma_titlecase': 0,
        'swap_titlecase': 0,
        'underscore_keepcase': 0,
        'underscore_lowercase': 0,
        'exact': 0,
        'other': 0
    }
    
    for term, wiki_file in mapping.items():
        if wiki_file is None:
            continue
        
        # Analyze which pattern matched
        if ',' in term:
            parts = term.split(',', 1)
            if len(parts) == 2:
                lastname = parts[0].strip()
                firstname = parts[1].strip()
                
                if wiki_file == f"{firstname.lower()}_{lastname.lower()}.txt":
                    patterns['swap_lowercase'] += 1
                elif wiki_file == f"{lastname},_{firstname}.txt":
                    patterns['keep_comma_titlecase'] += 1
                elif wiki_file == f"{firstname}_{lastname}.txt":
                    patterns['swap_titlecase'] += 1
                else:
                    patterns['other'] += 1
        else:
            cleaned = term
            if cleaned.endswith(', the'):
                cleaned = cleaned[:-5]
            cleaned = cleaned.strip()
            
            if wiki_file == cleaned.replace(' ', '_') + '.txt':
                patterns['underscore_keepcase'] += 1
            elif wiki_file == cleaned.lower().replace(' ', '_') + '.txt':
                patterns['underscore_lowercase'] += 1
            elif wiki_file == term + '.txt':
                patterns['exact'] += 1
            else:
                patterns['other'] += 1
    
    print("\nMATCH STRATEGY BREAKDOWN:")
    print("-" * 60)
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"{pattern:25s}: {count:4d} terms")
    print("-" * 60)
    
    logger.info("\nMatch strategy breakdown:")
    for pattern, count in patterns.items():
        if count > 0:
            logger.info(f"  {pattern}: {count}")


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Dragon's Codex - Glossary to Wiki Mapping Builder")
    logger.info("=" * 60)
    
    # Check input file exists
    if not UNIFIED_GLOSSARY.exists():
        logger.error(f"Unified glossary not found: {UNIFIED_GLOSSARY}")
        logger.error("Please ensure unified_glossary.json exists in data/metadata/books/")
        return 1
    
    # Check wiki directory exists
    if not WIKI_PATH.exists():
        logger.error(f"Wiki directory not found: {WIKI_PATH}")
        logger.error("Please ensure wiki .txt files are in data/raw/wiki/")
        return 1
    
    try:
        # Load data
        glossary = load_glossary(UNIFIED_GLOSSARY)
        wiki_files = get_wiki_files(WIKI_PATH)
        
        # Build mapping
        mapping = build_mapping(glossary, wiki_files)
        
        # Save mapping
        save_mapping(mapping, OUTPUT_MAPPING)
        
        # Print reports
        print_statistics(mapping)
        analyze_patterns(mapping)
        print_unmatched(mapping, max_display=50)
        
        logger.info("\n✓ Mapping complete!")
        print("\n✓ All done! Check the log for full details.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)