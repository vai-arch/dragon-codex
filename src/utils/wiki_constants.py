import re
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger
from src.utils.util_files_functions import load_json_from_file

logger = get_logger(__name__)


def define_taxonomy():
    """Define concept taxonomy - which categories belong to which groups"""


# AJAH
AJAHS = {
    "Yellow_Ajah",
    "Blue_Ajah",
    "Green_Ajah",
    "Red_Ajah",
    "White_Ajah",
    "Brown_Ajah",
    "Gray_Ajah",
    "Black_Ajah",
}

# ALIGNMENT (dark-side)
ALIGNMENT_DARK = {
    "Darkfriends",
    "The_Shadow",
    "Black_Ajah",
    "Forsaken",
    "Dreadlords",
    "The_Turned",
    "Chosen",
}

# CHANNELING AFFILIATIONS
CHANNELING_AFFILIATIONS = {
    "Aes_Sedai",
    "Asha'man",
    "Wilders",
    "Kinswomen",
    "Windfinders",
    "Wise_Ones",
    "Damane",
    "Sul'dam",
    "Dreadlords",
    "Forsaken",
    "Ayyad",
    "The_Turned",
    "Channelers",
    "Sparkers",
    "Learners",
    "Accepted",
    "Novices",
    "Tower_initiates",
    "Asha'man_(rank)",
    "Dedicated",
    "Soldier_(Asha'man)",
    "Accepted",
}

# CULTURAL GROUPS
CULTURAL_GROUPS = {
    "Aiel",
    "Ogier",
    "Tuatha'an",
    "Seanchan",
    "Atha'an_Miere",
    "Da'shain_Aiel",
    "Jenn_Aiel",
    "Tinkers",
}

# GENDER
GENDERS = {"Men", "Women"}

# MILITARY GROUPS
MILITARY_GROUPS = {
    "Warders",
    "Deathwatch_Guards",
    "Ever_Victorious_Army",
    "Five_Great_Captains",
    "Winged_Guard",
    "Band_of_the_Red_Hand",
    "Tower_Guards",
    "Queen's_Guards",
    "Redarms",
}

# MILITARY ROLES
MILITARY_ROLES = {
    "Generals",
    "Captains",
    "Five_Great_Captains",
    "Lord_Captain",
    "Lord_Captain_Commanders",
    "Warriors",
}

# ORGANIZATIONS: Important WoT groups and factions
ORGANIZATIONS = {
    # Aes Sedai factions
    "Aes_Sedai_factions",
    "Rand's_Aes_Sedai",
    "Rebel_Aes_Sedai",
    "Unaligned_sisters",
    "Elaida_a'Roihan's_White_Tower",
    # Military/Combat groups
    "Band_of_the_Red_Hand",
    "Redarms",
    "Children_of_the_Light",
    "Whitecloaks",
    "Dragonsworn",
    # Aiel societies and clans
    "Aiel_warrior_societies",
    "Aiel_clans",
    "Aiel_septs",
    "Far_Dareis_Mai",
    "Far_Aldazar_Din",
    "Aethan_Dor",
    "Duadhe_Mahdi'in",
    "Cor_Darei",
    "Hama_N'dore",
    "Seia_Doon",
    "Sha'mad_Conde",
    "Shae'en_M'taal",
    "Sovin_Nai",
    "Tain_Shari",
    "Mera'din",
    "Chareen",
    "Chumai",
    "Codarra",
    "Cosaida",
    "Daryne",
    "Degalle",
    "Domai",
    "Goshien",
    "Haido",
    "Imran",
    "Jarra",
    "Jenda",
    "Jhirad",
    "Jindo",
    "Jumai",
    "Miagoma",
    "Moshaine",
    "Musara",
    "Nakai",
    "Neder",
    "Nine_Valleys",
    "Rahien_Sorei",
    "Reyn",
    "Serai",
    "Shaarad",
    "Shaido",
    "Shelan",
    "Shiande",
    "Shorara",
    "Taardad",
    # Seanchan groups
    "Deathwatch_Guards",
    "Ever_Victorious_Army",
    "The_Blood",
    # Atha'an Miere groups
    "Sea_Folk",
    "Windfinders",
    "Wavemistresses",
    "Sailmistresses",
    "Mistresses_of_the_Ships",
    "Deckmistresses",
    "First_Twelve_of_the_Atha'an_Miere",
    "Roofmistresses",
    # Other groups
    "Tuatha'an",
    "Tinkers",
    "Kinswomen",
    "Cha_Faile",
    "Younglings",
    "Dorlan_Group",
    "Farm_Group",
    "Ebou_Dari_Stash",
    "Winged_Guard",
    "Tower_Guards",
    "Queen's_Guards",
    "Illuminators",
    "White_Tower",
    "Hunters_of_the_Horn",
    "Logain's_followers",
    # Meta group categories
    "Groups",
    "Organizations",
    "Military_units",
}

