
from pathlib import Path
import re
from typing import Optional
from src.utils.util_files_functions import load_json_from_file
from src.utils.logger import get_logger
 
logger = get_logger(__name__)

def define_taxonomy():
    """Define concept taxonomy - which categories belong to which groups"""
    
# LOCATIONS: Countries, cities, regions, buildings, geographic features
LOCATION_CATEGORIES = [
    "Aiel_Waste", "Almoren", "Almoth_Plain", "Altara", "Amadicia", "Andor", 
    "Arad_Doman", "Arafel", "Aramaelle", "Aridhol", "Borderlands", "Cairhien",
    "Coremanda", "Eharon", "Essenia", "Far_Madding", "Farashelle", "Ghealdan",
    "Illian", "Kandor", "Manetheren", "Murandy", "Safer", "Saldaea", "Shienar",
    "Tar_Valon", "Tear", "Westlands", "Former_Nations_of_the_New_Era", "Ten_Nations",
    "Malkier", "Mayene", "Tarabon", "Jaramide", "Maredo_(people)", "Masenashar_(people)",
    "Seanchan_continent", "Shara", "Toman_Head", "Tomanelle", "Two_Rivers",
    "Shadar_Logoth", "Caemlyn", "Cairhien_Academy", "Cairhien_expedition",
    "Caemlyn_Embassy",
    # Geographic features
    "Cities", "Cities_(Age_of_Legends)", "Great_Cities", "Capitals", "Villages", "Towns",
    "Historical_settlements", "Ruins",
    "Rivers", "Stones_River", "Oceans", "Gulfs_and_bays", "Islands", 
    "Islands_of_the_Atha'an_Miere",
    "Mountains", "Hills", "Spine_Ridge", "Plains", "Marshes", "Forests", "Peninsulas",
    "Continents", "Geographical_features", "Geographical_regions",
    "Other_features", "Bridges", "Roads", "Gates",
    # Buildings
    "Buildings", "Other_notable_buildings", "Inns", "Taverns", "Palaces", 
    "White_Tower", "Holds",
    # Clans/Locations
    "Bent_Peak", "Black_Cliffs", "Black_Hills", "Black_Rock", "Black_Water",
    "Broken_Cliff", "Chane_Rocks", "Cold_Peak", "Iron_Mountain", "White_Cliff",
    "White_Mountain", "Red_Salt", "Red_Water", "Green_Salts", "Salt_Flat",
    "Smoke_Water", "Two_Spires", "Jaern_Rift",
    # Nationality/people markers
    "Altara_(people)", "Amadicia_(people)", "Andor_(people)", "Arad_Doman_(people)",
    "Arafel_(people)", "Aiel_(people)", "Almoren_(people)", "Aramaelle_(people)", 
    "Aridhol_(people)", "Age_of_Legends_(people)", "Borderlands_(people)", 
    "Cairhien_(people)", "Aelgar_(people)", "Aldeshar_(people)", "Amayar_(people)", 
    "Eharon_(people)", "Esandara_(people)", "Essenia_(people)", "Farashelle_(people)", 
    "Black_Hills_(people)", "Dal_Calain_(people)", "Darmovan_(people)", 
    "Dhowlan_(people)", "Far_Madding_(people)", "Ghealdan_(people)", 
    "Hol_Cuchone_(people)", "Illian_(people)", "Jaramide_(people)", "Kandor_(people)",
    "Khodomar_(people)", "Malkier_(people)", "Manetheren_(people)", "Mayene_(people)",
    "Murandy_(people)", "Safer_(people)", "Saldaea_(people)", "Seanchan_(people)",
    "Shandalle_(people)", "Shara_(people)", "Sharan_(people)", "Shienar_(people)",
    "Shiota_(people)", "Talmour_(people)", "Tar_Valon_(people)", "Tarabon_(people)",
    "Tear_(people)", "Tova_(people)", "Two_Rivers_(people)", "Caembarin_(people)",
    "Coremanda_(people)", "Unclaimed_territories_(people)", "Atha'an_Miere_(people)",
    "Tuatha'an_(people)",
    # Locations/Places
    "Locations", "Places", "Nations", "Historical_nations", "Nations_of_the_Free_Years",
    "Unclaimed_territories",
]

