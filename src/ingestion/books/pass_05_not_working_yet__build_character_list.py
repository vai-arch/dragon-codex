"""
Build unified character list from all book glossaries.

Week 2 Session 2 - Dragon's Codex
Extracts character names from glossary sections of all 15 books.
"""

import json
import os
import traceback
from pathlib import Path
from collections import defaultdict
import re

def load_config():
    """Load basic configuration"""
    # Adjust these paths as needed
    return {
        'books_json_path': 'data/raw/books',
        'output_path': 'data/metadata/character_names_initial.json',
        'stats_path': 'data/metadata/character_extraction_stats.json'
    }

def is_character_entry(term: dict) -> bool:
    """
    Determine if a glossary entry is likely a character.
    
    WoT character indicators:
    - Contains names (capitalized words)
    - Has biographical info keywords
    - Not a place/object/concept
    """
    term_name = term.get('term', '')
    if isinstance(term_name, list):
        term_name = " ".join(term_name)  # or choose a different joiner
    else:
        term_name = str(term_name)

    description = term.get('description', '').strip().lower()
    
    # Skip empty entries
    if not term_name or not description:
        return False
    
    # Place/concept indicators (NOT characters)
    non_character_keywords = [
        'city', 'country', 'nation', 'place', 'region', 'land',
        'tower', 'palace', 'fortress', 'building',
        'object', 'artifact', 'weapon', 'angreal', 'ter\'angreal',
        'concept', 'power', 'weave', 'ability',
        'organization', 'group', 'order', 'society',
        'age', 'era', 'period', 'war', 'battle',
        'the one power', 'saidin', 'saidar', 'channeling'
    ]
    
    # Character indicators
    character_keywords = [
        'daughter of', 'son of', 'sister of', 'brother of',
        'wife of', 'husband of', 'mother of', 'father of',
        'queen', 'king', 'lord', 'lady', 'prince', 'princess',
        'aes sedai', 'warder', 'amyrlin', 'ajah',
        'wisdom', 'mayor', 'captain', 'general',
        'channeler', 'dreamer', 'wolfbrother', 'ta\'veren',
        'born in', 'raised in', 'trained',
        'he is', 'she is', 'he was', 'she was'
    ]
    
    # Check for non-character keywords
    for keyword in non_character_keywords:
        if keyword in description:
            # Some exceptions: "Queen of [place]" is still a character
            if any(char_kw in description for char_kw in ['queen', 'king', 'lord', 'lady']):
                continue
            return False
    
    # Check for character keywords
    for keyword in character_keywords:
        if keyword in description:
            return True
    
    # # Check if term looks like a person's name (capitalized, has spaces)
    # # WoT names often have apostrophes: al'Thor, a'Vere
    # name_pattern = r'^[A-Z][a-z]+(?:[\''][a-z]+)?(?:\s+[A-Z][a-z]+(?:[\''][a-z]+)?)*$'

    # Check if term looks like a person's name (capitalized, has spaces)
    # WoT names often have apostrophes: al'Thor, a'Vere
    name_pattern = r"^[A-Z][a-z]+(?:'[a-z]+)?(?:\s+[A-Z][a-z]+(?:'[a-z]+)?)*$"


    if re.match(name_pattern, term_name):
        # Additional check: if description mentions pronouns
        if any(pronoun in description for pronoun in ['he ', 'she ', 'his ', 'her ']):
            return True
    
    return False

def extract_character_aliases(term_name: str, description: str) -> list:
    """
    Extract potential aliases/titles from character description.
    
    Examples:
    - "also known as the Dragon Reborn"
    - "called the Amyrlin Seat"
    - "the Car'a'carn"
    """
    aliases = []
    
    # Common alias patterns
    alias_patterns = [
        r'also known as (?:the )?([A-Z][a-z\s\']+)',
        r'called (?:the )?([A-Z][a-z\s\']+)',
        r'known as (?:the )?([A-Z][a-z\s\']+)',
        r'the ([A-Z][a-z\s\']+)(?:,|\.|$)',
    ]
    
    for pattern in alias_patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        aliases.extend(matches)
    
    # Clean up aliases
    aliases = [alias.strip() for alias in aliases if len(alias.strip()) > 2]
    return list(set(aliases))  # Remove duplicates

