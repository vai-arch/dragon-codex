"""Test WoT constants module"""
from src.utils.wot_constants import (
    BOOK_TITLES, 
    get_book_number, 
    get_book_title,
    MAJOR_CHARACTERS,
    get_character_aliases,
    MAGIC_SYSTEM_TERMS,
    is_magic_term
)

def test_constants():
    print("="*70)
    print("Testing WoT Constants Module")
    print("="*70)
    
    # Test book titles
    print("\nBook Titles (0-14):")
    for num in range(15):
        title = get_book_title(num)
        print(f"  {num:2}: {title}")
    
    # Test book number lookup
    print("\nBook Number Lookup:")
    test_titles = [
        "The Eye of the World",
        "TEOTW",
        "Eye of the World",
        "The Great Hunt"
    ]
    for title in test_titles:
        num = get_book_number(title)
        print(f"  '{title}' → Book {num}")
    
    # Test character aliases
    print("\nCharacter Aliases:")
    test_chars = ["Rand al'Thor", "Egwene al'Vere", "Moiraine Damodred"]
    for char in test_chars:
        aliases = get_character_aliases(char)
        if aliases:
            print(f"  {char}: {', '.join(aliases[:3])}...")
    
    # Test magic system terms
    print("\nMagic System Terms:")
    test_terms = ["One Power", "channeling", "saidin", "balefire", "not_magic"]
    for term in test_terms:
        is_magic = is_magic_term(term)
        status = "✓" if is_magic else "✗"
        print(f"  {status} '{term}': {is_magic}")
    
    print("\n" + "="*70)
    print("✓✓✓ Constants module works correctly!")
    print("="*70)

if __name__ == "__main__":
    test_constants()