"""
Dragon's Codex - Wheel of Time Constants
Contains WoT-specific constants, mappings, and reference data.
"""

# Book number to title mapping
BOOK_TITLES = {
    0: "New Spring",
    1: "The Eye of the World",
    2: "The Great Hunt",
    3: "The Dragon Reborn",
    4: "The Shadow Rising",
    5: "The Fires of Heaven",
    6: "Lord of Chaos",
    7: "A Crown of Swords",
    8: "The Path of Daggers",
    9: "Winter's Heart",
    10: "Crossroads of Twilight",
    11: "Knife of Dreams",
    12: "The Gathering Storm",
    13: "Towers of Midnight",
    14: "A Memory of Light",
}

# Title to number mapping (for reverse lookup)
TITLE_TO_NUMBER = {title: num for num, title in BOOK_TITLES.items()}

# Common title variations (for parsing wiki files)
TITLE_VARIATIONS = {
    "New Spring": ["New Spring", "new spring"],
    "The Eye of the World": ["The Eye of the World", "Eye of the World", 
                              "The Eye Of The World", "EOTW"],
    "The Great Hunt": ["The Great Hunt", "Great Hunt", "TGH"],
    "The Dragon Reborn": ["The Dragon Reborn", "Dragon Reborn", "TDR"],
    "The Shadow Rising": ["The Shadow Rising", "Shadow Rising", "TSR"],
    "The Fires of Heaven": ["The Fires of Heaven", "Fires of Heaven", "TFOH"],
    "Lord of Chaos": ["Lord of Chaos", "LOC"],
    "A Crown of Swords": ["A Crown of Swords", "Crown of Swords", "ACOS"],
    "The Path of Daggers": ["The Path of Daggers", "Path of Daggers", "TPOD"],
    "Winter's Heart": ["Winter's Heart", "Winters Heart", "WH"],
    "Crossroads of Twilight": ["Crossroads of Twilight", "COT"],
    "Knife of Dreams": ["Knife of Dreams", "KOD"],
    "The Gathering Storm": ["The Gathering Storm", "Gathering Storm", "TGS"],
    "Towers of Midnight": ["Towers of Midnight", "TOM"],
    "A Memory of Light": ["A Memory of Light", "Memory of Light", "AMOL"],
}

# Character name variations and aliases
MAJOR_CHARACTERS = {
    "Rand al'Thor": [
        "Rand", "Rand al'Thor", "Dragon Reborn", "Car'a'carn", 
        "Coramoor", "He Who Comes With the Dawn", "Lews Therin"
    ],
    "Egwene al'Vere": [
        "Egwene", "Egwene al'Vere", "Amyrlin Seat", "Amyrlin", 
        "Mother", "Dreamer"
    ],
    "Matrim Cauthon": [
        "Mat", "Mat Cauthon", "Matrim Cauthon", "Son of Battles",
        "Prince of the Ravens", "Gambler"
    ],
    "Perrin Aybara": [
        "Perrin", "Perrin Aybara", "Young Bull", "Perrin Goldeneyes",
        "Lord Perrin", "Wolfbrother"
    ],
    "Nynaeve al'Meara": [
        "Nynaeve", "Nynaeve al'Meara", "Nynaeve Mandragoran",
        "Wisdom", "Malkieri Queen"
    ],
    "Elayne Trakand": [
        "Elayne", "Elayne Trakand", "Daughter-Heir", 
        "Queen of Andor", "Aes Sedai"
    ],
    "Aviendha": [
        "Aviendha", "Wise One"
    ],
    "Min Farshaw": [
        "Min", "Min Farshaw", "Seer"
    ],
    "Moiraine Damodred": [
        "Moiraine", "Moiraine Damodred", "Moiraine Sedai", "Aes Sedai"
    ],
    "Lan Mandragoran": [
        "Lan", "al'Lan Mandragoran", "Warder", "King of Malkier",
        "Last King of Malkier", "Dai Shan"
    ],
    "Thom Merrilin": [
        "Thom", "Thom Merrilin", "Gleeman", "Master Merrilin"
    ],
}