# PROFESSIONS
PROFESSIONS = {
    "Blacksmiths",
    "Healers",
    "Innkeepers",
    "Merchants",
    "Advocates",
    "Hunters_of_the_Horn",
    "Wisdoms",
    "Bards",
    "Gleemen",
    "Scholars",
    "Historians",
    "Philosophers",
    "Poets",
    "Writers",
    "Artists",
    "Mapmakers",
    "Inventors",
    "Librarians",
    "Thief-catchers",
    "Farmers",
    "Fishers",
    "Sailors",
    "Soldiers",
    "Mercenaries",
    "Guardsmans",
    "Servants",
    "Cooks",
    "Stablemen",
    "Clerks",
    "Secretaries",
    "Bankers",
    "Tavernkeepers",
    "Barbers",
    "Craftsmans",
    "Carpenters",
    "Builders",
    "Masons",
    "Smiths",
    "Goldsmiths",
    "Silversmiths",
    "Weavers",
    "Seamstresses",
    "Midwives",
    "Entertainers",
    "Gamblers",
}

# SOCIAL ROLES & STATUS
SOCIAL_ROLES = {
    "Queens",
    "Kings",
    "Lords",
    "Ladies",
    "Nobility",
    "Rulers",
    "Royalty",
    "The_Blood",
    "Emperors",
    "Empresses",
    "Prince",
    "Panarchs",
    "High_Seats",
    "Nobles",
    "Clan_chiefs",
}

# SPECIAL ABILITIES
SPECIAL_ABILITIES = {
    "Ta'veren",
    "Wolfbrothers",
    "Dreamers",
    "Dreamwalkers",
    "Sniffers",
    "Viewers",
    "Blademasters",
    "Heroes_of_the_Horn",
    "Treesingers",
}

# NATIONALITIES (people categories)
NATIONALITY_CATEGORIES = {
    "Aiel_(people)",
    "Andor_(people)",
    "Arafel_(people)",
    "Arad_Doman_(people)",
    "Atha'an_Miere_(people)",
    "Cairhien_(people)",
    "Ghealdan_(people)",
    "Illian_(people)",
    "Kandor_(people)",
    "Malkier_(people)",
    "Mayene_(people)",
    "Murandy_(people)",
    "Saldaea_(people)",
    "Seanchan_(people)",
    "Shara_(people)",
    "Shienar_(people)",
    "Tarabon_(people)",
    "Tar_Valon_(people)",
    "Tear_(people)",
    "Two_Rivers_(people)",
    "Almoth_Plain_(people)",
    "Amadicia_(people)",
    "Borderlands_(people)",
    "Far_Madding_(people)",
    "Toman_Head",
    "Midlander_(people)",
    # Historical nations
    "Age_of_Legends_(people)",
    "Manetheren_(people)",
    "Aridhol_(people)",
    "Almoren_(people)",
    "Aramaelle_(people)",
    "Caembarin_(people)",
    "Coremanda_(people)",
    "Eharon_(people)",
    "Essenia_(people)",
    "Farashelle_(people)",
    "Jaramide_(people)",
    "Safer_(people)",
}