# CREATURES: Animals, Shadowspawn, special beings
CREATURE_CATEGORIES = [
    "Animals", "Horses", "Wolves", "Ferrets", "Cats", "Other_animals",
    "Seanchan_animals",
    "Shadowspawn", "Constructs",
    "Aelfinn_and_Eelfinn", "Extradimensional_entities",
    "Other_non-humans", "Ogier",
]

# ITEMS: Non-magical objects, weapons, clothing, food, tools
ITEM_CATEGORIES = [
    "Weapons", "Sword_forms", "Battle_Cries",
    "Clothing", "Fashion", "Thrones",
    "Crowns_and_Regalia", "Symbols", "Flags",
    "Foods", "Wine", "Herbs_and_Medicines", "Poisons",
    "Games", "Dice",
    "Books", "All_books", "Series_books", "Main_Series",
    "Maps", "Maps_of_Nations_and_Kingdoms",
    "Goods", "Items", "Misc._items", "Special_objects",
    "Ships", "Instruments", "Tools", "Technology",
    "Calendars", "Measurements",
]

# HISTORICAL: Time periods, events, wars
HISTORICAL_CATEGORIES = [
    "Ages", "First_Age", "Second_Age", "Third_Age", "Fourth_Age",
    "Age_of_Legends", "After_the_Breaking", "New_Era", "New_Era_chronology",
    "The_Free_Years", "People_of_the_Free_Years",
    "Battles", "Wars",
    "Timeline", "Time", "Dates", "History", "Historical", "Historical_people",
    "Dreadlords", "Jenn_Aiel",
    "Languages", "Old_Tongue", "Phrases", "Slang",
    "Legends",
]

# CULTURAL: Customs, traditions, songs, holidays
CULTURAL_CATEGORIES = [
    "Culture", "Aiel_culture", "Atha'an_Miere_culture", "Ogier_culture", 
    "Seanchan_culture",
    "Customs", "Laws_and_customs", "Tradition", "Holidays", "Marriage",
    "Songs", "Instruments",
    "Conventions", "Philosophy", "Theories", "Parallels",
]

# CONCEPTS: Metaphysical, abstract WoT concepts
CONCEPT_CATEGORIES = [
    "The_Pattern", "The_Wheel_of_Time", "Ta'veren", "Heroes_of_the_Horn",
    "Tel'aran'rhiod", "The_Shadow", "Shadow",
    "Bound_to_the_Wheel", "Reincarnated",
    "Titles", "Metaphysics", "Concepts", "In-universe_content",
    "Deceased", "Balefired", "Living", "The_Turned",
    "Prophecies", "Comparison",
    "Constellation", "Constellations",
    "Trees", "Plants",
]

# ORGANIZATIONS: Important WoT groups and factions
ORGANIZATION_CATEGORIES = [
    # Aes Sedai
    "Ajahs", "Blue_Ajah", "Brown_Ajah", "Gray_Ajah", "Green_Ajah", 
    "Red_Ajah", "White_Ajah", "Yellow_Ajah", "Black_Ajah",
    # Aes Sedai factions
    "Aes_Sedai_factions", "Rand's_Aes_Sedai", "Rebel_Aes_Sedai", 
    "Unaligned_sisters", "Elaida_a'Roihan's_White_Tower",
    # Military/Combat groups
    "Band_of_the_Red_Hand", "Redarms",
    "Children_of_the_Light", "Whitecloaks",
    "Dragonsworn",
    # Aiel societies and clans
    "Aiel_warrior_societies", "Aiel_clans", "Aiel_septs",
    "Far_Dareis_Mai", "Far_Aldazar_Din", "Aethan_Dor", "Duadhe_Mahdi'in",
    "Cor_Darei", "Hama_N'dore", "Seia_Doon", "Sha'mad_Conde", "Shae'en_M'taal",
    "Sovin_Nai", "Tain_Shari", "Mera'din",
    "Chareen", "Chumai", "Codarra", "Cosaida", "Daryne", "Degalle", "Domai",
    "Goshien", "Haido", "Imran", "Jarra", "Jenda", "Jhirad", "Jindo", "Jumai",
    "Miagoma", "Moshaine", "Musara", "Nakai", "Neder", "Nine_Valleys", "Rahien_Sorei",
    "Reyn", "Serai", "Shaarad", "Shaido", "Shelan", "Shiande", "Shorara", "Taardad",
    # Seanchan groups
    "Deathwatch_Guards", "Ever_Victorious_Army", "The_Blood",
    # Atha'an Miere groups
    "Sea_Folk", "Windfinders", "Wavemistresses", "Sailmistresses", 
    "Mistresses_of_the_Ships", "Deckmistresses", "First_Twelve_of_the_Atha'an_Miere",
    "Roofmistresses",
    # Other groups
    "Tuatha'an", "Tinkers",
    "Kinswomen", "Cha_Faile", "Younglings",
    "Dorlan_Group", "Farm_Group", "Ebou_Dari_Stash", "Winged_Guard",
    "Tower_Guards", "Queen's_Guards",
    # Meta group categories
    "Groups", "Organizations", "Military_units",
]