# One Power and magic system terms
MAGIC_SYSTEM_TERMS = {
    "one_power": [
        "One Power", "True Source", "Power", "channeling", "channel",
        "saidin", "saidar", "weave", "weaves", "flows"
    ],
    "power_objects": [
        "angreal", "sa'angreal", "ter'angreal", "access key",
        "Choedan Kal", "seals", "Seals on the Dark One's prison"
    ],
    "abilities": [
        "Traveling", "Skimming", "Healing", "Delving", "Compulsion",
        "balefire", "Gateway", "Skim", "Shielding", "Stilling", "Gentling"
    ],
    "aes_sedai": [
        "Aes Sedai", "sister", "sisters", "Accepted", "Novice",
        "Three Oaths", "Warder bond", "Warder", "Amyrlin Seat"
    ],
    "ajah": [
        "Blue Ajah", "Red Ajah", "Green Ajah", "Yellow Ajah",
        "White Ajah", "Gray Ajah", "Brown Ajah", "Black Ajah"
    ],
    "organizations": [
        "White Tower", "Black Tower", "Asha'man", "Wise Ones",
        "Windfinders", "Kin", "Children of the Light", "Whitecloaks"
    ],
}

# Prophecy types
PROPHECY_TYPES = [
    "Karaethon Cycle",
    "Dark Prophecy",
    "Jendai Prophecy",
    "Min's Viewing",
    "Dreaming",
    "Foretelling",
]

# Major locations
MAJOR_LOCATIONS = [
    "Two Rivers", "Emond's Field", "Baerlon", "Caemlyn", "Tar Valon",
    "White Tower", "Cairhien", "Tear", "Rhuidean", "Aiel Waste",
    "Shayol Ghul", "Shienar", "Fal Dara", "Far Madding", "Ebou Dar",
    "Salidar", "Black Tower", "Andor", "Cairhien", "Illian",
    "Tarabon", "Arad Doman", "Seanchan", "Amadicia", "Ghealdan",
]

# Special terms with apostrophes (for normalization)
APOSTROPHE_TERMS = [
    "al'Thor", "al'Vere", "al'Meara", "a'Vere",
    "Tel'aran'rhiod", "sa'angreal", "ter'angreal",
    "ta'veren", "Tar'mon'Gai'don", "Car'a'carn",
    "Aiel", "Aes'Sedai", "Dai'shan",
]


def get_book_number(title):
    """
    Get book number from title (handles variations).
    
    Args:
        title: Book title (any variation)
    
    Returns:
        Book number (0-14) or -1 if not found
    """
    # Direct lookup
    if title in TITLE_TO_NUMBER:
        return TITLE_TO_NUMBER[title]
    
    # Check variations
    for canonical, variations in TITLE_VARIATIONS.items():
        if title in variations:
            return TITLE_TO_NUMBER[canonical]
    
    # Case-insensitive check
    title_lower = title.lower().strip()
    for canonical, variations in TITLE_VARIATIONS.items():
        if any(title_lower == v.lower() for v in variations):
            return TITLE_TO_NUMBER[canonical]
    
    return -1


def get_book_title(number):
    """
    Get book title from number.
    
    Args:
        number: Book number (0-14)
    
    Returns:
        Book title or None if not found
    """
    return BOOK_TITLES.get(number)


def is_prequel(book_number):
    """
    Check if a book number is the prequel.
    
    Args:
        book_number: Book number
    
    Returns:
        True if prequel (book 0), False otherwise
    """
    return book_number == 0