# =============================================================================
# ALL CHARACTER CATEGORIES
# =============================================================================
# fmt: off
ALL_CHARACTER_CATEGORIES = AJAHS | ALIGNMENT_DARK | CHANNELING_AFFILIATIONS | CULTURAL_GROUPS | GENDERS | MILITARY_GROUPS | MILITARY_ROLES | ORGANIZATIONS | PROFESSIONS | SOCIAL_ROLES | SPECIAL_ABILITIES | NATIONALITY_CATEGORIES
# fmt: on

# MAGIC ITEMS - POWER OBJECTS
POWER_OBJECTS = {
    "Angreal",
    "Sa'angreal",
    "Ter'angreal",
    "Items_of_Power",
}

# MAGIC CONCEPTS - ONE POWER
ONE_POWER_CONCEPTS = {
    "One_Power",
    "Saidin",
    "Channelers",
    "Channeling",
    "Weaves",
    "Talents",
    "Special_abilities",
    "Strength_in_power",
    "Taint",
}

# MAGIC PLACES & REALMS
MAGIC_PLACES = {
    "Tel'aran'rhiod",
    "The_Pattern",
    "Shadar_Logoth",
}

# MAGIC ENTITIES
MAGIC_ENTITIES = {
    "Shadowspawn",
    "Constructs",
    "Aelfinn_and_Eelfinn",
    "Extradimensional_entities",
}

# MAGIC WEAPONS & SPECIAL ITEMS
MAGIC_WEAPONS = {
    "Weapons",
    "Crowns_and_Regalia",
    "Special_objects",
}

# =============================================================================
# ALL MAGIC CATEGORIES (for easy checking)
# =============================================================================
ALL_MAGIC_CATEGORIES = POWER_OBJECTS | ONE_POWER_CONCEPTS | MAGIC_PLACES | MAGIC_ENTITIES | MAGIC_WEAPONS

# TIMELINE: (Historical) Time periods, events, wars
TIMELINE_CATEGORIES = {
    "Ages",
    "First_Age",
    "Second_Age",
    "Third_Age",
    "Fourth_Age",
    "Age_of_Legends",
    "After_the_Breaking",
    "New_Era",
    "New_Era_chronology",
    "The_Free_Years",
    "People_of_the_Free_Years",
    "Battles",
    "Wars",
    "Timeline",
    "Time",
    "Dates",
    "History",
    "Historical",
    "Historical_people",
    "Dreadlords",
    "Jenn_Aiel",
    "Languages",
    "Old_Tongue",
    "Phrases",
    "Slang",
    "Legends",
}

ALL_TIMELINE_CATEGORIES = TIMELINE_CATEGORIES

# =============================================================================
# ALL PROPHECIES CATEGORIES (for easy checking)
# =============================================================================
ALL_PROPHECIES_CATEGORIES = {"Prophecies", "Foretellings", "Foreseen events", "Foreseen people"}