# EXCLUDE: Character attributes, magic, prophecies, and meta wiki categories
EXCLUDE_CATEGORIES = [
    # Character organizational affiliations (status, not the org itself)
    "Aes_Sedai", "Aes_Sedai_(Age_of_Legends)", "Aes_Sedai_(Free_Years)", 
    "Aes_Sedai_after_the_Breaking", "Aes_Sedai_positions",
    "High_Ranking_Aes_Sedai", "Middle_Ranking_Aes_Sedai", "Low_Ranking_Aes_Sedai",
    "Accepted", "Novices", "Mistresses_of_Novices", "Learners", "Wilders", "Sparkers",
    "No_Ajah", "Unknown_Ajah", "Ajah_Heads",
    "Amyrlin_Seats", "Keepers_of_the_Chronicles", "Sitters",
    "Asha'man", "Asha'man_(rank)", "Dedicated", "Soldier_(Asha'man)", "Soldiers",
    "Taim's_cronies", "Logain's_followers", "Stewards_of_the_Dragon",
    "Lord_Captain", "Lord_Captain_Commanders", "Questioners", "Inquisitors",
    "False_Dragons",
    "Aiel",
    "Da'shain_Aiel", "Gai'shain", "Jenn_Aiel",
    "Clan_chiefs", "Wise_Ones",
    # Seanchan affiliations
    "Seanchan", "Damane", "Sul'dam", "Da'covale", "Seekers", "Seekers_for_Truth",
    "Morat'rakens", "Seanchan_animal_handlers", "S'redit_handler",
    "So'jhin", "Truthspeakers",
    # Atha'an Miere affiliations
    "Atha'an_Miere",
    # Other affiliations
    "Darkfriends", "Forsaken", "The_Turned",
    "Ayyad", "Shara", "Amayar",
    "Hunters_of_the_Horn",
    # Character professions
    "Merchants", "Council_of_Merchants", "Peddlers", "Traders",
    "Guards", "Guardsmans", "Warriors", "Mercenaries",
    "Servants", "Serving_girls", "Maids", "Head_servants", "Stablemen",
    "Farmers", "Millers", "Fishers",
    "Blacksmiths", "Blademasters", "Swordmasters", "Sword_instructors",
    "Masters_of_the_Blades",
    "Gleemen", "Bards", "Entertainers", "Gamblers",
    "Healers", "Best_healers", "Midwives", "Wisdoms", "Women's_Circle",
    "Apprentices", "Bootmakers", "Bellfounders", "Lensmakers", "Goldsmiths",
    "Mapmakers", "Bankers", "Barbers", "Bouncers", "Brickmasons", "Builders",
    "Carpenters", "Cargomasters", "Dockmasters", "Ferrymasters", "Footmen",
    "Boatmens", "Fletchers", "Farriers", "Gatekeepers", "Gardeners",
    "Quartermasters", "Cobblers", "Coopers", "Cooks", "Craftsmans", "Cutpurses",
    "Innkeepers", "Tavernkeepers", "Thief-catchers", "Thugs", "Wagon_Drivers",
    "Watchmen", "Weavers", "Seamstresses", "Thatchers", "Treesingers",
    "Masons", "Silversmiths", "Saddlemakers", "Clerks", "Secretaries",
    "Housewifes", "Librarians", "Chief_Librarians", "Illuminators", "Inventors",
    "Historians", "Philosophers", "Poets", "Scholars", "Artists", "Authors",
    "Sailors", "Ship_captains", "Sedan_Chair_bearers",
    "Orphan_keepers", "Baker_(possibly)s",
    # Character roles/positions
    "Kings", "Queens", "Lords", "Ladies", "Prince", "Rulers", "Royalty",
    "Emperors", "Empresses", "Panarchs", "Firsts_of_Mayene",
    "Captains", "Generals", "Five_Great_Captains",
    "Advocates", "Assistants", "Attendants", "Council_of_Nine",
    "Counsels_of_Far_Madding", "Mayors_and_governors", "Village_Councilors",
    "Nobility", "High_Nobility_of_Tear", "Noble_houses", "Nobles",
    "High_Seats", "Major_Houses_of_Andor",
    "Government", "Ruling_bodies", "Politics",
    "Headmistresses",
    # Character abilities
    "Dreamers", "Dreamwalkers", "Sniffers", "Wolfbrothers", "Channelers",
    "Viewers", "Doomseers",
    "Special_abilities", "Strength_in_power", "Talents",
    # Magic (already in magic_index)
    "Angreal", "Sa'angreal", "Ter'angreal", "One_Power",
    "Channeling", "Saidin", "Weaves", "Taint",
    "Items_of_Power",
    # Prophecies (already in prophecy_index)
    "Foretellings", "Prophecies", "Foreseen_events", "Foreseen_people",
    # Character attributes
    "Male", "Female", "Men", "Women",
    "Unknown_gender", "Unknown_nationality", "Unknown_occupation",
    "Unknown_clan", "Unknown_sept", "Unknown_society", "Unknown_status",
    "Characters", "People", "Unnamed_characters", "Fictitious_Characters",
    "Characters_named_after_fans", "Antagonists", "POV_character",
    "Historical_people",
    # Living/Deceased markers
    "Living", "Living_as_of_ACOS", "Living_as_of_AMOL", "Living_as_of_CCG",
    "Living_as_of_COT", "Living_as_of_GUIDE", "Living_as_of_KOD",
    "Living_as_of_LOC", "Living_as_of_NS", "Living_as_of_TDR",
    "Living_as_of_TEOTW", "Living_as_of_TFOH", "Living_as_of_TGH",
    "Living_as_of_TGS", "Living_as_of_TOM", "Living_as_of_TPOD",
    "Living_as_of_TSASG", "Living_as_of_TSR", "Living_as_of_TWOTC",
    "Living_as_of_WH",
    "Deceased", "Balefired", "Reincarnated",
    # Meta/admin categories
    "Administrative_redirects", "Alias_redirects", "Aliases", "Book_redirects",
    "Category_redirects", "Chapter_redirects", "Date_redirects",
    "Geo-political_redirects", "Grammar_redirects", "Inclusion_redirects",
    "Naming_redirect", "Naming_redirects", "Old_Tongue_redirects",
    "Redirects", "Sword_form_redirects", "Timeline_redirects",
    "Disambiguation", "Chapter_disambiguations",
    "Articles_that_need_to_be_wikified", "Articles_to_be_expanded",
    "Citation_needed", "Cleanup", "Contradictions", "Dubious",
    "Exegetic", "Notes_needed", "Todo", "Updates_needed",
    "Trivia", "Statistical_analysis",
    "A_Crown_of_Swords_chapter_summaries", "A_Memory_of_Light_chapter_summaries",
    "Crossroads_of_Twilight_chapter_summaries", "Knife_of_Dreams_chapter_summaries",
    "Lord_of_Chaos_chapter_summaries", "New_Spring_chapter_summaries",
    "The_Dragon_Reborn_chapter_summaries", "The_Eye_of_the_World_chapter_summaries",
    "The_Fires_of_Heaven_chapter_summaries", "The_Gathering_Storm_chapter_summaries",
    "The_Great_Hunt_chapter_summaries", "The_Path_of_Daggers_chapter_summaries",
    "The_Shadow_Rising_chapter_summaries", "Towers_of_Midnight_chapter_summaries",
    "Winter's_Heart_chapter_summaries",
    "Chapter_summaries", "Chapter_summaries_crown_of_swords",
    "Book_glossaries", "Glossary", "Glossary_Only",
    "Character_Chronologies",
    "Pages_using_ISBN_magic_links", "Pages_using_duplicate_arguments_in_template_calls",
    "Pages_with_broken_file_links", "Pages_with_reference_errors",
    "List_pages", "Short_pages",
    "Wotwiki_featured_articles",
    "Non-canon", "Online_Forums", "Publishers",
    "Military", "Military_Ranks",
    "Occupations", "Races", "Slaves",
    "Eyes-and-ears",
]

