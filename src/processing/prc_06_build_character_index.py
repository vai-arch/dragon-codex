"""
Dragon's Codex - Character Index Builder v2.0
Builds comprehensive character index leveraging wiki categories.

Extracts from:
- wiki_character.json (2,452 character pages with categories)
- redirect_mapping.json (2,785+ redirects for aliases)

New Approach:
- Use categories directly instead of content parsing
- Structured fields for fast lookups
- Comprehensive coverage of all character attributes

Input: data/processed/wiki/wiki_character.json
Output: data/metadata/wiki/character_index.json
"""

import sys
import traceback
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.paths import get_paths
from src.utils.util_files_functions import load_json_from_file, save_json_to_file
from src.utils.util_statistics import total_statistics_logging
from src.utils.wiki_constants import (
    AJAHS,
    ALIGNMENT_DARK,
    CHANNELING_AFFILIATIONS,
    CULTURAL_GROUPS,
    GENDERS,
    MILITARY_GROUPS,
    MILITARY_ROLES,
    NATIONALITY_CATEGORIES,
    ORGANIZATIONS,
    PROFESSIONS,
    SOCIAL_ROLES,
    SPECIAL_ABILITIES,
)

# File paths
in_file_wiki_character = None
out_file_character_index = None


def normalize_name(name: str) -> str:
    """Normalize character name for matching."""
    return name.replace(".txt", "").replace("_", " ")


def extract_gender(categories: List[str]) -> Optional[str]:
    """Extract gender from categories."""
    for category in categories:
        if category in GENDERS:
            if category == "Men":
                return "male"
            else:
                return "female"
    return None


def extract_channeling_info(categories: List[str], gender: Optional[str]) -> Dict:
    """Extract channeling information from categories."""
    channeling = {"can_channel": False, "type": None, "affiliations": []}

    # Check for channeling affiliations
    affiliations = []
    for category in categories:
        if category in CHANNELING_AFFILIATIONS:
            affiliations.append(category.replace("_", " "))
            channeling["can_channel"] = True

    if affiliations:
        channeling["affiliations"] = sorted(affiliations)

        # Determine channeling type from gender
        if gender == "male":
            channeling["type"] = "saidin"
        elif gender == "female":
            channeling["type"] = "saidar"

    return channeling


def extract_ajah(categories: List[str]) -> Optional[str]:
    """Extract Ajah from categories."""
    for category in categories:
        if category in AJAHS:
            return category.replace("_", " ")
    return None


def extract_special_abilities(categories: List[str]) -> List[str]:
    """Extract special abilities from categories."""
    abilities = []
    for category in categories:
        if category in SPECIAL_ABILITIES:
            abilities.append(category.replace("_", " "))
    return sorted(abilities) if abilities else []


def extract_nationalities(categories: List[str]) -> List[str]:
    """Extract nationalities from categories (ending with '(people)')."""
    nationalities = []
    for category in categories:
        if category in NATIONALITY_CATEGORIES:
            nationality = category.replace("_(people)", "").replace("_", " ")
            nationalities.append(nationality)
    return sorted(nationalities) if nationalities else []


def extract_organizations(categories: List[str]) -> List[str]:
    """Extract organizations from categories."""
    orgs = []
    for category in categories:
        if category in ORGANIZATIONS:
            orgs.append(category.replace("_", " "))
    return sorted(orgs) if orgs else []


def extract_military_groups(categories: List[str]) -> List[str]:
    """Extract military groups from categories."""
    groups = []
    for category in categories:
        if category in MILITARY_GROUPS:
            groups.append(category.replace("_", " "))
    return sorted(groups) if groups else []


def extract_social_roles(categories: List[str]) -> List[str]:
    """Extract social roles from categories."""
    roles = []
    for category in categories:
        if category in SOCIAL_ROLES or category in MILITARY_ROLES:
            roles.append(category.replace("_", " "))
    return sorted(roles) if roles else []