# LOCATIONS: Countries, cities, regions, buildings, geographic features. CONCEPTS
LOCATION_CATEGORIES = {
    "Aiel_Waste",
    "Almoren",
    "Almoth_Plain",
    "Altara",
    "Amadicia",
    "Andor",
    "Arad_Doman",
    "Arafel",
    "Aramaelle",
    "Aridhol",
    "Borderlands",
    "Cairhien",
    "Coremanda",
    "Eharon",
    "Essenia",
    "Far_Madding",
    "Farashelle",
    "Ghealdan",
    "Illian",
    "Kandor",
    "Manetheren",
    "Murandy",
    "Safer",
    "Saldaea",
    "Shienar",
    "Tar_Valon",
    "Tear",
    "Westlands",
    "Former_Nations_of_the_New_Era",
    "Ten_Nations",
    "Malkier",
    "Mayene",
    "Tarabon",
    "Jaramide",
    "Maredo_(people)",
    "Masenashar_(people)",
    "Seanchan_continent",
    "Shara",
    "Toman_Head",
    "Tomanelle",
    "Two_Rivers",
    "Shadar_Logoth",
    "Caemlyn",
    "Cairhien_Academy",
    "Cairhien_expedition",
    "Caemlyn_Embassy",
    # Geographic features
    "Cities",
    "Cities_(Age_of_Legends)",
    "Great_Cities",
    "Capitals",
    "Villages",
    "Towns",
    "Historical_settlements",
    "Ruins",
    "Rivers",
    "Stones_River",
    "Oceans",
    "Gulfs_and_bays",
    "Islands",
    "Islands_of_the_Atha'an_Miere",
    "Mountains",
    "Hills",
    "Spine_Ridge",
    "Plains",
    "Marshes",
    "Forests",
    "Peninsulas",
    "Continents",
    "Geographical_features",
    "Geographical_regions",
    "Other_features",
    "Bridges",
    "Roads",
    "Gates",
    # Buildings
    "Buildings",
    "Other_notable_buildings",
    "Inns",
    "Taverns",
    "Palaces",
    "White_Tower",
    "Holds",
    # Clans/Locations
    "Bent_Peak",
    "Black_Cliffs",
    "Black_Hills",
    "Black_Rock",
    "Black_Water",
    "Broken_Cliff",
    "Chane_Rocks",
    "Cold_Peak",
    "Iron_Mountain",
    "White_Cliff",
    "White_Mountain",
    "Red_Salt",
    "Red_Water",
    "Green_Salts",
    "Salt_Flat",
    "Smoke_Water",
    "Two_Spires",
    "Jaern_Rift",
    # Nationality/people markers
    "Altara_(people)",
    "Amadicia_(people)",
    "Andor_(people)",
    "Arad_Doman_(people)",
    "Arafel_(people)",
    "Aiel_(people)",
    "Almoren_(people)",
    "Aramaelle_(people)",
    "Aridhol_(people)",
    "Age_of_Legends_(people)",
    "Borderlands_(people)",
    "Cairhien_(people)",
    "Aelgar_(people)",
    "Aldeshar_(people)",
    "Amayar_(people)",
    "Eharon_(people)",
    "Esandara_(people)",
    "Essenia_(people)",
    "Farashelle_(people)",
    "Black_Hills_(people)",
    "Dal_Calain_(people)",
    "Darmovan_(people)",
    "Dhowlan_(people)",
    "Far_Madding_(people)",
    "Ghealdan_(people)",
    "Hol_Cuchone_(people)",
    "Illian_(people)",
    "Jaramide_(people)",
    "Kandor_(people)",
    "Khodomar_(people)",
    "Malkier_(people)",
    "Manetheren_(people)",
    "Mayene_(people)",
    "Murandy_(people)",
    "Safer_(people)",
    "Saldaea_(people)",
    "Seanchan_(people)",
    "Shandalle_(people)",
    "Shara_(people)",
    "Sharan_(people)",
    "Shienar_(people)",
    "Shiota_(people)",
    "Talmour_(people)",
    "Tar_Valon_(people)",
    "Tarabon_(people)",
    "Tear_(people)",
    "Tova_(people)",
    "Two_Rivers_(people)",
    "Caembarin_(people)",
    "Coremanda_(people)",
    "Unclaimed_territories_(people)",
    "Atha'an_Miere_(people)",
    "Tuatha'an_(people)",
    # Locations/Places
    "Locations",
    "Places",
    "Nations",
    "Historical_nations",
    "Nations_of_the_Free_Years",
    "Unclaimed_territories",
}

# CREATURES: Animals, Shadowspawn, special beings
CREATURE_CATEGORIES = {
    "Animals",
    "Horses",
    "Wolves",
    "Ferrets",
    "Cats",
    "Other_animals",
    "Seanchan_animals",
    "Shadowspawn",
    "Constructs",
    "Aelfinn_and_Eelfinn",
    "Extradimensional_entities",
    "Other_non-humans",
    "Ogier",
}