REDIRECT_CATEGORIES = [
                "Naming_redirects",
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
            ]

CATEGORY_OVERRIDES = {
    'Elayne_Trakand_Chronology.txt': ['Character_Chronologies'],
    'Egwene_al\'Vere_Chronology.txt': ['Character_Chronologies'],
    # Add any future overrides here
}

CATEGORIES_TO_SKIP = {
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
    "Official",
    "Other_Media",
    "Real-world_content",
    "Real-world_redirects",
    "Real_people",
    "Reference",
    "Role_Playing",
    "Spoilers",
    "Stubs",
    "TV_Series",
    "The_World_of_Robert_Jordan's_The_Wheel_of_Time",
    "Wheel_of_Time_translations",
}

PROPHECIES_CATEGORIES = {
    "Prophecies",
    "Foretellings",
    "Foreseen events",
    "Foreseen people"
}

MAGIC_CATEGORIES = {
    "One Power", 
    "Weaves",
    "Ter'angreal",
    "Angreal",
    "Sa'angreal",
    "Items of Power",
    "Strength in power",
    "Taint",
    "Saidin",
    "Tel'aran'rhiod",
    "The Pattern",
    "Metaphysics",
    "Aelfinn and Eelfinn",
    "Constructs",
}

"""
Dragon's Codex - WoT Wiki Category Mappings
All real categories from the wiki organized by type for character index extraction.
"""

