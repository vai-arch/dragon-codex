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


BOOK_NUMBER_MAP = {
    "New Spring": 0,
    "The Eye of the World": 1,
    "The Great Hunt": 2,
    "The Dragon Reborn": 3,
    "The Shadow Rising": 4,
    "The Fires of Heaven": 5,
    "Lord of Chaos": 6,
    "A Crown of Swords": 7,
    "The Path of Daggers": 8,
    "Winter's Heart": 9,
    "Crossroads of Twilight": 10,
    "Knife of Dreams": 11,
    "The Gathering Storm": 12,
    "Towers of Midnight": 13,
    "A Memory of Light": 14,
    # Abbreviations
    "NS": 0,
    "TEOTW": 1,
    "TGH": 2,
    "TDR": 3,
    "TSR": 4,
    "TFOH": 5,
    "LOC": 6,
    "ACOS": 7,
    "TPOD": 8,
    "WH": 9,
    "COT": 10,
    "KOD": 11,
    "TGS": 12,
    "TOM": 13,
    "AMOL": 14,
}

# Title to number mapping (for reverse lookup)
TITLE_TO_NUMBER = {title: num for num, title in BOOK_TITLES.items()}

EVENT_BOOK_MAP = {
    "moiraine and siuan become novices": 0,
    "white tower entry": 0,
    "tar valon": 0,
    "young channelers": 0,
    "moiraine born": 0,
    "cairhien": 0,
    "damodred family": 0,
    "future aes sedai": 0,
    "siuan born": 0,
    "tear": 0,
    "future amyrlin": 0,
    "lan born": 0,
    "malkier": 0,
    "last prince": 0,
    "future warder": 0,
    "nynaeve born": 1,
    "two rivers": 1,
    "future wisdom": 1,
    "min born": 1,
    "baerlon": 1,
    "viewings": 1,
    "future advisor": 1,
    "tenobia born": 1,
    "saldaea": 1,
    "future queen": 1,
    "rand born": 1,
    "dragonmount": 1,
    "dragon reborn": 1,
    "adopted by tam": 1,
    "perrin born": 1,
    "wolfbrother": 1,
    "future lord": 1,
    "mat born": 1,
    "future cairhienin lord": 1,
    "egwene born": 1,
    "emond's field": 1,
    "elayne born": 1,
    "caemlyn": 1,
    "faile born": 1,
    "future wife of perrin": 1,
    "aviendha born": 1,
    "aiel waste": 1,
    "future wise one": 1,
    "tuon born": 1,
    "seanchan": 1,
    "future empress": 1,
    "fall of malkier": 1,
    "blight invasion": 1,
    "kingdom destroyed": 1,
    "trolloc attack on two rivers": 1,
    "winternight": 1,
    "trollocs": 1,
    "myrddraal": 1,
    "escape from two rivers": 1,
    "portal stone": 1,
    "fal dara refuge": 1,
    "meeting with baerlon warder": 1,
    "ingtar": 1,
    "padan fain": 1,
    "darkfriend reveal": 1,
    "eye of the world confrontation": 1,
    "forsaken ba'alzamon": 1,
    "true power": 1,
    "rand's first channeling": 1,
    "rand learns of dragon prophecy": 1,
    "moiraine reveal": 1,
    "battle at emond's field": 1,
    "fades": 1,
    "villagers defend": 1,
    "flight to tar valon": 1,
    "grand alliance": 1,
    "white tower arrival": 1,
    "siuan and moiraine raised to shawl": 2,
    "blue ajah": 2,
    "accepted to aes sedai": 2,
    "great hunt begins": 2,
    "horn of valere": 2,
    "false dragons": 2,
    "rand pursues horn": 2,
    "shadar logoth": 2,
    "mashadar": 2,
    "infiltration of shadar logoth": 2,
    "mashadar possession": 2,
    "rand cursed": 2,
    "meeting with ogier": 2,
    "stedding": 2,
    "loial introduction": 2,
    "battle at falme": 2,
    "seanchan landing": 2,
    "a'dam use": 2,
    "treaty of falme": 2,
    "rand claims dragon banner": 2,
    "dragon reborn acceptance": 2,
    "followers gather": 2,
    "perrin's wolfbrother awakening": 2,
    "wolves": 2,
    "faile capture": 2,
    "egwene and nynaeve captured": 2,
    "red ajah imprisonment": 2,
    "rand's healing from curse": 3,
    "lanfear confrontation": 3,
    "saidin taint": 3,
    "rand's time in cairhien": 3,
    "car'a'carn title": 3,
    "aiel alliance": 3,
    "meeting with aes sedai sitters": 3,
    "hall of the tower": 3,
    "dragon debate": 3,
    "perrin's rescue of faile": 3,
    "whitecloaks": 3,
    "two rivers refugees": 3,
    "mat's escape from ebou dar": 3,
    "dice game": 3,
    "fleeing": 3,
    "rand battles lanfear": 3,
    "tel'aran'rhiod": 3,
    "dreamworld fight": 3,
    "discovery of black ajah": 3,
    "liandrin plot": 3,
    "tower infiltration": 3,
    "aiel war aftermath": 3,
    "cairhien destruction": 3,
    "laman's death": 3,
    "rand enters dragonmount": 3,
    "lews therin voices": 3,
    "identity struggle": 3,
    "fall of illian": 4,
    "shadowspawn siege": 4,
    "corlan dashiva": 4,
    "perrin becomes lord of the two rivers": 4,
    "saldaea alliance": 4,
    "faile marriage": 4,
    "rand's trip to rhuidean": 4,
    "aiel visions": 4,
    "past lives": 4,
    "battle at tarwin's gap": 4,
    "rand's forces": 4,
    "trolloc victory": 4,
    "egwene's tower training": 4,
    "novice to accepted": 4,
    "nynaeve healing": 4,
    "mat's campaign in altara": 4,
    "bandar eban capture": 4,
    "shadar logoth dagger threat": 4,
    "mashadar spread": 4,
    "containment efforts": 4,
    "flight from tar valon": 5,
    "black ajah coup": 5,
    "elaida's rise": 5,
    "nynaeve and elayne in cairhien": 5,
    "succession intrigues": 5,
    "rebel support": 5,
    "mat's alliance with sea folk": 5,
    "atha'an miere": 5,
    "ship battles": 5,
    "battle at cairhien walls": 5,
    "seanchan invasion": 5,
    "damane use": 5,
    "rand's meeting with min": 5,
    "ter'angreal discovery": 5,
    "forsaken rahvin's plot": 5,
    "caemlyn trap": 5,
    "rand ensnared": 5,
    "egwene's kidnapping": 5,
    "tower chaos": 5,
    "battle of the shining walls": 5,
    "aiel victory": 5,
    "laman killed": 5,
    "rand's battle with rahvin": 6,
    "forsaken death": 6,
    "seanchan conquest of caemlyn": 6,
    "imperial armies": 6,
    "andomaire": 6,
    "battle of dumai's wells": 6,
    "rand vs. demandred": 6,
    "a'dam breaking": 6,
    "perrin's black tower founding": 6,
    "male channelers": 6,
    "logain leadership": 6,
    "egwene's escape from tower": 6,
    "self-lashing": 6,
    "accepted promotion": 6,
    "mat's victory at falme": 6,
    "seanchan retreat": 6,
    "rand's treaty with aiel": 6,
    "waste access": 6,
    "clan unification": 6,
    "cleansing of saidin": 9,  # Corrected from errors
    "13x13 circle": 9,
    "taint removal": 9,
    "battle at the rock": 7,
    "whitecloaks assault": 7,
    "fortress siege": 7,
    "elayne's coronation in andor": 7,
    "lion throne": 7,
    "succession": 7,
    "min's viewing of dragon's peace": 7,
    "future visions": 7,
    "ter'angreal": 7,
    "egwene's rise to amyrlin": 7,
    "hall election": 7,
    "tower unification": 7,
    "rand's trip to tear": 7,
    "stone of tear": 7,
    "callandor claim": 7,
    "battle at tarwin's gap aftermath": 7,
    "border defenses": 7,
    "shadow advances": 7,
    "perrin's wolf dream visions": 7,
    "shara": 7,
    "future quests": 7,
    "mat's campaign against shadow": 7,
    "altara liberation": 7,
    "whitecloak defeats": 7,
    "forsaken ishamael's awakening": 7,
    "shadow leadership": 7,
    "plans": 7,
    "rand's battles with forsaken": 8,
    "semirhage captivity": 8,
    "rescue": 8,
    "sea folk alliance with westlands": 8,
    "ship deployments": 8,
    "shadow fights": 8,
    "egwene's tower reforms": 8,
    "sitters replacement": 8,
    "black ajah hunt": 8,
    "elayne's defense of andor": 8,
    "border wars": 8,
    "cairhien claims": 8,
    "perrin's attack on black tower": 8,
    "male aes sedai integration": 8,
    "mat's journey to ebou dar": 8,
    "seanchan politics": 8,
    "tuon meeting": 8,
    "rand's vision at dragonmount": 8,
    "future prophecies": 8,
    "alliances": 8,
    "battle at the aryth ocean": 8,
    "sea folk vs. shadow fleets": 8,
    "forsaken graendal's schemes": 8,
    "intrigues": 8,
    "pawn manipulations": 8,
    "winter's heart revelations": 9,
    "black ajah exposed": 9,
    "tower arrests": 9,
    "rand's confrontation with demandred": 9,
    "falme dream": 9,
    "future battle": 9,
    "egwene's battle for tower": 9,
    "siuan release": 9,
    "hall overthrow": 9,
    "healed mat": 3,
    "shadar logoth dagger": 3,
    "egwene's accepted test": 3,
    "dumai's wells": 6,
    "forced bond": 6,
    "far madding": 9,
    "shayol ghul": 14,
    "pit of doom": 14,
    "mat's marriage to tuon": 9,
    "seanchan customs": 9,
    "gholam attack": 9,
    "perrin's trials in two rivers": 9,
    "wolfkin": 9,
    "shara quest": 9,
    "rand's cleansing of shara": 9,
    "portal stones": 9,
    "shadowspawn fights": 9,
    "battle at the last battle site visions": 9,
    "prophecies": 9,
    "alliances forming": 9,
    "crossroads of twilight intrigues": 10,
    "forsaken escapes": 10,
    "tower divisions": 10,
    "egwene's captivity by black ajah": 10,
    "escape plans": 10,
    "mat's seanchan campaigns": 10,
    "empire politics": 10,
    "gholam pursuit": 10,
    "perrin's shara explorations": 10,
    "wolfbrother visions": 10,
    "new lands": 10,
    "rand's isolation at dragonmount": 10,
    "prophecies study": 10,
    "loneliness": 10,
    "knife of dreams battles": 11,
    "seanchan invasions": 11,
    "westlands defenses": 11,
    "egwene's return to tower": 11,
    "amyrlin strengthening": 11,
    "black ajah trials": 11,
    "mat's victory over gholam": 11,
    "assassination attempt": 11,
    "survival": 11,
    "perrin's battles in shara": 11,
    "seanchan allies": 11,
    "rand's alliances with aiel": 11,
    "clan unifications": 11,
    "waste campaigns": 11,
    "battle at cairhien": 11,
    "shadowspawn assaults": 11,
    "city defense": 11,
    "the gathering storm storms": 12,
    "everstorm": 12,
    # Add more if needed from future expansions
}
# Common title variations (for parsing wiki files)
TITLE_VARIATIONS = {
    "New Spring": ["New Spring", "new spring"],
    "The Eye of the World": ["The Eye of the World", "Eye of the World", "The Eye Of The World", "EOTW"],
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
        "Rand",
        "Rand al'Thor",
        "Dragon Reborn",
        "Car'a'carn",
        "Coramoor",
        "He Who Comes With the Dawn",
        "Lews Therin",
    ],
    "Egwene al'Vere": ["Egwene", "Egwene al'Vere", "Amyrlin Seat", "Amyrlin", "Mother", "Dreamer"],
    "Matrim Cauthon": ["Mat", "Mat Cauthon", "Matrim Cauthon", "Son of Battles", "Prince of the Ravens", "Gambler"],
    "Perrin Aybara": ["Perrin", "Perrin Aybara", "Young Bull", "Perrin Goldeneyes", "Lord Perrin", "Wolfbrother"],
    "Nynaeve al'Meara": ["Nynaeve", "Nynaeve al'Meara", "Nynaeve Mandragoran", "Wisdom", "Malkieri Queen"],
    "Elayne Trakand": ["Elayne", "Elayne Trakand", "Daughter-Heir", "Queen of Andor", "Aes Sedai"],
    "Aviendha": ["Aviendha", "Wise One"],
    "Min Farshaw": ["Min", "Min Farshaw", "Seer"],
    "Moiraine Damodred": ["Moiraine", "Moiraine Damodred", "Moiraine Sedai", "Aes Sedai"],
    "Lan Mandragoran": ["Lan", "al'Lan Mandragoran", "Warder", "King of Malkier", "Last King of Malkier", "Dai Shan"],
    "Thom Merrilin": ["Thom", "Thom Merrilin", "Gleeman", "Master Merrilin"],
}