# ITEMS: Non-magical objects, weapons, clothing, food, tools
ITEM_CATEGORIES = {
    "Weapons",
    "Sword_forms",
    "Battle_Cries",
    "Clothing",
    "Fashion",
    "Thrones",
    "Crowns_and_Regalia",
    "Symbols",
    "Flags",
    "Foods",
    "Wine",
    "Herbs_and_Medicines",
    "Poisons",
    "Games",
    "Dice",
    "Books",
    "All_books",
    "Series_books",
    "Main_Series",
    "Maps",
    "Maps_of_Nations_and_Kingdoms",
    "Goods",
    "Items",
    "Misc._items",
    "Special_objects",
    "Ships",
    "Instruments",
    "Tools",
    "Technology",
    "Calendars",
    "Measurements",
}

# CULTURAL: Customs, traditions, songs, holidays
CULTURAL_CATEGORIES = {
    "Culture",
    "Aiel_culture",
    "Atha'an_Miere_culture",
    "Ogier_culture",
    "Seanchan_culture",
    "Customs",
    "Laws_and_customs",
    "Tradition",
    "Holidays",
    "Marriage",
    "Songs",
    "Instruments",
    "Conventions",
    "Philosophy",
    "Theories",
    "Parallels",
}

# CONCEPTS: Metaphysical, abstract WoT concepts
CONCEPT_CATEGORIES = {
    "The_Pattern",
    "The_Wheel_of_Time",
    "Ta'veren",
    "Heroes_of_the_Horn",
    "Tel'aran'rhiod",
    "The_Shadow",
    "Shadow",
    "Bound_to_the_Wheel",
    "Reincarnated",
    "Titles",
    "Metaphysics",
    "Concepts",
    "In-universe_content",
    "Deceased",
    "Balefired",
    "Living",
    "The_Turned",
    "Prophecies",
    "Comparison",
    "Constellation",
    "Constellations",
    "Trees",
    "Plants",
}

ORGANIZATION_CATEGORIES = {
    "Aes_Sedai",
    "Black_Ajah",
    "Entertainers",
    "Illuminators",
    "Red_Ajah",
    "Aiel_septs",
    "Warriors",
    "Accepted",
    "Brown_Ajah",
    "Atha'an_Miere",
    "Military",
    "Military_units",
    "Kinswomen",
    "Ajah_Heads",
    "Seanchan",
    "Blacksmiths",
    "Ever_Victorious_Army",
    "Dragonsworn",
    "Mistresses_of_Novices",
    "Darkfriends",
    "Novices",
    "Mercenaries",
    "Aiel_clans",
    "Peddlers",
    "Noble_houses",
    "Children_of_the_Light",
    "Wise_Ones",
    "Soldiers",
    "Groups",
    "Aiel_warrior_societies",
    "Organizations",
    "Healers",
}

# =============================================================================
# ALL CONCEPT CATEGORIES (for easy checking)
# =============================================================================
ALL_CONCEPT_CATEGORIES = LOCATION_CATEGORIES | CREATURE_CATEGORIES | ITEM_CATEGORIES | CULTURAL_CATEGORIES | CONCEPT_CATEGORIES | ORGANIZATION_CATEGORIES

# =============================================================================
# CATEGORIES TO SKIP (for easy checking)
# =============================================================================
CATEGORIES_TO_SKIP = {
    "Inclusion_redirects",
    "Timeline_redirects",
    "Authors",
    "Chapter_redirects",
    "Date_redirects",
    "Book_redirects",
    "Publishers",
    "Administrative_redirects",
    "Non-canon",
    "Statistical_analysis",
    "Book_glossaries",
    "Online_Forums",
    "Candidates_for_deletion",
    "Character_not_mentioned_in_books",
    "Characters_only_mentioned_in_the_Companion",
    "Characters_only_mentioned_in_the_RPG",
    "Characters_only_mentioned_in_the_RPG",
    "Characters_original_to_the_video_game",
    "Characters_original_to_the_video_game",
    "Creators",
    "Disambiguation",
    "Images_by_Ellisa_Mitchell",
    "Items_original_to_the_video_game",
    "List_pages",
    "Official",
    "Other_Media",
    "Real-world_content",
    "Real-world_redirects",
    "Real_people",
    "Reference",
    "Role_Playing",
    "Spoilers",
    "Stubs",
    "Category_redirects",
    "TV_Series",
    "The_World_of_Robert_Jordan's_The_Wheel_of_Time",
    "Wheel_of_Time_translations",
    "Series_books",
    "All_books",
}