# =============================================================================
# GENDER
# =============================================================================
GENDER_CATEGORIES = {
    'Men': 'male',
    'Women': 'female'
}

# =============================================================================
# CHANNELING AFFILIATIONS
# =============================================================================
CHANNELING_AFFILIATIONS = {
    'Aes_Sedai',
    'Asha\'man',
    'Wilders',
    'Kinswomen',
    'Windfinders',
    'Wise_Ones',
    'Damane',
    'Sul\'dam',
    'Dreadlords',
    'Forsaken',
    'Ayyad',
    'The_Turned',
    'Channelers',
    'Sparkers',
    'Learners',
    'Accepted',
    'Novices',
    'Tower_initiates',
    'Asha\'man_(rank)',
    'Dedicated',
    'Soldier_(Asha\'man)',
}

# =============================================================================
# AJAH
# =============================================================================
AJAH_CATEGORIES = {
    'Yellow_Ajah': 'Yellow Ajah',
    'Blue_Ajah': 'Blue Ajah',
    'Green_Ajah': 'Green Ajah',
    'Red_Ajah': 'Red Ajah',
    'White_Ajah': 'White Ajah',
    'Brown_Ajah': 'Brown Ajah',
    'Gray_Ajah': 'Gray Ajah',
    'Black_Ajah': 'Black Ajah',
}

# =============================================================================
# SPECIAL ABILITIES
# =============================================================================
SPECIAL_ABILITIES = {
    'Ta\'veren': 'ta_veren',
    'Wolfbrothers': 'wolfbrother',
    'Dreamers': 'dreamer',
    'Dreamwalkers': 'dreamwalker',
    'Sniffers': 'sniffer',
    'Viewers': 'viewer',
    'Blademasters': 'blademaster',
    'Heroes_of_the_Horn': 'hero_of_the_horn',
    'Treesingers': 'treesinger',
}

