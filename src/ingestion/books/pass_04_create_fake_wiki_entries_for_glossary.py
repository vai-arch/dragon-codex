"""
Generate wiki stub files for unmatched glossary terms.

This script:
1. Loads the glossary-to-wiki mapping
2. Loads the unified glossary
3. For each unmatched term (null in mapping):
   - Creates a minimal wiki stub file
   - Adds appropriate categories
   - Includes glossary definition
   - Lists book sources
4. Saves to data/raw/wiki/

Usage:
    python generate_wiki_stubs.py
"""

import json
import sys
import logging
from pathlib import Path
from src.utils.config import Config
from src.utils.logger import setup_logging, get_logger
from typing import Dict, List

# Paths
WIKI_PATH = Config().WIKI_GLOSSARY_PATH

# Input/Output files
UNIFIED_GLOSSARY = Config().METADATA_BOOKS_PATH / "unified_glossary.json"
OUTPUT_MAPPIN = Config().METADATA_PATH / "glossary_to_wiki_mapping.json"

logger = get_logger(__name__)

# Category mapping for the 33 terms
TERM_CATEGORIES = {
    # Battle Cries / Old Tongue Phrases
    "Al Ellisande!": ["Old_Tongue", "Battle_Cries"],
    "Carai an Caldazar!": ["Old_Tongue", "Battle_Cries"],
    "Carai an Ellisande!": ["Old_Tongue", "Battle_Cries"],
    "Tai'shar": ["Old_Tongue", "Phrases"],
    "Do Miere A'vron": ["Old_Tongue", "Phrases"],
    "Tia mi aven Moridin isainde vadin": ["Old_Tongue", "Phrases"],
    
    # Titles / Military Ranks
    "Lance-Captain": ["Titles", "Military_Ranks"],
    "Sword-Captain": ["Titles", "Military_Ranks"],
    "Master of the Lances": ["Titles", "Military_Ranks"],
    "Standardbearer": ["Titles", "Military_Ranks"],
    "Armsmen": ["Military", "Groups"],
    "Head of the Great Council of Thirteen": ["Titles", "Seanchan"],
    
    # Groups / Organizations
    "Companions, the": ["Organizations", "Military"],
    "Leashed Ones": ["Groups", "Seanchan"],
    "Fetches": ["Shadow", "Groups"],
    "Treekillers": ["Groups"],
    "Sea Folk hierarchy": ["Organizations", "Sea_Folk"],
    
    # Concepts / Abstract
    "Great Pattern": ["Concepts", "Philosophy"],
    "Great Game, the": ["Concepts", "Politics"],
    "Covenant of the Ten Nations": ["History", "Concepts"],
    "Tree, the": ["Concepts", "Aiel"],
    "Treesong": ["Concepts", "Ogier"],
    "Sung Wood": ["Concepts", "Ogier"],
    "Succession": ["Concepts", "Politics"],
    "Forced": ["Concepts", "Aes_Sedai"],
    
    # Measurements / Units
    "Bittern": ["Measurements"],
    "Hide": ["Measurements"],
    "Kith": ["Measurements"],
    
    # Places / Things
    "Depository": ["Locations", "White_Tower"],
    "Stump": ["Concepts", "Ogier"],
    
    # Characters / Entities
    "Lady of the Shadows": ["Characters", "Shadow"],
    
    # Terms that might be errors but we'll create stubs anyway
    "Der'morat": ["Old_Tongue", "Glossary_Only"],
}


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


def create_wiki_filename(term: str) -> str:
    """
    Convert term to wiki filename.
    Uses simple underscore replacement.
    """
    # Normalize apostrophes
    term = term.replace(''', "'").replace(''', "'").replace('`', "'")
    
    # Replace spaces with underscores
    filename = term.replace(' ', '_') + '.txt'
    
    return filename


def generate_wiki_stub(term: str, glossary_data: Dict, categories: List[str]) -> str:
    """
    Generate wiki stub content for a glossary term.
    
    Args:
        term: Glossary term
        glossary_data: Full glossary entry data
        categories: List of category names
    
    Returns:
        Wiki page content as string
    """
    # Get data from glossary
    pronunciation = glossary_data.get('pronunciation', '')
    definition = glossary_data.get('definition', 'No definition available.')
    sources = glossary_data.get('sources', [])
    
    # Build categories list
    categories_list = ['Glossary_Only'] + categories
    categories_str = ', '.join(categories_list)
    
    # Build book sources list
    book_list = []
    for source in sources:
        book_num = source.get('book_number', '?')
        book_title = source.get('book_title', 'Unknown')
        book_list.append(f"- Book {book_num}: {book_title}")
    books_str = '\n'.join(book_list) if book_list else '- Source information not available'
    
    # Generate content
    content = f"""# {term}
<!-- Metadata -->
<!-- Auto-generated stub from glossary -->
<!-- Categories: {categories_str} -->

## Categories
{categories_str}

---

**{term}**{' (' + pronunciation + ')' if pronunciation else ''} is a term from the Wheel of Time glossaries.

## Definition

{definition}

## Appearances in Glossaries

{books_str}

---

*This page was auto-generated from glossary data. It may be incomplete or require additional information from the wiki community.*
"""
    
    return content


def save_wiki_stub(filename: str, content: str, wiki_path: Path):
    """Save wiki stub to file."""
    file_path = wiki_path / filename
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Created: {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to create {filename}: {e}")
        return False


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Dragon's Codex - Wiki Stub Generator")
    logger.info("=" * 60)
    
    # Check input file exists
    if not UNIFIED_GLOSSARY.exists():
        logger.error(f"Glossary not found: {UNIFIED_GLOSSARY}")
        return 1
    
    try:
        # Load glossary
        glossary = load_glossary(UNIFIED_GLOSSARY)
        
        # Get terms to process (from TERM_CATEGORIES)
        terms_to_create = list(TERM_CATEGORIES.keys())
        
        print(f"\nGenerating wiki stubs for {len(terms_to_create)} terms...")
        print("-" * 60)
        
        created_count = 0
        skipped_count = 0
        
        for term in terms_to_create:
            # Get glossary data
            if term not in glossary:
                logger.warning(f"Term not in glossary: {term}")
                skipped_count += 1
                continue
            
            glossary_data = glossary[term]
            
            # Get categories
            categories = TERM_CATEGORIES[term]
            
            # Generate filename
            filename = create_wiki_filename(term)
            
            # Check if file already exists
            if (WIKI_PATH / filename).exists():
                logger.info(f"Skipped (already exists): {filename}")
                skipped_count += 1
                continue
            
            # Generate content
            content = generate_wiki_stub(term, glossary_data, categories)
            
            # Save file
            if save_wiki_stub(filename, content, WIKI_PATH):
                created_count += 1
                print(f"✓ Created: {filename}")
            else:
                skipped_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("WIKI STUB GENERATION COMPLETE")
        print("=" * 60)
        print(f"Created: {created_count} files")
        print(f"Skipped: {skipped_count} files")
        print(f"Total terms: {len(terms_to_create)}")
        print("=" * 60)
        
        if created_count > 0:
            print(f"\n✓ Wiki stubs created in: {WIKI_PATH}")
            print("\nNext steps:")
            print("1. Re-run: python build_glossary_wiki_mapping.py")
            print("2. Should now have 100% match rate!")
        
        logger.info(f"\n✓ Generation complete! Created {created_count} stubs.")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)