# =============================================================================
# REDIRECT CATEGORIES (for easy checking)
# =============================================================================
REDIRECT_CATEGORIES = {
    "Naming_redirects",
    "Naming_redirect",
    "Alias_redirects",
    "Grammar_redirects",
    "Old_Tongue_redirects",
    "Geo-political_redirects",
    "Sword_form_redirects",
    "Chapter_redirects",
    "Date_redirects",
    "Timeline_redirects",
    "Book_redirects",
    "Category_redirects",
    "Inclusion_redirects",
    "Administrative_redirects",
    "Real-world_redirects",
    "Redirects",
}

CATEGORY_OVERRIDES = {
    "Elayne_Trakand_Chronology.txt": ["Character_Chronologies"],
    "Egwene_al'Vere_Chronology.txt": ["Character_Chronologies"],
    # Add any future overrides here
}

# =============================================================================
# STATUS (for temporal filtering later if needed)
# =============================================================================
STATUS_CATEGORIES = {
    "Living_as_of_AMOL",
    "Living_as_of_TOM",
    "Living_as_of_TGS",
    "Living_as_of_KOD",
    "Living_as_of_COT",
    "Living_as_of_WH",
    "Living_as_of_TPOD",
    "Living_as_of_ACOS",
    "Living_as_of_LOC",
    "Living_as_of_TFOH",
    "Living_as_of_TSR",
    "Living_as_of_TDR",
    "Living_as_of_TGH",
    "Living_as_of_TEOTW",
    "Living_as_of_NS",
    "Deceased",
}


def check_fist_level_key_in_json(filepath: str, key_to_check: str) -> bool:
    """
    Check if a first-level key exists in a JSON file.

    Args:
        filename: Path to JSON file
        key_to_check: Key to check for
    """
    data = load_json_from_file(filepath, log=False)

    # Ensure it's a dictionary
    if isinstance(data, dict):
        return key_to_check in data
    else:
        raise ValueError("JSON is not a dictionary.")


def extract_page_name(file_path: Path) -> Optional[str]:
    """Extract page name from wiki file H1 header."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# ") and not line.startswith("##"):
                    page_name = line[2:].strip()
                    return page_name
        logger.warning(f"No H1 header found in {file_path.name}")
        return None
    except Exception as e:
        logger.warning(f"Error extracting page name from {file_path.name}: {e}")
        return None


def extract_id(content: str):
    """
    Extract page ID from wiki page content.

    Args:
        content: Full text content of a wiki page
    """
    # Extract page ID
    page_id_match = re.search(r"<!--\s*Page ID:\s*(\d+)\s*-->", content)
    if page_id_match:
        page_id = int(page_id_match.group(1))
    else:
        page_id = None

    return page_id


def extract_categories(filepath, content: str) -> list:
    """
    Extract categories from wiki page content.

    Categories are in format:
    <!-- Categories: Cat1, Cat2, Cat3 -->

    Args:
        content: Full text content of a wiki page
    """

    if not content:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath.name}: {e}")
            return []

    pattern = r"<!--\s*Categories:\s*(.*?)\s*-->"
    match = re.search(pattern, content, re.IGNORECASE)

    all_categories = []

    if match:
        categories_str = match.group(1)
        # Split by comma and strip whitespace
        categories = [cat.strip() for cat in categories_str.split(",")]
        # Filter out empty strings
        categories = [cat for cat in categories if cat]

        # Apply overrides if they exist for this file
        if filepath.name in CATEGORY_OVERRIDES:
            categories.extend(CATEGORY_OVERRIDES[filepath.name])

        all_categories = list(set(categories))  # Deduplicate

    return all_categories