# =============================================================================
# NATIONALITIES (people categories)
# =============================================================================
NATIONALITY_CATEGORIES = {
    'Aiel_(people)',
    'Andor_(people)',
    'Arafel_(people)',
    'Arad_Doman_(people)',
    'Atha\'an_Miere_(people)',
    'Cairhien_(people)',
    'Ghealdan_(people)',
    'Illian_(people)',
    'Kandor_(people)',
    'Malkier_(people)',
    'Mayene_(people)',
    'Murandy_(people)',
    'Saldaea_(people)',
    'Seanchan_(people)',
    'Shara_(people)',
    'Shienar_(people)',
    'Tarabon_(people)',
    'Tar_Valon_(people)',
    'Tear_(people)',
    'Two_Rivers_(people)',
    'Almoth_Plain_(people)',
    'Amadicia_(people)',
    'Borderlands_(people)',
    'Far_Madding_(people)',
    'Toman_Head',
    'Midlander_(people)',
    # Historical nations
    'Age_of_Legends_(people)',
    'Manetheren_(people)',
    'Aridhol_(people)',
    'Almoren_(people)',
    'Aramaelle_(people)',
    'Caembarin_(people)',
    'Coremanda_(people)',
    'Eharon_(people)',
    'Essenia_(people)',
    'Farashelle_(people)',
    'Jaramide_(people)',
    'Safer_(people)',
}

# =============================================================================
# ORGANIZATIONS (non-channeling)
# =============================================================================
ORGANIZATIONS = {
    'Band_of_the_Red_Hand',
    'Children_of_the_Light',
    'Illuminators',
    'Tuatha\'an',
    'White_Tower',
    'Hunters_of_the_Horn',
    'Logain\'s_followers',
    'Rand\'s_Aes_Sedai',
    'Rebel_Aes_Sedai',
    'Dragonsworn',
    'Cha_Faile',
    'Younglings',
}

# =============================================================================
# MILITARY GROUPS
# =============================================================================
MILITARY_GROUPS = {
    'Warders',
    'Deathwatch_Guards',
    'Ever_Victorious_Army',
    'Five_Great_Captains',
    'Winged_Guard',
    'Band_of_the_Red_Hand',
    'Tower_Guards',
    'Queen\'s_Guards',
    'Redarms',
}

# =============================================================================
# SOCIAL ROLES & STATUS
# =============================================================================
SOCIAL_ROLES = {
    'Queens',
    'Kings',
    'Lords',
    'Ladies',
    'Nobility',
    'Rulers',
    'Royalty',
    'The_Blood',
    'Emperors',
    'Empresses',
    'Prince',
    'Panarchs',
    'High_Seats',
    'Nobles',
    'Clan_chiefs',
}

# =============================================================================
# MILITARY ROLES
# =============================================================================
MILITARY_ROLES = {
    'Generals',
    'Captains',
    'Five_Great_Captains',
    'Lord_Captain',
    'Lord_Captain_Commanders',
    'Warriors',
}

# =============================================================================
# AES SEDAI POSITIONS
# =============================================================================
AES_SEDAI_POSITIONS = {
    'Amyrlin_Seats',
    'Keepers_of_the_Chronicles',
    'Sitters',
    'Ajah_Heads',
    'Mistresses_of_Novices',
}

# =============================================================================
# ASHA'MAN POSITIONS
# =============================================================================
ASHAMAN_POSITIONS = {
    'Asha\'man_(rank)',
    'Dedicated',
    'Soldier_(Asha\'man)',
}

# =============================================================================
# PROFESSIONS
# =============================================================================
PROFESSIONS = {
    'Blacksmiths',
    'Healers',
    'Innkeepers',
    'Merchants',
    'Advocates',
    'Hunters_of_the_Horn',
    'Wisdoms',
    'Bards',
    'Gleemen',
    'Scholars',
    'Historians',
    'Philosophers',
    'Poets',
    'Writers',
    'Artists',
    'Mapmakers',
    'Inventors',
    'Librarians',
    'Thief-catchers',
    'Farmers',
    'Fishers',
    'Sailors',
    'Soldiers',
    'Mercenaries',
    'Guardsmans',
    'Servants',
    'Cooks',
    'Stablemen',
    'Clerks',
    'Secretaries',
    'Bankers',
    'Tavernkeepers',
    'Barbers',
    'Craftsmans',
    'Carpenters',
    'Builders',
    'Masons',
    'Smiths',
    'Goldsmiths',
    'Silversmiths',
    'Weavers',
    'Seamstresses',
    'Midwives',
    'Entertainers',
    'Gamblers',
}