def build_character_list(books_path: str) -> dict:
    """
    Build unified character list from all book glossaries.
    
    Returns dict with:
    - characters: list of character objects
    - stats: extraction statistics
    """
    characters = {}
    stats = {
        'books_processed': 0,
        'total_glossary_entries': 0,
        'characters_identified': 0,
        'characters_by_book': {},
        'duplicate_names': 0,
        'errors': []
    }
    
    # Get all JSON book files
    book_files = sorted(Path(books_path).glob('*.json'))
    
    print(f"\nProcessing {len(book_files)} books...")
    print("=" * 60)
    
    for book_file in book_files:
        try:
            with open(book_file, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            book_num = book_data.get('book_number', 'unknown')
            book_name = book_data.get('book_name', 'unknown')
            glossary = book_data.get('glossary', [])
            
            print(f"\nBook {book_num}: {book_name}")
            print(f"  Glossary entries: {len(glossary)}")
            
            stats['books_processed'] += 1
            stats['total_glossary_entries'] += len(glossary)
            
            book_characters = []
            
            # Process each glossary entry
            for entry in glossary:
                if is_character_entry(entry):
                    term_name = entry['term']
                    if isinstance(term_name, list):
                        term_name = " ".join(term_name)  # or choose a different joiner
                    else:
                        term_name = str(term_name)

                    term_name = term_name.rstrip(":")  # remove trailing colon
                    description = entry.get('description', '')
                    pronunciation = entry.get('pronunciation', '')
                    
                    # Extract aliases
                    aliases = extract_character_aliases(term_name, description)
                    
                    # Create character object
                    character = {
                        'name': term_name,
                        'pronunciation': pronunciation,
                        'aliases': aliases,
                        'first_mentioned_book': book_num,
                        'first_mentioned_book_name': book_name,
                        'books_appeared_in': [book_num],
                        'description_snippet': description[:200]  # First 200 chars
                    }
                    
                    # Add to character list (or update if exists)
                    if term_name in characters:
                        # Character already exists, update books appeared in
                        characters[term_name]['books_appeared_in'].append(book_num)
                        stats['duplicate_names'] += 1
                    else:
                        characters[term_name] = character
                        book_characters.append(term_name)
                        stats['characters_identified'] += 1
            
            stats['characters_by_book'][f"Book {book_num}"] = {
                'name': book_name,
                'new_characters': len(book_characters),
                'characters': book_characters[:10]  # First 10 for preview
            }
            
            print(f"  Characters identified: {len(book_characters)}")
            
        except Exception as e:
            error_msg = f"Error processing {book_file.name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            traceback.print_exc()
            stats['errors'].append(error_msg)
    
    return {
        'characters': list(characters.values()),
        'stats': stats
    }

def save_character_list(data: dict, output_path: str, stats_path: str):
    """Save character list and stats to JSON files"""
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save character list
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data['characters'], f, indent=2, ensure_ascii=False)
    
    # Save stats
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(data['stats'], f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Character list saved to: {output_path}")
    print(f"✅ Stats saved to: {stats_path}")

def print_summary(data: dict):
    """Print summary statistics"""
    stats = data['stats']
    characters = data['characters']
    
    print("\n" + "=" * 60)
    print("CHARACTER EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Books processed: {stats['books_processed']}")
    print(f"Total glossary entries: {stats['total_glossary_entries']}")
    print(f"Characters identified: {stats['characters_identified']}")
    print(f"Unique characters: {len(characters)}")
    print(f"Characters appearing in multiple books: {stats['duplicate_names']}")
    
    if stats['errors']:
        print(f"\n⚠️  Errors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:5]:
            print(f"  - {error}")
    
    # Show characters with most aliases
    print("\nCharacters with most aliases:")
    sorted_chars = sorted(characters, key=lambda c: len(c.get('aliases', [])), reverse=True)
    for char in sorted_chars[:5]:
        print(f"  {char['name']}: {', '.join(char.get('aliases', [])[:3])}")
    
    # Show characters appearing in most books
    print("\nCharacters appearing in most books:")
    sorted_chars = sorted(characters, key=lambda c: len(c.get('books_appeared_in', [])), reverse=True)
    for char in sorted_chars[:5]:
        books = len(char.get('books_appeared_in', []))
        print(f"  {char['name']}: {books} books")

def main():
    """Main execution"""
    config = load_config()
    
    print("Dragon's Codex - Character List Builder")
    print("Week 2 Session 2")
    print("=" * 60)
    
    # Build character list
    data = build_character_list(config['books_json_path'])
    
    # Save results
    save_character_list(
        data, 
        config['output_path'],
        config['stats_path']
    )
    
    # Print summary
    print_summary(data)
    
    print("\n" + "=" * 60)
    print("✅ Character list build complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()