def extract_professions(categories: List[str]) -> List[str]:
    """Extract professions from categories."""
    profs = []
    for category in categories:
        if category in PROFESSIONS:
            profs.append(category.replace("_", " "))
    return sorted(profs) if profs else []


def extract_alignment(categories: List[str]) -> List[str]:
    """Extract alignment (dark-side) from categories."""
    alignment = []
    for category in categories:
        if category in ALIGNMENT_DARK:
            alignment.append(category.replace("_", " "))
    return sorted(alignment) if alignment else []


def extract_cultural_groups(categories: List[str]) -> List[str]:
    """Extract cultural groups from categories."""
    groups = []
    for category in categories:
        if category in CULTURAL_GROUPS:
            groups.append(category.replace("_", " "))
    return sorted(groups) if groups else []


def process_character(filename: str, char_data: Dict) -> Optional[Dict]:
    """Process a single character and extract all information."""

    character_name = char_data.get("character_name")
    if not character_name:
        return None

    categories = char_data.get("metadata", {}).get("categories", [])

    # Build index entry
    index_entry = {
        "primary_name": character_name,
        "filename": filename,
    }

    # Extract aliases from redirects
    aliases = char_data.get("aliases", [])
    aliases = sorted(list(set(aliases)))  # Remove duplicates

    if aliases:
        index_entry["aliases"] = aliases

    # Extract gender
    gender = extract_gender(categories)
    if gender:
        index_entry["gender"] = gender

    # Extract channeling info
    channeling = extract_channeling_info(categories, gender)
    if channeling["can_channel"]:
        index_entry["can_channel"] = True
        if channeling["type"]:
            index_entry["channeling_type"] = channeling["type"]
        if channeling["affiliations"]:
            index_entry["channeling_affiliations"] = channeling["affiliations"]

    # Extract Ajah
    ajah = extract_ajah(categories)
    if ajah:
        index_entry["ajah"] = ajah

    # Extract special abilities
    abilities = extract_special_abilities(categories)
    if abilities:
        index_entry["special_abilities"] = abilities

    # Extract nationalities
    nationalities = extract_nationalities(categories)
    if nationalities:
        index_entry["nationalities"] = nationalities

    # Extract organizations
    organizations = extract_organizations(categories)
    if organizations:
        index_entry["organizations"] = organizations

    # Extract military groups
    military = extract_military_groups(categories)
    if military:
        index_entry["military_groups"] = military

    # Extract social roles
    social = extract_social_roles(categories)
    if social:
        index_entry["social_roles"] = social

    # Extract professions
    professions = extract_professions(categories)
    if professions:
        index_entry["professions"] = professions

    # Extract alignment
    alignment = extract_alignment(categories)
    if alignment:
        index_entry["alignment"] = alignment

    # Extract cultural groups
    cultural = extract_cultural_groups(categories)
    if cultural:
        index_entry["cultural_groups"] = cultural

    return index_entry


def process_all_characters(characters: Dict) -> tuple:
    """Process all characters to build index."""

    print(f"\n⚙️  Processing {len(characters):,} characters...")

    character_index = {}

    # Statistics
    stats = {
        "total": 0,
        "with_aliases": 0,
        "channelers": 0,
        "male_channelers": 0,
        "female_channelers": 0,
        "ta_veren": 0,
        "wolfbrothers": 0,
        "dreamers": 0,
        "with_ajah": 0,
        "with_nationality": 0,
        "with_organizations": 0,
        "darkfriends": 0,
        "with_professions": 0,
    }

    for filename, char_data in characters.items():
        entry = process_character(filename, char_data)

        if not entry:
            continue

        character_name = entry["primary_name"]
        character_index[character_name] = entry

        # Update statistics
        stats["total"] += 1

        if entry.get("aliases"):
            stats["with_aliases"] += 1

        if entry.get("can_channel"):
            stats["channelers"] += 1
            if entry.get("channeling_type") == "saidin":
                stats["male_channelers"] += 1
            elif entry.get("channeling_type") == "saidar":
                stats["female_channelers"] += 1

        if entry.get("ajah"):
            stats["with_ajah"] += 1

        abilities = entry.get("special_abilities", [])
        if "ta_veren" in abilities:
            stats["ta_veren"] += 1
        if "wolfbrother" in abilities:
            stats["wolfbrothers"] += 1
        if "dreamer" in abilities or "dreamwalker" in abilities:
            stats["dreamers"] += 1

        if entry.get("nationalities"):
            stats["with_nationality"] += 1

        if entry.get("organizations"):
            stats["with_organizations"] += 1

        if entry.get("alignment"):
            stats["darkfriends"] += 1

        if entry.get("professions"):
            stats["with_professions"] += 1

        # Progress indicator
        if stats["total"] % 500 == 0:
            print(f"   Processed {stats['total']:,} characters...")

    print(f"\n✅ Processed all {stats['total']:,} characters")

    return character_index, stats