# =============================================================================
# ALIGNMENT (dark-side)
# =============================================================================
ALIGNMENT_DARK = {
    'Darkfriends',
    'The_Shadow',
    'Black_Ajah',
    'Forsaken',
    'Dreadlords',
    'The_Turned',
    'Chosen',
}

# =============================================================================
# CULTURAL GROUPS
# =============================================================================
CULTURAL_GROUPS = {
    'Aiel',
    'Ogier',
    'Tuatha\'an',
    'Seanchan',
    'Atha\'an_Miere',
    'Da\'shain_Aiel',
    'Jenn_Aiel',
    'Tinkers',
}

# =============================================================================
# AIEL CLANS
# =============================================================================
AIEL_CLANS = {
    'Chareen',
    'Codarra',
    'Daryne',
    'Goshien',
    'Jindo',
    'Miagoma',
    'Nakai',
    'Reyn',
    'Shaido',
    'Shaarad',
    'Shiande',
    'Taardad',
}

# =============================================================================
# AIEL WARRIOR SOCIETIES
# =============================================================================
AIEL_SOCIETIES = {
    'Aethan_Dor',
    'Black_Eyes',
    'Brothers_of_the_Eagle',
    'Cor_Darei',
    'Duadhe_Mahdi\'in',
    'Far_Aldazar_Din',
    'Far_Dareis_Mai',
    'Hama_N\'dore',
    'Maidens',
    'Mera\'din',
    'Rahien_Sorei',
    'Red_Shields',
    'Seia_Doon',
    'Sha\'mad_Conde',
    'Shae\'en_M\'taal',
    'Sovin_Nai',
    'Stone_Dogs',
    'Tain_Shari',
    'Thunder_Walkers',
    'True_Bloods',
    'Water_Seekers',
}

# =============================================================================
# SEANCHAN SPECIFIC
# =============================================================================
SEANCHAN_GROUPS = {
    'Da\'covale',
    'So\'jhin',
    'Deathwatch_Guards',
    'Ever_Victorious_Army',
    'Seekers_for_Truth',
    'Truthspeakers',
    'Listeners',
}

# =============================================================================
# ATHA'AN MIERE SPECIFIC
# =============================================================================
ATHAAN_MIERE_GROUPS = {
    'Windfinders',
    'Sailmistresses',
    'Wavemistresses',
    'First_Twelve_of_the_Atha\'an_Miere',
}

# =============================================================================
# STATUS (for temporal filtering later if needed)
# =============================================================================
STATUS_CATEGORIES = {
    'Living_as_of_AMOL',
    'Living_as_of_TOM',
    'Living_as_of_TGS',
    'Living_as_of_KOD',
    'Living_as_of_COT',
    'Living_as_of_WH',
    'Living_as_of_TPOD',
    'Living_as_of_ACOS',
    'Living_as_of_LOC',
    'Living_as_of_TFOH',
    'Living_as_of_TSR',
    'Living_as_of_TDR',
    'Living_as_of_TGH',
    'Living_as_of_TEOTW',
    'Living_as_of_NS',
    'Deceased',
}

# =============================================================================
# PROPHECY CATEGORIES
# =============================================================================
PROPHECY_CATEGORIES = {
    'Prophecies',
    'Foretellings',
    'Foreseen_events',
    'Foreseen_people',
}

# =============================================================================
# MAGIC ITEMS - POWER OBJECTS
# =============================================================================
POWER_OBJECTS = {
    'Angreal',
    'Sa\'angreal',
    'Ter\'angreal',
    'Items_of_Power',
}

# =============================================================================
# MAGIC CONCEPTS - ONE POWER
# =============================================================================
ONE_POWER_CONCEPTS = {
    'One_Power',
    'Saidin',
    'Channelers',
    'Channeling',
    'Weaves',
    'Talents',
    'Special_abilities',
    'Strength_in_power',
    'Taint',
}

# =============================================================================
# MAGIC PLACES & REALMS
# =============================================================================
MAGIC_PLACES = {
    'Tel\'aran\'rhiod',
    'The_Pattern',
    'Shadar_Logoth',
}

