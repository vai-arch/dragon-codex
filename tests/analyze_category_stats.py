"""
Dragon's Codex - Category Statistics Extractor
Counts how many characters belong to each category from filename_to_categories.json
"""

import json
from pathlib import Path
from collections import defaultdict

from src.utils.config import Config

config = Config()

# Load the filename_to_categories.json file
categories_file = Config().FILE_CATEGORY_TO_FILES

print(f"Loading categories from: {categories_file}")

with open(categories_file, 'r', encoding='utf-8') as f:
    categories_data = json.load(f)

print(f"Loaded {len(categories_data)} categories\n")

# Import category sets from our mappings
from src.utils.wiki_constants import (
    GENDER_CATEGORIES,
    CHANNELING_AFFILIATIONS,
    AJAH_CATEGORIES,
    SPECIAL_ABILITIES,
    NATIONALITY_CATEGORIES,
    ORGANIZATIONS,
    MILITARY_GROUPS,
    SOCIAL_ROLES,
    MILITARY_ROLES,
    AES_SEDAI_POSITIONS,
    ASHAMAN_POSITIONS,
    PROFESSIONS,
    ALIGNMENT_DARK,
    CULTURAL_GROUPS,
    AIEL_CLANS,
    AIEL_SOCIETIES,
    SEANCHAN_GROUPS,
    ATHAAN_MIERE_GROUPS,
)

def print_category_stats(title, category_set, categories_data):
    """Print statistics for a category set."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    
    total_chars = 0
    found_categories = []
    
    for category in sorted(category_set):
        if category in categories_data:
            count = categories_data[category]['count']
            total_chars += count
            found_categories.append((category, count))
            print(f"  {category:45s} {count:5,} characters")
        else:
            print(f"  {category:45s}     0 characters (not in wiki)")
    
    print(f"\n  TOTAL: {total_chars:,} character assignments")
    print(f"  Found {len(found_categories)}/{len(category_set)} categories")
    
    return total_chars, found_categories


def main():
    """Main statistics extraction."""
    
    print("\n" + "="*80)
    print("CATEGORY STATISTICS EXTRACTION")
    print("="*80)
    
    all_stats = {}
    
    # Gender
    total, found = print_category_stats(
        "GENDER", 
        set(GENDER_CATEGORIES.keys()), 
        categories_data
    )
    all_stats['gender'] = total
    
    # Channeling Affiliations
    total, found = print_category_stats(
        "CHANNELING AFFILIATIONS", 
        CHANNELING_AFFILIATIONS, 
        categories_data
    )
    all_stats['channeling'] = total
    
    # Ajah
    total, found = print_category_stats(
        "AJAH", 
        set(AJAH_CATEGORIES.keys()), 
        categories_data
    )
    all_stats['ajah'] = total
    
    # Special Abilities (just get the category names, not the mapped values)
    ability_categories = set(SPECIAL_ABILITIES.keys())
    total, found = print_category_stats(
        "SPECIAL ABILITIES", 
        ability_categories, 
        categories_data
    )
    all_stats['abilities'] = total
    
    # Nationalities
    total, found = print_category_stats(
        "NATIONALITIES", 
        NATIONALITY_CATEGORIES, 
        categories_data
    )
    all_stats['nationalities'] = total
    
    # Organizations
    total, found = print_category_stats(
        "ORGANIZATIONS", 
        ORGANIZATIONS, 
        categories_data
    )
    all_stats['organizations'] = total
    
    # Military Groups
    total, found = print_category_stats(
        "MILITARY GROUPS", 
        MILITARY_GROUPS, 
        categories_data
    )
    all_stats['military_groups'] = total
    
    # Social Roles
    total, found = print_category_stats(
        "SOCIAL ROLES", 
        SOCIAL_ROLES, 
        categories_data
    )
    all_stats['social_roles'] = total
    
    # Military Roles
    total, found = print_category_stats(
        "MILITARY ROLES", 
        MILITARY_ROLES, 
        categories_data
    )
    all_stats['military_roles'] = total
    
    # Aes Sedai Positions
    total, found = print_category_stats(
        "AES SEDAI POSITIONS", 
        AES_SEDAI_POSITIONS, 
        categories_data
    )
    all_stats['aes_sedai_positions'] = total
    
    # Asha'man Positions
    total, found = print_category_stats(
        "ASHA'MAN POSITIONS", 
        ASHAMAN_POSITIONS, 
        categories_data
    )
    all_stats['ashaman_positions'] = total
    
    # Professions
    total, found = print_category_stats(
        "PROFESSIONS", 
        PROFESSIONS, 
        categories_data
    )
    all_stats['professions'] = total
    
    # Alignment (Dark)
    total, found = print_category_stats(
        "ALIGNMENT (DARK)", 
        ALIGNMENT_DARK, 
        categories_data
    )
    all_stats['alignment_dark'] = total
    
    # Cultural Groups
    total, found = print_category_stats(
        "CULTURAL GROUPS", 
        CULTURAL_GROUPS, 
        categories_data
    )
    all_stats['cultural_groups'] = total
    
    # Aiel Clans
    total, found = print_category_stats(
        "AIEL CLANS", 
        AIEL_CLANS, 
        categories_data
    )
    all_stats['aiel_clans'] = total
    
    # Aiel Warrior Societies
    total, found = print_category_stats(
        "AIEL WARRIOR SOCIETIES", 
        AIEL_SOCIETIES, 
        categories_data
    )
    all_stats['aiel_societies'] = total
    
    # Seanchan Groups
    total, found = print_category_stats(
        "SEANCHAN GROUPS", 
        SEANCHAN_GROUPS, 
        categories_data
    )
    all_stats['seanchan_groups'] = total
    
    # Atha'an Miere Groups
    total, found = print_category_stats(
        "ATHA'AN MIERE GROUPS", 
        ATHAAN_MIERE_GROUPS, 
        categories_data
    )
    all_stats['athaan_miere_groups'] = total
    
    # Final Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\nTotal character assignments by category type:")
    for category_type, count in sorted(all_stats.items()):
        print(f"  {category_type:30s} {count:6,} assignments")
    
    print(f"\n✅ Category statistics complete!\n")


if __name__ == "__main__":
    main()