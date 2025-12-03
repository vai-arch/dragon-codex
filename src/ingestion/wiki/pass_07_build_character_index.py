"""
Dragon's Codex - Character Index Builder
Builds comprehensive character index with aliases, abilities, and book appearances.

Extracts from:
- wiki_character.json (2,450 character pages)
- wiki_chronology.json (5 major character chronologies)
- redirect_mapping.json (2,850+ redirects for aliases)
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime


    #     print("    data/metadata/character_index.json")
    #     sys.exit(1)
from src.utils.config import Config

character_file = Config().FILE_WIKI_CHARACTER
chronology_file = Config().FILE_WIKI_CHRONOLOGY
redirect_file = Config().FILE_REDIRECT_MAPPING
output_file = Config().FILE_CHARACTER_INDEX

# Known major titles to look for
MAJOR_TITLES = [
    'Dragon Reborn',
    'Amyrlin Seat',
    "Car'a'carn",
    'King of Illian',
    'King of Andor',
    'Queen of Andor',
    'Lord of the Two Rivers',
    'Prince of the Ravens',
    'The Prophet',
    'First Counsel',
    'M\'Hael',
    'Captain-General',
]

# Title acquisition keywords
TITLE_KEYWORDS = [
    'became', 'proclaimed', 'crowned', 'named', 'declared',
    'raised', 'chosen', 'elected', 'appointed'
]


def load_data(character_file, chronology_file, redirect_file):
    """
    Load all required data files.
    
    Args:
        character_file: Path to wiki_character.json
        chronology_file: Path to wiki_chronology.json
        redirect_file: Path to redirect_mapping.json
        
    Returns:
        tuple: (characters, chronologies, redirects)
    """
    print(f"\n📂 Loading data files...")
    
    with open(character_file, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    print(f"   ✓ Loaded {len(characters):,} character pages")
    
    with open(chronology_file, 'r', encoding='utf-8') as f:
        chronologies = json.load(f)
    print(f"   ✓ Loaded {len(chronologies):,} chronology pages")
    
    with open(redirect_file, 'r', encoding='utf-8') as f:
        redirects = json.load(f)
    print(f"   ✓ Loaded {len(redirects):,} redirects")
    
    return characters, chronologies, redirects


def normalize_name(name):
    """
    Normalize character name for matching.
    
    Args:
        name: Character name string
        
    Returns:
        str: Normalized name
    """
    # Remove file extension
    name = name.replace('.txt', '')
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    return name


def build_reverse_redirect_map(redirects):
    """
    Build reverse mapping: character_name -> [list of aliases/redirects].
    
    Args:
        redirects: Dict of redirect_from -> redirect_to
        
    Returns:
        dict: character_name -> [aliases]
    """
    print(f"\n🔄 Building reverse redirect map...")
    
    reverse_map = defaultdict(list)
    
    for redirect_from, redirect_to in redirects.items():
        # Normalize both names
        target = normalize_name(redirect_to)
        alias = normalize_name(redirect_from)
        
        # Don't add if alias is the same as target
        if alias.lower() != target.lower():
            reverse_map[target].append(alias)
    
    # Count how many characters have aliases
    chars_with_aliases = sum(1 for aliases in reverse_map.values() if aliases)
    print(f"   ✓ {chars_with_aliases:,} characters have aliases")
    print(f"   ✓ Average aliases per character: {len(redirects) / max(chars_with_aliases, 1):.1f}")
    
    return dict(reverse_map)


def extract_books_appeared(char_data):
    """
    Extract list of book numbers where character appears.
    
    Args:
        char_data: Parsed character data
        
    Returns:
        list: Sorted list of book numbers
    """
    books = set()
    
    # From temporal sections
    for section in char_data.get('temporal_sections', []):
        book_num = section.get('book_number')
        if book_num is not None:
            books.add(book_num)
    
    return sorted(list(books))


def extract_abilities(char_data):
    """
    Extract character abilities from categories and content.
    
    Args:
        char_data: Parsed character data
        
    Returns:
        dict: Abilities dictionary (only non-empty)
    """
    abilities = {}
    categories = char_data.get('metadata', {}).get('categories', [])
    
    # From categories
    if 'Channelers' in categories or 'Aes_Sedai' in categories or 'Asha\'man' in categories:
        # Determine channeling type
        if 'Men' in categories:
            abilities['channeling'] = 'saidin'
        elif 'Women' in categories:
            abilities['channeling'] = 'saidar'
        else:
            abilities['channeling'] = 'unknown'
    
    if 'Ta\'veren' in categories:
        abilities['ta_veren'] = True
    
    if 'Dreamers' in categories:
        abilities['dreamer'] = True
    
    if 'Wolfbrothers' in categories:
        abilities['wolfbrother'] = True
    
    # Look for ability/power related sections
    for section in char_data.get('non_temporal_sections', []):
        section_title = section.get('section_title', '').lower()
        content = section.get('content', '').lower()
        
        if 'abilit' in section_title or 'power' in section_title or 'channel' in section_title:
            # Try to extract strength
            if abilities.get('channeling'):
                if 'very strong' in content or 'extremely strong' in content:
                    abilities['strength'] = 'very strong'
                elif 'strong' in content or 'powerful' in content:
                    abilities['strength'] = 'strong'
                elif 'weak' in content:
                    abilities['strength'] = 'weak'
            
            # Look for specific talents
            talents = []
            if 'traveling' in content or 'gateway' in content:
                talents.append('Traveling')
            if 'healing' in content:
                talents.append('Healing')
            if 'balefire' in content:
                talents.append('Balefire')
            if 'compulsion' in content:
                talents.append('Compulsion')
            
            if talents:
                abilities['talents'] = talents
    
    return abilities  # Returns empty dict if no abilities


def extract_titles(char_data):
    """
    Extract character titles and when they were acquired.
    
    Args:
        char_data: Parsed character data
        
    Returns:
        list: List of title dicts [{title, acquired_book, source}]
    """
    titles = []
    
    # Search in temporal sections for title mentions
    for section in char_data.get('temporal_sections', []):
        content = section.get('content', '')
        book_number = section.get('book_number')
        book_title = section.get('book_title', '')
        
        # Look for major titles
        for major_title in MAJOR_TITLES:
            # Check if title appears in content
            if major_title.lower() in content.lower():
                # Look for acquisition keywords nearby
                for keyword in TITLE_KEYWORDS:
                    pattern = f"{keyword}[^.]*{major_title}"
                    if re.search(pattern, content, re.IGNORECASE):
                        titles.append({
                            'title': major_title,
                            'acquired_book': book_number,
                            'source': book_title
                        })
                        break  # Found acquisition, move to next title
                else:
                    # Title mentioned but no clear acquisition
                    # Only add if not already in list
                    if not any(t['title'] == major_title for t in titles):
                        titles.append({
                            'title': major_title,
                            'source': book_title
                        })
    
    # Also check non-temporal sections for title mentions
    for section in char_data.get('non_temporal_sections', []):
        section_title = section.get('section_title', '').lower()
        content = section.get('content', '')
        
        # Look in titles/background sections
        if 'title' in section_title or 'background' in section_title:
            for major_title in MAJOR_TITLES:
                if major_title.lower() in content.lower():
                    # Don't duplicate
                    if not any(t['title'] == major_title for t in titles):
                        titles.append({'title': major_title})
    
    return titles  # Returns empty list if no titles


def process_characters(characters, chronologies, reverse_redirects):
    """
    Process all characters to build index.
    
    Args:
        characters: Dict of character pages
        chronologies: Dict of chronology pages
        reverse_redirects: Dict of character -> [aliases]
        
    Returns:
        dict: Complete character index
    """
    print(f"\n⚙️  Processing {len(characters):,} characters...")
    
    character_index = {}
    
    # Track statistics
    stats = {
        'total': 0,
        'with_chronology': 0,
        'with_books': 0,
        'with_aliases': 0,
        'with_abilities': 0,
        'with_titles': 0,
        'channelers': 0,
        'ta_veren': 0
    }
    
    for filename, char_data in characters.items():
        character_name = char_data.get('character_name')
        if not character_name:
            continue
        
        stats['total'] += 1
        
        # Build index entry
        index_entry = {
            'primary_name': character_name,
            'filename': filename,
            'page_type': char_data.get('page_type', 'CHARACTER')
        }
        
        # Extract books appeared
        books = extract_books_appeared(char_data)
        
        # Check for chronology page
        chronology_name = filename.replace('.txt', '_Chronology.txt')
        if chronology_name in chronologies:
            index_entry['has_chronology'] = True
            index_entry['chronology_file'] = chronology_name
            stats['with_chronology'] += 1
            
            # Merge books from chronology
            chrono_books = extract_books_appeared(chronologies[chronology_name])
            books = sorted(set(books + chrono_books))
        
        # Only add books if not empty
        if books:
            index_entry['books_appeared'] = books
            stats['with_books'] += 1
        
        # Get aliases from redirects
        normalized_name = normalize_name(character_name)
        aliases = reverse_redirects.get(normalized_name, [])
        
        # Also check by filename
        normalized_filename = normalize_name(filename)
        if normalized_filename != normalized_name:
            aliases.extend(reverse_redirects.get(normalized_filename, []))
        
        # Remove duplicates
        aliases = list(set(aliases))
        
        if aliases:
            index_entry['aliases'] = sorted(aliases)
            stats['with_aliases'] += 1
        
        # Extract abilities
        abilities = extract_abilities(char_data)
        if abilities:
            index_entry['abilities'] = abilities
            stats['with_abilities'] += 1
            
            if abilities.get('channeling'):
                stats['channelers'] += 1
            if abilities.get('ta_veren'):
                stats['ta_veren'] += 1
        
        # Extract titles
        titles = extract_titles(char_data)
        if titles:
            index_entry['titles'] = titles
            stats['with_titles'] += 1
        
        # Add categories
        categories = char_data.get('metadata', {}).get('categories', [])
        if categories:
            index_entry['categories'] = categories
        
        # Add to index
        character_index[character_name] = index_entry
        
        # Progress indicator
        if stats['total'] % 500 == 0:
            print(f"   Processed {stats['total']:,} characters...")
    
    print(f"\n✅ Processed all {stats['total']:,} characters")
    print(f"\n📊 Statistics:")
    print(f"   Characters with chronology pages:  {stats['with_chronology']:3,}")
    print(f"   Characters with book appearances:  {stats['with_books']:3,}")
    print(f"   Characters with aliases:           {stats['with_aliases']:3,}")
    print(f"   Characters with abilities:         {stats['with_abilities']:3,}")
    print(f"   Characters with titles:            {stats['with_titles']:3,}")
    print(f"   Channelers:                        {stats['channelers']:3,}")
    print(f"   Ta'veren:                          {stats['ta_veren']:3,}")
    
    return character_index, stats


def validate_major_characters(character_index):
    """
    Deep validation of the 5 major characters.
    
    Args:
        character_index: Complete character index
        
    Returns:
        bool: Validation passed
    """
    print(f"\n🔍 Validating major characters...")
    
    major_characters = [
        "Rand al'Thor",
        "Mat Cauthon",
        "Perrin Aybara",
        "Egwene al'Vere",
        "Elayne Trakand"
    ]
    
    validation_passed = True
    
    for char_name in major_characters:
        print(f"\n   {char_name}:")
        
        if char_name not in character_index:
            print(f"      ❌ NOT FOUND in index!")
            validation_passed = False
            continue
        
        char = character_index[char_name]
        
        # Check chronology
        if char.get('has_chronology'):
            print(f"      ✓ Has chronology page: {char['chronology_file']}")
        else:
            print(f"      ⚠️  No chronology page")
        
        # Check books
        books = char.get('books_appeared', [])
        if books:
            print(f"      ✓ Appears in {len(books)} books: {books}")
        else:
            print(f"      ⚠️  No book appearances recorded")
        
        # Check aliases
        aliases = char.get('aliases', [])
        if aliases:
            print(f"      ✓ {len(aliases)} aliases: {aliases[:3]}...")
        else:
            print(f"      ⚠️  No aliases found")
        
        # Check abilities
        abilities = char.get('abilities', {})
        if abilities:
            print(f"      ✓ Abilities: {', '.join(abilities.keys())}")
        else:
            print(f"      ⚠️  No abilities detected")
        
        # Check titles
        titles = char.get('titles', [])
        if titles:
            title_names = [t['title'] for t in titles]
            print(f"      ✓ {len(titles)} titles: {title_names}")
        else:
            print(f"      ⚠️  No titles found")
    
    if validation_passed:
        print(f"\n   ✅ All major characters validated!")
    else:
        print(f"\n   ⚠️  Some validation issues found")
    
    return validation_passed


def save_character_index(character_index, stats, output_file):
    """
    Save character index to JSON file.
    
    Args:
        character_index: Complete character index
        stats: Statistics dict
        output_file: Output file path
    """
    print(f"\n💾 Saving character index to: {output_file}")
    
    # Save main index
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(character_index, f, indent=2, ensure_ascii=False)
    
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"   ✓ Saved {len(character_index):,} characters ({file_size:.2f} MB)")
    
    # Save summary statistics
    stats_file = str(output_file).replace('.json', '_stats.txt')
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("CHARACTER INDEX STATISTICS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Total characters indexed:           {stats['total']:5,}\n")
        f.write(f"Characters with chronology pages:   {stats['with_chronology']:5,}\n")
        f.write(f"Characters with book appearances:   {stats['with_books']:5,}\n")
        f.write(f"Characters with aliases:            {stats['with_aliases']:5,}\n")
        f.write(f"Characters with abilities:          {stats['with_abilities']:5,}\n")
        f.write(f"Characters with titles:             {stats['with_titles']:5,}\n")
        f.write(f"Channelers:                         {stats['channelers']:5,}\n")
        f.write(f"Ta'veren:                           {stats['ta_veren']:5,}\n")
    
    print(f"   ✓ Saved statistics to: {stats_file}")


def main():
    """Main character indexing function."""
    import sys
    
    print("\n" + "="*80)
    print("DRAGON'S CODEX - CHARACTER INDEX BUILDER")
    print("="*80)
    
    print(f"\n📂 Configuration:")
    print(f"   Character file:   {character_file}")
    print(f"   Chronology file:  {chronology_file}")
    print(f"   Redirect file:    {redirect_file}")
    print(f"   Output file:      {output_file}")
    
    start_time = datetime.now()
    
    # Step 1: Load data
    characters, chronologies, redirects = load_data(
        character_file, chronology_file, redirect_file
    )
    
    # Step 2: Build reverse redirect map
    reverse_redirects = build_reverse_redirect_map(redirects)
    
    # Step 3: Process all characters
    character_index, stats = process_characters(
        characters, chronologies, reverse_redirects
    )
    
    # Step 4: Validate major characters
    validate_major_characters(character_index)
    
    # Step 5: Save index
    save_character_index(character_index, stats, output_file)
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*80)
    print("CHARACTER INDEX COMPLETE!")
    print("="*80)
    print(f"\n⏱️  Total time: {duration}")
    print(f"📊 Characters indexed: {len(character_index):,}")
    print(f"\n✅ Week 3 Goal 3: COMPLETE!\n")


if __name__ == "__main__":
    main()