# =============================================================================
# MAGIC ENTITIES
# =============================================================================
MAGIC_ENTITIES = {
    'Shadowspawn',
    'Constructs',
    'Aelfinn_and_Eelfinn',
    'Extradimensional_entities',
}

# =============================================================================
# MAGIC WEAPONS & SPECIAL ITEMS
# =============================================================================
MAGIC_WEAPONS = {
    'Weapons',
    'Crowns_and_Regalia',
    'Special_objects',
}

# =============================================================================
# ALL MAGIC CATEGORIES (for easy checking)
# =============================================================================
ALL_MAGIC_CATEGORIES = (
    POWER_OBJECTS | 
    ONE_POWER_CONCEPTS | 
    MAGIC_PLACES | 
    MAGIC_ENTITIES | 
    MAGIC_WEAPONS
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_prophecy_category(category: str) -> bool:
    """Check if category is prophecy-related."""
    return category in PROPHECY_CATEGORIES

def is_power_object(category: str) -> bool:
    """Check if category is a Power object (angreal, ter'angreal, etc)."""
    return category in POWER_OBJECTS

def is_one_power_concept(category: str) -> bool:
    """Check if category is One Power concept."""
    return category in ONE_POWER_CONCEPTS

def is_magic_place(category: str) -> bool:
    """Check if category is a magical place."""
    return category in MAGIC_PLACES

def is_magic_entity(category: str) -> bool:
    """Check if category is a magical entity."""
    return category in MAGIC_ENTITIES

def is_magic_weapon(category: str) -> bool:
    """Check if category is a magical weapon."""
    return category in MAGIC_WEAPONS

def is_any_magic_category(category: str) -> bool:
    """Check if category is any magic-related category."""
    return category in ALL_MAGIC_CATEGORIES

def classify_magic_page(categories: list) -> str:
    """
    Classify a magic page based on its categories.
    Returns: 'power_object', 'concept', 'place', 'entity', 'weapon', or 'other'
    """
    for category in categories:
        if is_power_object(category):
            return 'power_object'
        if is_one_power_concept(category):
            return 'concept'
        if is_magic_place(category):
            return 'place'
        if is_magic_entity(category):
            return 'entity'
        if is_magic_weapon(category):
            return 'weapon'
    
    return 'other'

def is_nationality(category: str) -> bool:
    """Check if category indicates nationality."""
    return category in NATIONALITY_CATEGORIES

def is_channeling_affiliation(category: str) -> bool:
    """Check if category indicates channeling ability."""
    return category in CHANNELING_AFFILIATIONS

def is_aiel_clan(category: str) -> bool:
    """Check if category is an Aiel clan."""
    return category in AIEL_CLANS

def is_aiel_society(category: str) -> bool:
    """Check if category is an Aiel warrior society."""
    return category in AIEL_SOCIETIES

def is_dark_aligned(category: str) -> bool:
    """Check if category indicates dark alignment."""
    return category in ALIGNMENT_DARK

def check_fist_level_key_in_json(filepath: str, key_to_check: str) -> bool:
    """
    Check if a first-level key exists in a JSON file.
    
    Args:
        filename: Path to JSON file
        key_to_check: Key to check for   
    """
    data = load_json_from_file(filepath) 

    # Ensure it's a dictionary
    if isinstance(data, dict):
        return key_to_check in data
    else:
        raise ValueError("JSON is not a dictionary.")

def extract_page_name(file_path: Path) -> Optional[str]:
    """Extract page name from wiki file H1 header."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# ') and not line.startswith('##'):
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
    page_id_match = re.search(r'<!--\s*Page ID:\s*(\d+)\s*-->', content)
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

    if(not content):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath.name}: {e}")
            return []

    pattern = r'<!--\s*Categories:\s*(.*?)\s*-->'
    match = re.search(pattern, content, re.IGNORECASE)
    
    all_categories = []

    if match:
        categories_str = match.group(1)
        # Split by comma and strip whitespace
        categories = [cat.strip() for cat in categories_str.split(',')]
        # Filter out empty strings
        categories = [cat for cat in categories if cat]

        # Apply overrides if they exist for this file
        if filepath.name in CATEGORY_OVERRIDES:
            categories.extend(CATEGORY_OVERRIDES[filepath.name])
        
        all_categories = list(set(categories))  # Deduplicate

    return all_categories