def normalize_apostrophes(text):
    """
    Normalize apostrophes in WoT terms for consistent searching.
    
    Args:
        text: Text containing WoT terms
    
    Returns:
        Text with normalized apostrophes
    """
    # Replace various apostrophe types with standard '
    replacements = {
        '\u2018': "'",
        '\u2019': "'",
        '`': "'",
        '\u02bb': "'",
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def get_character_aliases(character_name):
    """
    Get all known aliases for a character.
    
    Args:
        character_name: Primary character name
    
    Returns:
        List of aliases (empty if character not found)
    """
    return MAJOR_CHARACTERS.get(character_name, [])


def find_character_by_alias(alias):
    """
    Find primary character name from any alias.
    
    Args:
        alias: Any known alias
    
    Returns:
        Primary character name or None if not found
    """
    alias_lower = alias.lower().strip()
    
    for primary, aliases in MAJOR_CHARACTERS.items():
        if any(alias_lower == a.lower() for a in aliases):
            return primary
    
    return None


def is_magic_term(text):
    """
    Check if text contains magic system terminology.
    
    Args:
        text: Text to check
    
    Returns:
        True if contains magic terms, False otherwise
    """
    text_lower = text.lower()
    
    for category, terms in MAGIC_SYSTEM_TERMS.items():
        if any(term.lower() in text_lower for term in terms):
            return True
    
    return False


def get_magic_terms_in_text(text):
    """
    Extract all magic terms found in text.
    
    Args:
        text: Text to search
    
    Returns:
        List of magic terms found
    """
    text_lower = text.lower()
    found_terms = []
    
    for category, terms in MAGIC_SYSTEM_TERMS.items():
        for term in terms:
            if term.lower() in text_lower:
                found_terms.append(term)
    
    return found_terms


# Query classification keywords
QUERY_KEYWORDS = {
    "character_evolution": [
        "arc", "development", "journey", "becomes", "evolution",
        "character development", "grows", "changes"
    ],
    "concept": [
        "what is", "explain", "how does", "definition", "describe",
        "tell me about"
    ],
    "prophecy": [
        "prophecy", "prophesy", "foretelling", "viewing", "predicted",
        "foreseen", "Karaethon", "Dream"
    ],
    "magic": [
        "channeling", "weave", "One Power", "saidin", "saidar",
        "Power", "Aes Sedai", "Healing", "Traveling"
    ],
    "timeline": [
        "when", "chronology", "order of events", "timeline",
        "sequence", "what happens in"
    ],
    "relationship": [
        "relationship", "between", "connected", "with",
        "bond", "married", "love"
    ],
}


def classify_query(query):
    """
    Classify query type based on keywords.
    
    Args:
        query: Query string
    
    Returns:
        Query type (str) or "general" if no match
    """
    query_lower = query.lower()
    
    # Count matches for each type
    scores = {}
    for query_type, keywords in QUERY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[query_type] = score
    
    if scores:
        # Return type with highest score
        return max(scores.items(), key=lambda x: x[1])[0]
    
    return "general"


if __name__ == "__main__":
    # Test the constants module
    print("=" * 60)
    print("Dragon's Codex - WoT Constants Test")
    print("=" * 60)
    
    print("\n📚 Book Mapping Tests:")
    print(f"  Book 1: {get_book_title(1)}")
    print(f"  Book 0 (prequel): {get_book_title(0)}")
    print(f"  'The Great Hunt' = Book {get_book_number('The Great Hunt')}")
    print(f"  'EOTW' = Book {get_book_number('EOTW')}")
    
    print("\n👤 Character Tests:")
    rand_aliases = get_character_aliases("Rand al'Thor")
    print(f"  Rand al'Thor aliases: {rand_aliases[:3]}...")
    print(f"  'Dragon Reborn' refers to: {find_character_by_alias('Dragon Reborn')}")
    
    print("\n✨ Magic System Tests:")
    test_text = "Rand channeled saidin and created a gateway using Traveling."
    print(f"  Text: '{test_text}'")
    print(f"  Is magic-related: {is_magic_term(test_text)}")
    print(f"  Terms found: {get_magic_terms_in_text(test_text)}")
    
    print("\n🔮 Query Classification Tests:")
    queries = [
        "How does Rand's character develop?",
        "What is the One Power?",
        "Tell me about the Dragon Reborn prophecy",
        "When does the Battle of Falme happen?",
    ]
    for q in queries:
        print(f"  '{q}'")
        print(f"    → {classify_query(q)}")
    
    print("\n✓ Constants test complete!")