# One Power and magic system terms
MAGIC_SYSTEM_TERMS = {
    "one_power": [
        "One Power",
        "True Source",
        "Power",
        "channeling",
        "channel",
        "saidin",
        "saidar",
        "weave",
        "weaves",
        "flows",
    ],
    "power_objects": [
        "angreal",
        "sa'angreal",
        "ter'angreal",
        "access key",
        "Choedan Kal",
        "seals",
        "Seals on the Dark One's prison",
    ],
    "abilities": [
        "Traveling",
        "Skimming",
        "Healing",
        "Delving",
        "Compulsion",
        "balefire",
        "Gateway",
        "Skim",
        "Shielding",
        "Stilling",
        "Gentling",
    ],
    "aes_sedai": [
        "Aes Sedai",
        "sister",
        "sisters",
        "Accepted",
        "Novice",
        "Three Oaths",
        "Warder bond",
        "Warder",
        "Amyrlin Seat",
    ],
    "ajah": [
        "Blue Ajah",
        "Red Ajah",
        "Green Ajah",
        "Yellow Ajah",
        "White Ajah",
        "Gray Ajah",
        "Brown Ajah",
        "Black Ajah",
    ],
    "organizations": [
        "White Tower",
        "Black Tower",
        "Asha'man",
        "Wise Ones",
        "Windfinders",
        "Kin",
        "Children of the Light",
        "Whitecloaks",
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
    "Two Rivers",
    "Emond's Field",
    "Baerlon",
    "Caemlyn",
    "Tar Valon",
    "White Tower",
    "Cairhien",
    "Tear",
    "Rhuidean",
    "Aiel Waste",
    "Shayol Ghul",
    "Shienar",
    "Fal Dara",
    "Far Madding",
    "Ebou Dar",
    "Salidar",
    "Black Tower",
    "Andor",
    "Cairhien",
    "Illian",
    "Tarabon",
    "Arad Doman",
    "Seanchan",
    "Amadicia",
    "Ghealdan",
]

# Special terms with apostrophes (for normalization)
APOSTROPHE_TERMS = [
    "al'Thor",
    "al'Vere",
    "al'Meara",
    "a'Vere",
    "Tel'aran'rhiod",
    "sa'angreal",
    "ter'angreal",
    "ta'veren",
    "Tar'mon'Gai'don",
    "Car'a'carn",
    "Aiel",
    "Aes'Sedai",
    "Dai'shan",
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
        "\u2018": "'",
        "\u2019": "'",
        "`": "'",
        "\u02bb": "'",
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
        "arc",
        "development",
        "journey",
        "becomes",
        "evolution",
        "character development",
        "grows",
        "changes",
    ],
    "concept": ["what is", "explain", "how does", "definition", "describe", "tell me about"],
    "prophecy": ["prophecy", "prophesy", "foretelling", "viewing", "predicted", "foreseen", "Karaethon", "Dream"],
    "magic": ["channeling", "weave", "One Power", "saidin", "saidar", "Power", "Aes Sedai", "Healing", "Traveling"],
    "timeline": ["when", "chronology", "order of events", "timeline", "sequence", "what happens in"],
    "relationship": ["relationship", "between", "connected", "with", "bond", "married", "love"],
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