def validate_major_characters(character_index: Dict) -> bool:
    """Validate the 5 major characters with detailed output."""

    print("\n🔍 Validating major characters...")

    major_characters = ["Rand al'Thor", "Mat Cauthon", "Perrin Aybara", "Egwene al'Vere", "Elayne Trakand"]

    validation_passed = True

    for char_name in major_characters:
        print(f"\n   {char_name}:")

        if char_name not in character_index:
            print("      ❌ NOT FOUND in index!")
            validation_passed = False
            continue

        char = character_index[char_name]

        # Gender
        if char.get("gender"):
            print(f"      ✓ Gender: {char['gender']}")

        # Channeling
        if char.get("can_channel"):
            print(f"      ✓ Can channel: {char.get('channeling_type', 'unknown')}")
            if char.get("channeling_affiliations"):
                print(f"         Affiliations: {', '.join(char['channeling_affiliations'])}")
            if char.get("ajah"):
                print(f"         Ajah: {char['ajah']}")

        # Special abilities
        if char.get("special_abilities"):
            print(f"      ✓ Special abilities: {', '.join(char['special_abilities'])}")

        # Aliases
        if char.get("aliases"):
            print(f"      ✓ {len(char['aliases'])} aliases: {', '.join(char['aliases'][:3])}...")

        # Nationality
        if char.get("nationalities"):
            print(f"      ✓ Nationality: {', '.join(char['nationalities'])}")

        # Organizations
        if char.get("organizations"):
            print(f"      ✓ Organizations: {', '.join(char['organizations'])}")

        # Social roles
        if char.get("social_roles"):
            print(f"      ✓ Roles: {', '.join(char['social_roles'])}")

    if validation_passed:
        print("\n   ✅ All major characters validated!")
    else:
        print("\n   ⚠️  Some validation issues found")

    return validation_passed


def main():
    start_time = datetime.now()

    # Step 1: Load data
    characters = load_json_from_file(in_file_wiki_character)

    # Step 3: Process all characters
    character_index, stats = process_all_characters(characters)

    # Step 4: Validate major characters
    validate_major_characters(character_index)

    # Step 5: Save index
    save_json_to_file(character_index, out_file_character_index, indent=2)

    # fmt: off
    statistics = {
        "name": "character_index",
        "metrics": stats
    }
    # fmt: on

    total_time = datetime.now() - start_time

    total_statistics_logging(total_time=total_time, log_name="prc_06_build_character_index", statistics=statistics, title="CHARACTER INDEX", tables=False)


if __name__ == "__main__":
    paths = get_paths()

    in_file_wiki_character = paths.FILE_WIKI_CHARACTER
    out_file_character_index = paths.FILE_CHARACTER_INDEX

    try:
        exit_code = main()
        exit_code = 0
    except Exception as e:
        print("❌ An error occurred in the script:", str(e))
        traceback.print_exc()  # optional: prints full stack trace
        exit_code = 1  # non-zero signals failure

    sys.exit(exit_code)
